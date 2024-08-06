import os

from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_welcome_head,
)

os.environ["STREAMLIT"] = "True"

from components.authentication import (
    DISCLAIMER_KEY,
    Roles,
    authenticate,
    privacy_notice,
    re_open_privacy_notice,
    validate_privacy_notice,
    validate_role,
    role_selector,
)
from src.util import set_model_cache_env

set_model_cache_env()

from pathlib import Path
from typing import List
import streamlit as st
from dataclasses import dataclass
import json

from components.feedback import feedback_form


@dataclass
class FAQ:
    question: str
    answer: str


st.set_page_config(
    page_icon="👋",
    page_title="Welcome",
    layout="wide",
    initial_sidebar_state="expanded",
)
custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

static_welcome_head()

if not validate_privacy_notice():
    privacy_notice()
    st.stop()

if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()

if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.STANDARDUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()


def load_faqs() -> List[FAQ]:
    import os

    storage_path = Path(os.environ["RAG_VERSION_DIR"]) / "faqs.json"
    if not os.path.exists(storage_path):
        with open(storage_path, "w") as file:
            file.write(json.dumps({}))
    with open(storage_path, "r") as file:
        faqs = json.loads(file.read())

    return [FAQ(f, faqs[f]) for f in faqs]


def display_faqs(faqs: List[FAQ]):
    for faq in faqs:
        with st.expander(faq.question):
            st.write(faq.answer)


with st.sidebar:
    re_open_privacy_notice()

st.header("How To")
with st.expander("Contracting Assistant"):
    st.write(
        "The contracting assistant page is intended to answer users questions on guidance related to contracting.  The bot references real company guidance to answer questions."
    )
    st.write(
        "Getting started is easy, just select the 'Create a new chat' option, type your question in the text box (rich text supported), and attach a relevant file if required, then hit 'Lookup'. "
    )
    st.image("static/new_chat.png")
    st.write(
        "If you would like to continue this chat with follow up questions, you can write another question at submit.  If you would like the bot to reference more information from the guidance document as you go on, hit the 'Lookup' button again.  If you would just like to continue the conversation with the current information, hit 'Followup'. "
    )
    st.image("static/query_toggle.png")
    st.write(
        "To revist and search through previous chats, just select the previous chat from the menu.  You can filter previous chats based on date of creation, and certain key words under the 'Filter' drop down. "
    )
    st.image("static/instance_filter.png")
with st.expander("📄 Contract Summarisation"):
    st.write(
        """
        Submit a contract as PDF to summarise some key points as described below:
        - Summary (two sentences)
        - Parties involved
        - Payment terms
        - Duration/expiry date
        - Liability cap and exclusions
        - Summary of the scope of work and costs
        """
    )
st.header("FAQs")
display_faqs(load_faqs())
feedback_form()
