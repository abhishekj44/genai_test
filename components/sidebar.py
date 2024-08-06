# TODO: tests
import os
from pathlib import Path
from typing import List
import streamlit as st

from components import USER_SELECTOR_KEY
from src.util import cache_resource


def file_list(version_directory: Path, pipeline_version: str):
    st.write("I currently know about the following documents:")
    files = os.listdir(version_directory / pipeline_version / "files")
    for file in files:
        st.markdown(f"- {file}")


@cache_resource
def example_section():
    with st.expander("Examples"):
        st.write("Here are some questions you could ask:")
        example_questions = [
            "What are audit standard terms?",
            "What minimum audit rights do we require in a contract?",
        ]
        for q in example_questions:
            st.markdown(f"- {q}")


@cache_resource
def about_section(version_directory: Path, pipeline_version: str):
    with st.expander("About"):
        st.write(f"My purpose is to answer questions about GPS legal documents.")
        file_list(
            version_directory=version_directory, pipeline_version=pipeline_version
        )
