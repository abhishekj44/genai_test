from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
from src.model_params import model_params
import matplotlib.pyplot as plt
import os


def validate_rag_version_directory(dir: Path):
    for x in ["files", "vdb", "conf.yml", "evaluation.csv"]:
        assert x in os.listdir(dir), f"{x} missing from directory"


def scores_bar_chart(df: pd.DataFrame, score_cols: List[str], save_dir: Path) -> None:
    _, ax = plt.subplots()
    df[score_cols].plot.bar(stacked=False, ax=ax)
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax.figure.savefig(save_dir / "eval_scores_bar.png", bbox_inches="tight")


def scores_bar_chart_stacked(
    df: pd.DataFrame, score_cols: List[str], save_dir: Path
) -> None:
    _, ax = plt.subplots()
    df[score_cols].plot.bar(stacked=True, ax=ax)
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax.figure.savefig(save_dir / "eval_scores_bar_stacked.png", bbox_inches="tight")


def costs_bar_chart_stacked(
    df: pd.DataFrame, cost_cols: List[str], save_dir: Path
) -> None:
    _, ax = plt.subplots()
    df[cost_cols].plot.bar(stacked=True, ax=ax)
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax.figure.savefig(save_dir / "costs_bar.png", bbox_inches="tight")


def update_q_dict(
    q_dict: Dict[int, Dict[str, Any]], i: int, response, chunks, rag_model
):
    q_dict[i]["response"] = response.choices[0].message.content
    q_dict[i]["context"] = "\n".join(chunks["documents"][0])
    q_dict[i]["completion_tokens"] = response.usage.completion_tokens
    q_dict[i]["prompt_tokens"] = response.usage.prompt_tokens
    q_dict[i]["meta_data"] = chunks["metadatas"][0]
    q_dict[i]["context_ids"] = chunks["ids"][0]
    q_dict[i]["context_distances"] = chunks["distances"][0]
    q_dict[i]["completion_cost"] = (
        model_params[rag_model].completion_cost_per_1M_tokens
        * q_dict[i]["completion_tokens"]
        / 1000000.0
    )
    q_dict[i]["prompt_cost"] = (
        model_params[rag_model].prompt_cost_per_1M_tokens
        * q_dict[i]["prompt_tokens"]
        / 1000000.0
    )


def load_all_evaluation_data(version_dir: Path):
    df = pd.DataFrame()
    for v in version_dir.glob("*"):
        if v.is_dir():
            eval_df = pd.read_csv(v / "evaluation.csv")
            eval_df["version"] = v.name
            df = pd.concat([df, eval_df])

    return df
