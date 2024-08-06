import argparse
from pathlib import Path
from typing import Dict, List
from src.evaluation import (
    costs_bar_chart_stacked,
    scores_bar_chart,
    scores_bar_chart_stacked,
    update_q_dict,
)
from src.messages import MessageHistory
from src.rag import RAG
from src.vectordb import VDB
from src.retriever import Retriever
from omegaconf import OmegaConf
import pandas as pd
from src.model_params import model_params
from uptrain import EvalLLM, ResponseMatching, Settings, Evals
import matplotlib.pyplot as plt
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv
import sys
import logging


def check_streamlit():
    """
    Function to check whether python code is run within streamlit

    Returns
    -------
    use_streamlit : boolean
        True if code is run within streamlit, else False
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except ModuleNotFoundError:
        return False


def run(directory: Path, vectorise: bool, question_dir: Path):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logger = logging.getLogger(__name__)

    load_dotenv(find_dotenv())
    load_dotenv(find_dotenv(".env.local"))

    from src.util import set_model_cache_env

    set_model_cache_env()

    config = OmegaConf.load(directory / "conf.yml")
    logger.info("Setting up pipeline")
    if check_streamlit():
        import streamlit as st

        st.write("Setting up pipeline")
    vdb = VDB(path=directory, **config["VDB"])
    retriever = Retriever(vdb, **config["Retriever"])
    message_manager = MessageHistory(
        storage_dir=directory, pipeline_version=directory.name, eval=True
    )

    if vectorise:
        message_manager.create_user("evaluation")
        message_manager.change_user("evaluation")
        logger.info("Vectorising")
        if check_streamlit():
            st.write("Vectorising")
        vdb.add_pdfs([p for p in (directory / "files").iterdir()])
    else:
        message_manager.change_user("evaluation")
        logger.info("Skipping vectorisation")
        if check_streamlit():
            st.write("Skipping vectorisation")
    rag = RAG(retriever=retriever, message_manager=message_manager, **config["RAG"])

    questions_df = pd.read_csv(question_dir)
    q_dict = questions_df.to_dict(orient="index")

    model = config["RAG"]["model"]
    for i in tqdm(q_dict, "running questions"):
        instance = message_manager.create_instance(name_override=str(i))
        message_manager.change_instance(instance_id=instance.id)
        response, chunks = rag.query(prompt=q_dict[i]["question"])
        update_q_dict(q_dict, i, response, chunks, model)

    import os

    settings = Settings(
        model="azure/" + config["Evaluation"]["model"],
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_api_version=config["Evaluation"]["api_version"],
        azure_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    eval_llm = EvalLLM(settings)
    logger.info("Evaluating")
    res = eval_llm.evaluate(
        data=list(q_dict.values()),
        checks=[
            ResponseMatching(method="llm"),
            Evals.CONTEXT_RELEVANCE,
            Evals.FACTUAL_ACCURACY,
            Evals.RESPONSE_RELEVANCE,
        ],  # method: llm/exact/rouge
    )
    logger.info("Making charts")
    eval_df = pd.DataFrame.from_dict(res)
    eval_df.to_csv(directory / "evaluation.csv")
    score_cols = [
        "score_response_matching",
        "score_response_match_recall",
        "score_response_match_precision",
        "score_context_relevance",
        "score_factual_accuracy",
        "score_response_relevance",
    ]
    scores_bar_chart(eval_df, score_cols, directory)
    scores_bar_chart_stacked(eval_df, score_cols, directory)
    cost_cols = ["completion_cost", "prompt_cost"]
    costs_bar_chart_stacked(eval_df, cost_cols, directory)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="RAGEvaluation",
        description="""
        Run this script using a RAG config to create and evaluate the RAG instance.
        You should create a directory for the RAG pipeline version with the following:
        - conf.yml (the configuration file for the RAG pipeline),
        - files (folder, containing all the files to be vectorised and queried against)
        """,
    )
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        help="The directory where the files to create the RAG pipeline are stored.",
    )
    parser.add_argument(
        "-q",
        "--questions",
        required=True,
        help="Path to the evaluation question set (.csv)",
    )
    parser.add_argument(
        "-v",
        "--vectorise",
        type=bool,
        help="Flag to toggle file vectorisation.  \
            Off requires a vdb to already exist in the RAG directory.",
    )
    args = parser.parse_args()
    directory = Path(args.directory)
    vectorise = args.vectorise
    question_dir = args.questions

    run(directory=directory, vectorise=vectorise, question_dir=question_dir)
