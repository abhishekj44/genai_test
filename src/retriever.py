"""
This module provides a Retriever class for querying and re-ranking text data using a VectorDB and a cross-encoder model.

The Retriever class includes methods for initializing the retriever, instantiating a cross-encoder model, re-ranking search results, and querying the VectorDB.

Attributes: RetrievalConfig (TypedDict): A type hint representing the retrieval configuration, including reranking parameters if provided.

Classes: Retriever: A class for querying and re-ranking text data using a VectorDB and a cross-encoder model.

Functions: No public functions are included in this module.
"""

from typing import Any, Dict, Optional, TypedDict

from chromadb.api.types import QueryResult, Where
from sentence_transformers import CrossEncoder

from src.util import cache_resource
from src.vectordb import VDB


class RetrievalConfig(TypedDict):
    reranking: Optional[Dict[str, Any]]


class Retriever:
    """A class for querying text data using a VectorDB and applying post processing.

    Args:
        vdb (VDB): An instance of the VectorDB.
        query_config (Dict): A dictionary representing the query configuration.
        retrieval_config (RetrievalConfig, optional): A dictionary representing the retrieval configuration, including reranking parameters if provided. Defaults to {}.

    Methods:
        __init__: Initializes the Retriever with the specified VectorDB, query configuration, and retrieval configuration.
        _instantiate_cross_encoder: Instantiates a cross-encoder model with the given model name.
        _rerank: Re-ranks the retrieved search results using a cross-encoder model.
        query: Queries the VectorDB with the given text and optional Where clause, and returns the query results.

    """

    def __init__(
        self, vdb: VDB, query_config: Dict, retrieval_config: RetrievalConfig = {}
    ) -> None:
        """
        Initializes the Retriever with the specified VectorDB, query configuration, and retrieval configuration.

        Args:
            vdb (VDB): An instance of the VectorDB.
            query_config (Dict): A dictionary representing the query configuration.
            retrieval_config (RetrievalConfig, optional): A dictionary representing the retrieval configuration, including reranking parameters if provided. Defaults to {}.

        Raises:
            AssertionError: If the top_k value specified in retrieval_config['reranking'] exceeds the n_results value specified in query_config.

        Returns:
            None
        """
        self.vdb = vdb
        self.query_config = query_config
        self.retrieval_config = retrieval_config
        if "reranking" in self.retrieval_config:
            assert (
                self.retrieval_config["reranking"]["top_k"]
                <= self.query_config["n_results"]
            ), f"top_k ({self.retrieval_config['reranking']['top_k']} > n_results {self.query_config['n_results']})"

    @cache_resource
    def _instantiate_cross_encoder(_self, model: str) -> CrossEncoder:
        """
        Instantiates a cross-encoder model with the given model name.

        Args:
            model (str): The name of the cross-encoder model.

        Returns:
            CrossEncoder: An instance of the cross-encoder model.
        """
        return CrossEncoder(model)

    def _rerank(
        self, query: str, retrieved_chunks: QueryResult, model: str, top_k: int
    ):
        """
        Re-ranks the retrieved search results using a cross-encoder model.

        Args:
            query (str): The query text.
            retrieved_chunks (QueryResult): The retrieved search results.
            model (str): The name of the cross-encoder model.
            top_k (int): The number of top results to retain after re-ranking.

        Returns:
            QueryResult: The re-ranked search results.
        """
        hits = retrieved_chunks["documents"][0]
        hits = [{"text": h, "original_index": i} for i, h in enumerate(hits)]
        cross_encoder_model = self._instantiate_cross_encoder(model)
        # Now, do the re-ranking with the cross-encoder
        sentence_pairs = [[query, hit["text"]] for hit in hits]
        similarity_scores = cross_encoder_model.predict(sentence_pairs)

        for idx in range(len(hits)):
            hits[idx]["cross-encoder_score"] = similarity_scores[idx]

        # Sort list by CrossEncoder scores
        hits = sorted(hits, key=lambda x: x["cross-encoder_score"], reverse=True)
        new_index_order = [h["original_index"] for h in hits][:top_k]
        for key in retrieved_chunks.keys():
            if retrieved_chunks[key]:
                retrieved_chunks[key][0] = [
                    retrieved_chunks[key][0][i] for i in new_index_order
                ]
        return retrieved_chunks

    def query(self, text: str, where: Optional[Where] = None) -> QueryResult:
        """
        Queries the VectorDB with the given text and optional Where clause, and returns the query results.
        Applies optional post processing if defined in config.

        Args:
            text (str): The query text.
            where (Where, optional): A Where clause to filter the query. Defaults to None.

        Returns:
            QueryResult: The query results from the VectorDB.
        """
        retrieved_chunks = self.vdb.collection.query(
            query_texts=text, where=where, **self.query_config
        )
        if "reranking" in self.retrieval_config:
            retrieved_chunks = self._rerank(
                text, retrieved_chunks, **self.retrieval_config["reranking"]
            )
        return retrieved_chunks
