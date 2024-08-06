import os
from pathlib import Path
import streamlit as st
import plotly.express as px
import yaml
import pandas as pd

from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_version_eval_head,
)

st.set_page_config(
    page_icon="📈",
    page_title="Version Evaluation",
    layout="wide",
    initial_sidebar_state="expanded",
)
from components.authentication import Roles, authenticate, role_selector, validate_role
from src.evaluation import load_all_evaluation_data

custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()

if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()

static_version_eval_head()

version_directory = Path(os.environ["RAG_VERSION_DIR"])

eval_df = load_all_evaluation_data(version_directory)

eval_df = eval_df.sort_values("version")

all_versions = eval_df["version"].unique()
selected_versions = st.multiselect(
    "Versions", options=all_versions, default=all_versions
)
eval_df = eval_df[eval_df["version"].isin(selected_versions)]

configs = {}
for i, ver in enumerate(selected_versions):
    conf_path = version_directory / ver / "conf.yml"
    with open(conf_path) as stream:
        configs[ver] = yaml.safe_load(stream)

# descs = {}
# for ver in configs:
#     descs[ver] = {}
#     descs[ver]["Description"] = configs[ver]["Description"]
#     descs[ver]["Evaluation Set"] = configs[ver]["Eval_Set"]

st.dataframe(
    pd.DataFrame.from_dict(configs, orient="index")[["Description", "Eval_Set"]].rename(
        {"Eval_Set": "Evaluation Set"}
    )
)

# for ver in configs:
#     st.write(ver)
#     st.write(configs[ver]["Description"])
#     st.write(configs[ver]['Eval_Set'])

scores = [
    "score_response_matching",
    "score_response_match_recall",
    "score_response_match_precision",
    "score_context_relevance",
    "score_factual_accuracy",
    "score_response_relevance",
]
plt_df = eval_df[scores + ["version"]].melt(id_vars="version", value_vars=scores)
plt_df = plt_df.rename(
    columns={"variable": "Criteria", "value": "Score", "version": "Version"}
)

st.header("Score distribution by version")
fig = px.box(plt_df, x="Version", y="Score", color="Criteria")
st.plotly_chart(fig, use_container_width=True)

st.header("Score distribution by criteria")
fig = px.box(plt_df, x="Criteria", y="Score", color="Version")
st.plotly_chart(fig, use_container_width=True)

tokens = ["completion_tokens", "prompt_tokens"]
plt_df = eval_df[tokens + ["version"]].melt(id_vars="version", value_vars=tokens)
plt_df = plt_df.rename(
    columns={"variable": "Source", "value": "Usage", "version": "Version"}
)

st.header("Token usage by version during evaluation")
fig = px.bar(plt_df, x="Version", y="Usage", color="Source")
st.plotly_chart(fig, use_container_width=True)

st.header(f"Score for each question and version for selected criteria")
selected_score = st.selectbox("Criteria", options=scores)
pivot_df = eval_df.pivot_table(
    index=["question", "ground_truth"],
    columns="version",
    values=selected_score,
    fill_value=False,
)
st.dataframe(pivot_df)

st.header("Full evaluation results")
st.dataframe(eval_df)

st.header("Version Configurations")

ver_cols = st.columns([1] * len(selected_versions))
for i, ver in enumerate(configs):
    with ver_cols[i]:
        st.write(ver)
        st.write(configs[ver])
