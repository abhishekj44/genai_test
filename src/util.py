from datetime import datetime
import os

import tiktoken

from src.model_params import model_params

from enum import Enum

import streamlit as st

import re
from bs4 import BeautifulSoup


class DeploymentType(Enum):
    """
    Enum for controlling what type of environment is being used.
    Local is default for local development e.g. personal computer
    Test is for github python test workflow.
    Pre-prod and dev are for respective deployments.
    """

    LOCAL = 0
    DEV = 1
    PREPROD = 2
    TEST = 3


# TODO: this will need to be re-implemented when copy paste functionality is available in deployment image
def copy_to_clipboard(text: str) -> None:
    pass


def current_datetime() -> str:
    """Get the current datetime in strf format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def estimate_token_count(text: str, model: str) -> int:
    """Estimate token count for a text portion for a specific model."""
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return len(tokens)


def check_within_token_limit(text: str, model: str) -> bool:
    """Function to assess if completion will be within token limits for model to avoid errors calling completion."""
    assert (
        model in model_params
    ), f"Model ({model}) not in known list of models: {', '.join(model_params.keys())}"
    est_token_count = estimate_token_count(text, model)
    token_limit = model_params[model].token_limit
    return est_token_count < (token_limit * 0.9)  # Allowance for completion length


def set_model_cache_env():
    assert "MODEL_CACHE" in os.environ, "MODEL_CACHE is missing from env"
    os.environ["TRANSFORMERS_CACHE"] = os.environ["MODEL_CACHE"]
    os.environ["HF_HOME"] = os.environ["MODEL_CACHE"]
    os.environ["HF_DATASETS_CACHE"] = os.environ["MODEL_CACHE"]
    os.environ["TORCH_HOME"] = os.environ["MODEL_CACHE"]


def cache_resource(func):
    if os.environ.get("STREAMLIT", False):
        return st.cache_resource(func)
    else:
        return func


def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", filename)


def strip_text_out_of_html(html: str):
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)
    return text
