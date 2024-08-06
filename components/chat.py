from pathlib import Path
from typing import Optional

from docx import Document
from src.vectordb import VDB, QueryResult
import streamlit as st
from src.messages import MessageHistory
from src.rag import RAG
from src.retriever import Retriever
from src.vectordb import VDB
from omegaconf import OmegaConf
from streamlit_quill import st_quill
from streamlit.runtime.uploaded_file_manager import UploadedFile
from src.docx_conversion import docx_to_string
from src.summarisation import extract_text_from_pdf


def prompt_input(input_disabled: bool, retrieval_only: bool):
    with st.form(key="prompt-file-input", clear_on_submit=True):
        content = st_quill(
            placeholder="What would you like to know?",
            html=True,
            readonly=input_disabled,
            toolbar=[
                [
                    "bold",
                    "italic",
                    "underline",
                    "strike",
                    {"script": "sub"},
                    {"script": "super"},
                ],
                [
                    {"list": "ordered"},
                    {"list": "bullet"},
                    {"indent": "-1"},
                    {"indent": "+1"},
                    {"align": []},
                ],
                [
                    {"header": 1},
                    {"header": 2},
                    {"header": [1, 2, 3, 4, 5, 6, False]},
                    {"size": ["small", False, "large", "huge"]},
                ],
            ],
        )
        user_file = st.file_uploader(
            "Upload a .PDF, .doc or .docx file (optional)",
            type=["pdf", "doc", "docx"],
            disabled=input_disabled,
            label_visibility="collapsed",
        )
        _, scol1, scol2 = st.columns([8, 1, 1])

        # with_retrieval = scol1.toggle(
        #     "Query DB to answer this question",
        #     value=True,
        #     disabled=retrieval_disabled or input_disabled,
        # )
        # with scol2:
        if scol1.form_submit_button(
            ":telescope: Lookup",
            help="Search for more information when you ask your question.  Best if you are asking a complex question not related to any previous questions and need additional information to answer it.",
        ):
            return content, True, user_file
        if not retrieval_only:
            if scol2.form_submit_button(
                ":left_speech_bubble: Followup",
                help="Only use the current information in the chat to continue the conversation.  Best if you are just asking for a simple clarification to your previous questions that doesn't need additional knowledge.",
            ):
                return content, False, user_file
    return None, None, None


def process_input_file(user_file: UploadedFile) -> str:
    if user_file.type in [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]:
        return docx_to_string(Document(user_file))
    elif user_file.type == "application/pdf":
        return extract_text_from_pdf(user_file)
    else:
        raise TypeError(f"File type is not doc, docx or pdf.")


def display_references(context: QueryResult):
    with st.expander("References"):
        meta_data = context["metadatas"][0]
        for i, doc in enumerate(context["documents"][0]):
            st.write(
                f"***{meta_data[i]['filename']} - Page: {meta_data[i]['page_number']}***"
            )
            st.write(doc)


def create_rag_app(
    version_directory: Path,
    version: str,
    message_manager: Optional[MessageHistory] = None,
) -> RAG:
    # if message_storage_dir:
    #     Path(message_storage_dir).mkdir(exist_ok=True, parents=True)
    #     msg_path = Path(message_storage_dir)
    # else:
    msg_path = version_directory
    config = OmegaConf.load(version_directory / version / "conf.yml")
    vdb = VDB(
        path=version_directory / version,
        **config["VDB"],
    )
    retriever = Retriever(vdb, **config["Retriever"])
    return RAG(
        retriever=retriever,
        message_manager=message_manager
        if message_manager
        else MessageHistory(storage_dir=msg_path, pipeline_version=version),
        **config["RAG"],
    )
