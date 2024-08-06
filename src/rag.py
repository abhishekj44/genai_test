"""
Module for the RAG (Retrieval-Augmented Generation) model.

This module provides functionality for using the RAG model to generate responses based on user prompts, with the ability to retrieve relevant information from a retriever and incorporate it into the generation process.

Classes:
    RAG: Class for the Retrieval-Augmented Generation model.

Functions:
    _metadata_formatter: Formats metadata into a string.
    _context_formatter: Formats retrieved documents and their metadata into a single context string.

Typing:
    EmbeddingConfig: Typed dictionary for embedding configuration.
    ClientConfig: Typed dictionary for client configuration.

Note:
    - This module requires `chromadb`, `openai`, `src.messages`, and `src.retriever` modules to be imported.
"""

import logging
import math
from typing import Dict, Optional

from chromadb.api.types import Where
from openai import AzureOpenAI

from src.model_params import model_params
from src.messages import MessageHistory, RAGMessage
from src.retriever import Retriever
from src.util import cache_resource, check_within_token_limit, estimate_token_count

logger = logging.getLogger("__main__")
logger.addHandler(logging.StreamHandler())


from typing import TypedDict


class EmbeddingConfig(TypedDict):
    model_name: str
    api_version: str


class ClientConfig(TypedDict):
    api_version: str


def _metadata_formatter(
    metadata: Dict[str, str], meta_data_keys=["filename", "page_number"]
) -> str:
    """
    Formats metadata into a string.

    Args:
    metadata (Dict[str, str]): The metadata to be formatted.

    Returns:
    str: A string representing the formatted metadata.
    """

    return "\n".join(
        f"{key}: {value}" for key, value in metadata.items() if key in meta_data_keys
    )


def _context_formatter(docs, metadatas) -> str:
    """
    Formats retrieved documents and their metadata into a single context string.

    Args:
    docs: The retrieved documents.
    metadatas: The metadata for the retrieved documents.

    Returns:
    str: A string representing the formatted context.
    """

    context = ""
    for i, doc in enumerate(docs):
        meta = _metadata_formatter(metadatas[i])
        context += meta
        context += "\n\n" + doc + "\n\n"
    return context


@cache_resource
def _create_client(_client_config):
    return AzureOpenAI(**_client_config)


class RAG:
    """
    Class for the Retrieval-Augmented Generation model.

    Attributes:
    retriever (Retriever): The retriever object for retrieving relevant information.
    message_manager (MessageHistory): The message history manager.
    client_config (ClientConfig): The client configuration for Azure OpenAI.
    model (str): The name of the model to be used.
    system_prompt_template (str): The system prompt template for generating responses.
    model_settings (Dict[str, str]): Additional settings for the model.

    Methods:
    __init__: Initializes the RAG model with the specified parameters.
    _create_context_message: Creates a context message based on retrieved chunks.
    query: Performs a query using the RAG model with optional retrieval and system prompt generation.
    """

    def __init__(
        self,
        retriever: Retriever,
        message_manager: MessageHistory,
        client_config: ClientConfig,
        model: str,
        system_prompt_template: str,
        model_settings: Dict[str, str],
    ) -> None:
        """
        Initializes the RAG model with the specified parameters.

        Args:
        retriever (Retriever): The retriever object for retrieving relevant information.
        message_manager (MessageHistory): The message history manager.
        client_config (ClientConfig): The client configuration for Azure OpenAI.
        model (str): The name of the model to be used.
        system_prompt_template (str): The system prompt template for generating responses.
        model_settings (Dict[str, str]): Additional settings for the model.
        """

        self.client = _create_client(client_config)
        self.retriver = retriever
        self.model = model
        self.model_settings = model_settings
        self.system_prompt_template = system_prompt_template
        self.message_manager = message_manager

    def _create_context_message(self, retrieved_chunks):
        """
        Creates a context message based on retrieved chunks.

        Args:
        retrieved_chunks: The retrieved chunks containing documents and metadata.
        """

        if retrieved_chunks["documents"] is None:
            raise KeyError("documents missing from retrieval")
        if retrieved_chunks["metadatas"] is None:
            raise KeyError("metadatas missing from retrieval")
        context = _context_formatter(
            retrieved_chunks["documents"][0],
            metadatas=retrieved_chunks["metadatas"][0],
        )
        system_prompt = self.system_prompt_template.format(context=context)
        return system_prompt

    def check_within_token_limit(self, text):
        return check_within_token_limit(text, model=self.model)

    def query(
        self,
        prompt: str,
        file_content: Optional[str] = None,
        where: Optional[Where] = None,
        with_retrieval: bool = False,
    ):
        """
        Performs a query using the RAG model with optional retrieval and system prompt generation.

        Args:
        prompt (str): The user prompt for the query.
        where (Optional[Where]): The optional 'where' condition for retrieval.
        with_retrieval (bool): Flag indicating whether retrieval should be performed.

        Returns:
        Tuple: A tuple containing the response from the RAG model and the retrieved chunks (if retrieval was performed).
        """
        assert self.message_manager.instance, "No instance"

        use_retrieval = (
            len(self.message_manager.instance.messages) == 0 or with_retrieval
        )
        retrieved_chunks = None

        if file_content:
            n_chunks = math.ceil(
                estimate_token_count(text=prompt + " " + file_content, model=self.model)
                / model_params[self.model].token_limit
            )
            if n_chunks > 1:
                document_chunk_length = (
                    len(file_content) // n_chunks
                )  # Integer division to get the chunk length
                document_chunks = [
                    file_content[i : i + document_chunk_length]
                    for i in range(0, len(file_content), document_chunk_length)
                ]
                responses = []
                all_retrieved_chunks = None
                for chunk in document_chunks:
                    if use_retrieval:
                        sub_prompt = " ".join(
                            [
                                prompt,
                                "Answer the question based on the attached file section: ",
                                chunk,
                            ]
                        )
                        retrieved_chunks = self.retriver.query(text=prompt, where=where)
                        if all_retrieved_chunks is None:
                            all_retrieved_chunks = retrieved_chunks
                        else:
                            for key in retrieved_chunks.keys():
                                if all_retrieved_chunks[key]:
                                    all_retrieved_chunks[key].extend(
                                        retrieved_chunks[key]
                                    )

                        system_prompt = self._create_context_message(retrieved_chunks)
                    else:
                        sub_prompt = prompt
                        system_prompt = chunk
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": sub_prompt},
                        ],
                        **self.model_settings,
                    )
                    responses.append(response)
                all_response_content = "\n".join(
                    [r.choices[0].message.content for r in responses]
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "The following are responses to a question based on different parts of a document.  Combine these into one cohesive answer for the entire document.",
                        },
                        {"role": "user", "content": all_response_content},
                    ],
                    **self.model_settings,
                )
                if all_retrieved_chunks:
                    self.message_manager.log_message(
                        RAGMessage(
                            role="system",
                            content=self._create_context_message(all_retrieved_chunks),
                        )
                    )

                self.message_manager.log_message(
                    RAGMessage(
                        role="user",
                        content=prompt + "\n Attached document: " + file_content,
                    )
                )

                self.message_manager.log_message(
                    MessageHistory.completion_to_message(response, all_retrieved_chunks)
                )

                return response, all_retrieved_chunks

        if use_retrieval:
            retrieved_chunks = self.retriver.query(text=prompt, where=where)
            system_prompt = self._create_context_message(retrieved_chunks)
            self.message_manager.log_message(
                RAGMessage(role="system", content=system_prompt)
            )
        if file_content:
            prompt = "\n".join([prompt, "Attached document: ", file_content])
        self.message_manager.log_message(RAGMessage(role="user", content=prompt))
        try:
            messages = self.message_manager.instance.to_chat_messages()
            content_so_far = []
            for i in range(len(messages) - 1, -1, -1):
                content_so_far.append(messages[i]["content"])
                if not self.check_within_token_limit(" ".join(content_so_far)):
                    i += 1
                    break
            response = self.client.chat.completions.create(
                model=self.model, messages=messages[i:], **self.model_settings
            )

        except Exception as e:
            self.message_manager.pop_message()
            if use_retrieval:
                self.message_manager.pop_message()
            logger.error(e)
            raise e
        try:
            self.message_manager.log_message(
                MessageHistory.completion_to_message(response, retrieved_chunks)
            )
        except Exception as e:
            logger.error(e)
            raise ValueError(response)
        return response, retrieved_chunks
