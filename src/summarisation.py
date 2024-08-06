import math
import os
from pathlib import Path
from openai import AzureOpenAI
from streamlit.runtime.uploaded_file_manager import UploadedFile
from pypdf import PdfReader
import streamlit as st
from src.model_params import model_params
from src.util import estimate_token_count  # Library for PDF processing


DEFAULT_SUMMARISATION_SYSTEM_PROMPT = """Your job is to summarise this document. The summary should have six sections:
- Summary (two sentences)
- Identify the parties involved
- Identify the payment terms
- Identify the contract duration/expiry date
- Identifty the liability cap and exclusions
- Give a summary of the scope of work and costs"""


def extract_text_from_pdf(pdf_file) -> str:
    """This function extracts text from a PDF File

    Args:
        pdf_file (Object): The PDF file uploaded  by the user

    Returns:
        str: The extracted text from the PDF
    """
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()

    return text


def _run_summary(model: str, api_version: str, system_prompt: str, text: str):
    client = AzureOpenAI(api_version=api_version)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": text},
        ],
    )
    if response.choices[0].message.content:
        return response.choices[0].message.content
    else:
        raise ValueError("Bad response")


FROM_CHUNKS_PROMPT_PREFIX = "The following texts were generated from portions of an original document that was too large to put into the context in one go. You need to combine this information into the described format to get the full summary.  "


def summarise(
    text: str,
    system_prompt: str,
    api_version: str = "2023-12-01-preview",
    model: str = "gpt-35-turbo-16k",
) -> str:
    n_chunks = math.ceil(
        estimate_token_count(text=text, model=model) / model_params[model].token_limit
    )
    # st.write("n-chunksß: " + str(n_chunks))
    if n_chunks > 1:
        chunk_length = len(text) // n_chunks  # Integer division to get the chunk length
        chunks = [text[i : i + chunk_length] for i in range(0, len(text), chunk_length)]
        summarised_chunks = [
            _run_summary(
                model=model,
                api_version=api_version,
                system_prompt="You will recieve a chunk of a document.  Make sure that you capture all of the relevant information so that when the chunks are combined, the following task can be completed.  "
                + system_prompt,
                text=chunk,
            )
            for chunk in chunks
        ]
        # st.write(summarised_chunks)
        text = "\n\n".join(summarised_chunks)
        system_prompt = FROM_CHUNKS_PROMPT_PREFIX + "\n\nn" + system_prompt
    return _run_summary(
        model=model, api_version=api_version, system_prompt=system_prompt, text=text
    )


def save_summary(storage_dir: Path, file_name: str, text: str):
    Path.mkdir(storage_dir, exist_ok=True, parents=True)
    with open(storage_dir / (file_name + ".txt"), "w") as file:
        file.write(text)


def list_summaries(storage_dir: Path):
    return os.listdir(storage_dir)


def load_summary(storage_dir: Path, file_name: str):
    with open(storage_dir / file_name, "r") as file:
        return file.read()
