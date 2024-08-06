from pathlib import Path
import streamlit as st
from components.chat import process_input_file
from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_summariser_head,
)
from src.summarisation import (
    DEFAULT_SUMMARISATION_SYSTEM_PROMPT,
    list_summaries,
    load_summary,
    save_summary,
    summarise,
)
from src.model_params import model_params
import math
from components.authentication import (
    DISCLAIMER_KEY,
    Roles,
    authenticate,
    privacy_notice,
    role_selector,
    validate_privacy_notice,
    validate_role,
)
import os

from src.util import current_datetime

storage_path = Path(os.environ["RAG_VERSION_DIR"]).parent

st.set_page_config(
    page_icon="📄",
    page_title="Contract Summarisation",
    layout="wide",
    initial_sidebar_state="expanded",
)
custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

static_summariser_head()

if not validate_privacy_notice():
    privacy_notice()
    st.stop()

if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()

if not validate_privacy_notice():
    privacy_notice()
    st.stop()

if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.STANDARDUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()

if st.button("Refresh"):
    # st.session_state.clear()
    st.rerun()

user_dir = storage_path / "summaries" / st.session_state.user_info["prid"]
Path.mkdir(user_dir, exist_ok=True, parents=True)

previous_summaries = list_summaries(storage_dir=user_dir)
options = ["CREATE A NEW SUMMARY"] + previous_summaries
selected = st.selectbox(
    label="Select a summary to view or create a new one", options=options
)
if selected:
    st.session_state.summary = None
    if selected == "CREATE A NEW SUMMARY":

        st.session_state.running = False

        # Creating file upload functionality using steamlit file_uploader. Currently only for PDF Files
        user_file = st.file_uploader("Upload your contract file", type=["pdf", "docx"])
        instruction = st.text_area(
            label="Instruction",
            value=DEFAULT_SUMMARISATION_SYSTEM_PROMPT,
            height=200,
        )

        selected_model = st.selectbox(
            label="Model", options=["gpt-35-turbo-16k", "gpt-4-32k"]
        )

        # If a file is uploaded the app uses the text extractor function to extract text from the PDF, it is then passed into GPT to be summarised. If no PDF is passed in a message is present to ask a user to do so.
        start_button = st.button(
            "Summarise",
            disabled=len(instruction) == 0
            or not user_file
            or not selected_model
            or st.session_state.running,
            key="run_button",
        )
        if start_button:
            start_button = False
            if user_file and selected_model:
                st.session_state.running = True
                text = process_input_file(user_file=user_file)
                contract_summary = summarise(
                    text=text, system_prompt=instruction, model=selected_model
                )
                st.session_state.summary = contract_summary
                save_summary(
                    storage_dir=user_dir,
                    file_name=current_datetime() + " " + user_file.name.split(".")[0],
                    text=contract_summary,
                )
            else:
                st.error("No file uploaded")

        if st.session_state.running:
            st.spinner()

    else:
        st.session_state.summary = load_summary(
            storage_dir=user_dir, file_name=selected
        )

if st.session_state.summary:
    st.write(st.session_state.summary)
