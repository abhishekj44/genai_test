from src.util import DeploymentType, cache_resource
import os

if DeploymentType[os.environ.get("DEPLOYMENT_TYPE", "LOCAL")] in [
    DeploymentType.DEV,
    DeploymentType.PREPROD,
]:
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import logging
from pathlib import Path
from typing import Dict, List, TypedDict

import chromadb
import tqdm
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from unstructured.chunking.basic import chunk_elements
from unstructured.documents.elements import Element
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import NarrativeText
from chromadb.config import Settings
from chromadb import QueryResult

logger = logging.getLogger(__name__)


def _partition_pdf(filepath: Path, **kwargs) -> List[Element]:

    """
    Partition a PDF file into a list of structured elements.

    Args:
        filepath (Path): The path to the PDF file.
        **kwargs: Additional keyword arguments for partitioning.

    Returns:
        List[Element]: A list of structured elements extracted from the PDF.
    """
    # Combine all text elements into a single string
    elements = partition_pdf(filepath, **kwargs)
    chapter_elements = []

    # Combine all text elements into a single string to identify chapters
    full_text = "\n".join(str(element) for element in elements if isinstance(element, NarrativeText))

    # Split the text by chapters assuming chapters are marked as "Chapter 1", "Chapter 2", etc.
    chapters = full_text.split('Chapter ')

    # Adjust the chapter indexing because we split by 'Chapter '
    if len(chapters) > 1:
        for i in range(1, 2 + 1):
            if i < len(chapters):
                chapter_identifier = f"Chapter {i}"
                for element in elements:
                    if chapter_identifier in str(element):
                        chapter_elements.append(element)

    return chapter_elements
    # return partition_pdf(filepath, **kwargs)


def _chunk_elements(elements: List[Element], **kwargs) -> List[Element]:
    """
    Chunk a list of elements using specified configurations.

    Args:
        elements (List[Element]): The list of elements to be chunked.
        **kwargs: Additional keyword arguments for chunking.

    Returns:
        List[Element]: A list of chunked elements.
    """
    chunked = chunk_elements(elements, **kwargs)
    for c in chunked:
        c.id_to_uuid()
    ids = [c.id for c in chunked]
    meta = [c.metadata.to_dict() for c in chunked]

    for chunk in meta:
        _keys = chunk.keys()
        if "languages" in _keys:
            chunk["languages"] = str(chunk["languages"])
        if "links" in _keys:
            chunk["links"] = str(chunk["links"])
        if "coordinates" in chunk.keys():
            chunk["coordinates"] = ""
        if "is_continuation" in _keys:
            chunk["is_continuation"] = str(chunk["is_continuation"])

    docs = [c.text if c.text else " " for c in chunked]
    return (ids, meta, docs)


class EmbeddingConfig(TypedDict):
    model_name: str
    api_version: str


def _setup_embedding_model(embedding_config: EmbeddingConfig):
    return OpenAIEmbeddingFunction(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        model_name=embedding_config["model_name"],
        api_version=embedding_config["api_version"],
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_id=embedding_config["model_name"],
        api_type="azure",
    )


class VDB:
    """
    Class for managing a Vector Database (VDB).
    """

    vdb_folder = "vdb"

    def __init__(
        self,
        path: Path,
        collection: str,
        embedding_config: EmbeddingConfig,
        partition_config: Dict,
        chunking_config: Dict,
    ) -> None:
        """
        Initialize the VDB with specified configurations.

        Args:
            path (Path): The path to the VDB.
            collection (str): The name of the collection in the VDB.
            embedding_config (EmbeddingConfig): Configuration for embedding function.
            partition_config (Dict): Configuration for partitioning.
            chunking_config (Dict): Configuration for chunking.
        """
        self.path = path
        self.client = self._setup_client()
        self.embedding_model = _setup_embedding_model(embedding_config)
        if collection in [c.name for c in self.client.list_collections()]:
            logger.info(f"Collection {collection} exists, retrieving...")
            self.collection = self.client.get_collection(
                collection, embedding_function=self.embedding_model
            )
        else:
            logger.info(f"Collection {collection} does not exist, creating...")
            self.collection = self.client.create_collection(
                collection,
                embedding_function=self.embedding_model,
                # metadata={
                #     "hnsw:construction_ef": 128,
                #     "hnsw:search_ef": 128,
                #     "hnsw:M": 128
                # }
            )
        self.partition_config = partition_config
        self.chunking_config = chunking_config

    @cache_resource
    def _setup_client(_self):
        return chromadb.PersistentClient(
            path=str(_self.path / _self.vdb_folder),
            settings=Settings(anonymized_telemetry=False),
        )

    def add_pdfs(self, paths: List[Path]):
        """
        Add PDF documents to the collection after partitioning and chunking.

        Args:
            paths (List[Path]): List of paths to the PDF documents.
        """
        ids = []
        meta = []
        docs = []
        for path in tqdm.tqdm(paths, "Chunking documents"):
            partitioned = _partition_pdf(path, **self.partition_config)
            new_ids, new_meta, new_docs = _chunk_elements(
                partitioned, **self.chunking_config
            )
            ids.extend(new_ids)
            meta.extend(new_meta)
            docs.extend(new_docs)
        chunk_size = 100
        for i in tqdm.tqdm(range(0, len(ids), chunk_size), "Vectorising documents"):
            # time.sleep(10)
            self.collection.add(
                ids=ids[i : i + chunk_size],
                metadatas=meta[i : i + chunk_size],
                documents=docs[i : i + chunk_size],
            )
