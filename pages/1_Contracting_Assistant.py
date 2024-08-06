import os
from components.authentication import (
    Roles,
    authenticate,
    privacy_notice,
    re_open_privacy_notice,
    role_selector,
    validate_privacy_notice,
    validate_role,
)
from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_prompt_head,
    static_prompts,
)

os.environ["STREAMLIT"] = "True"

from pathlib import Path
from typing import Any, List

import html2text
import streamlit as st

from components import (
    CREATE_NEW_USER_DEFAULT,
    CREATE_NEW_CHAT_DEFAULT,
    INSTANCE_ID_KEY,
    MESSAGE_MANAGER_SYSTEM_KEY,
    PIPELINE_VERSION_KEY,
    USER_NAME_KEY,
    VERSION_MANAGER_KEY,
)
import time
from components.sidebar import (
    about_section,
)
from components.feedback import feedback_box
from components.instance_selector import instance_selector
from components.chat import (
    display_references,
    create_rag_app,
    process_input_file,
    prompt_input,
)
from src.messages import Instance, MessageHistory
from src.pipeline_versions import VersionManager
from src.util import copy_to_clipboard, clean_filename
from streamlit import session_state

version_directory = Path(os.environ["RAG_VERSION_DIR"])
# message_storage_dir = os.environ.get("CHAT_STORAGE_DIR")
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

MAX_INSTANCE_NAME_LENGTH = 60

st.set_page_config(
    page_icon="🤖",
    page_title="Contracting QA",
    layout="wide",
    initial_sidebar_state="expanded",
)
custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

static_prompt_head()


if not validate_privacy_notice():
    privacy_notice()
    st.stop()

st.warning(
    "This tool produces outputs responses made with Generative AI.  Users are responsible for reviewing the output and should not use it as the sole basis for decision-making."
)

if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()


if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.STANDARDUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()

states = {
    VERSION_MANAGER_KEY: VersionManager(version_directory),
    MESSAGE_MANAGER_SYSTEM_KEY: None,
    USER_NAME_KEY: None,
}

default_instances = [Instance(id=-1, name=CREATE_NEW_CHAT_DEFAULT)]

for key in states:
    if key not in session_state:
        session_state[key] = states[key]

# Information bar
with st.sidebar:
    # Version selector
    version = st.query_params.get(
        PIPELINE_VERSION_KEY, session_state[VERSION_MANAGER_KEY].default
    )
    selected_pipeline_version = st.selectbox(
        "App version",
        options=session_state[VERSION_MANAGER_KEY].app_versions,
        index=session_state[VERSION_MANAGER_KEY].app_versions.index(version),
        key="app_version_selector",
    )
    if selected_pipeline_version != session_state[VERSION_MANAGER_KEY].default:
        st.warning(
            f"Non default app version selected.  The default and most stable version is {session_state[VERSION_MANAGER_KEY].default}."
        )
    if selected_pipeline_version:
        if (
            version != selected_pipeline_version
            or not session_state[MESSAGE_MANAGER_SYSTEM_KEY]
        ):
            st.query_params[PIPELINE_VERSION_KEY] = selected_pipeline_version
            session_state[MESSAGE_MANAGER_SYSTEM_KEY] = MessageHistory(
                storage_dir=version_directory,
                pipeline_version=selected_pipeline_version,
            )
            st.query_params[PIPELINE_VERSION_KEY] = selected_pipeline_version
            time.sleep(0.1)
            # st.rerun()
        # User Selection
        ## Define all options
        user_options: List[Any] = [CREATE_NEW_USER_DEFAULT] + session_state[
            MESSAGE_MANAGER_SYSTEM_KEY
        ].user_list()
        user = st.session_state.user_info["prid"]
        if user:
            # st.header("User")

            if user not in user_options:
                session_state[MESSAGE_MANAGER_SYSTEM_KEY].create_user(user)
                session_state[MESSAGE_MANAGER_SYSTEM_KEY].change_user(user)
                st.rerun()

            if not session_state[MESSAGE_MANAGER_SYSTEM_KEY].user:
                session_state[MESSAGE_MANAGER_SYSTEM_KEY].change_user(user)
                st.rerun()

            # Update the instance options based on the selected user
            if user:
                instance_id = int(st.query_params.get(INSTANCE_ID_KEY, -1))
                ## Get the list of chats in for the selected user
                historical = session_state[MESSAGE_MANAGER_SYSTEM_KEY].load_instances()
                ## Allow selection of an instance
                selected_instance = instance_selector(
                    default_instances, historical, instance_id
                )
                ## If a choice is made
                if selected_instance:
                    ## If its not the default

                    if selected_instance.name == CREATE_NEW_CHAT_DEFAULT:
                        session_state[MESSAGE_MANAGER_SYSTEM_KEY].default_instance()
                        time.sleep(0.1)

                    else:
                        session_state[MESSAGE_MANAGER_SYSTEM_KEY].change_instance(
                            selected_instance.id
                        )
                        time.sleep(0.1)

                    if str(selected_instance.id) != st.query_params.get(
                        INSTANCE_ID_KEY, "NONE"
                    ):
                        st.query_params[INSTANCE_ID_KEY] = selected_instance.id
                        time.sleep(0.1)
                        st.rerun()

                    if selected_instance.name != CREATE_NEW_CHAT_DEFAULT:
                        with st.form("Share"):
                            selected_user_to_share = st.selectbox(
                                label="Share",
                                options=session_state[
                                    MESSAGE_MANAGER_SYSTEM_KEY
                                ].user_list(),
                            )
                            if st.form_submit_button():
                                st.write(
                                    session_state[
                                        MESSAGE_MANAGER_SYSTEM_KEY
                                    ].share_instance_with_user(
                                        user_to_share_with=selected_user_to_share,
                                        instance_id=selected_instance.id,
                                    )
                                )

                else:
                    st.write("Please select an instance")
            else:
                st.warning(
                    "You must select a user profile and chat instance to continue."
                )
            st.info(
                "Chats are locked to app versions for traceability, so to revisit a previous chat you must also select the correct version"
            )

    re_open_privacy_notice()

    st.divider()

    about_section(
        version_directory=version_directory,
        pipeline_version=selected_pipeline_version,
    )

chat_container = st.container()
if session_state[MESSAGE_MANAGER_SYSTEM_KEY].instance:
    for i, message in enumerate(
        session_state[MESSAGE_MANAGER_SYSTEM_KEY].instance.messages
    ):
        if message.role in ["user", "assistant"]:
            with chat_container.chat_message(message.role):
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    with st.container(
                        height=400 if len(message.content) > 1000 else None,
                        border=False,
                    ):
                        st.markdown(message.content, unsafe_allow_html=True)
                    if message.context is not None:
                        display_references(message.context)
                    if message.role == "assistant":
                        feedback_box(
                            message_index=i,
                            message=message,
                            message_manager_state=session_state[
                                MESSAGE_MANAGER_SYSTEM_KEY
                            ],
                        )

                with col2:
                    if message.role == "assistant":
                        if st.button(
                            "Copy", key=message.content + str(i), disabled=True
                        ):
                            copy_to_clipboard(message.content)
else:
    with chat_container:
        static_prompts()

prompt, with_retrieval, user_file = prompt_input(
    input_disabled=session_state[MESSAGE_MANAGER_SYSTEM_KEY].user is None,
    retrieval_only=not st.session_state[MESSAGE_MANAGER_SYSTEM_KEY].instance
    or len(st.session_state[MESSAGE_MANAGER_SYSTEM_KEY].instance.messages) == 0,
)

if prompt:
    if selected_instance.name == CREATE_NEW_CHAT_DEFAULT:
        new_instance = session_state[MESSAGE_MANAGER_SYSTEM_KEY].create_instance(
            clean_filename(html2text.html2text(prompt)[:MAX_INSTANCE_NAME_LENGTH])
        )
        session_state[MESSAGE_MANAGER_SYSTEM_KEY].change_instance(new_instance.id)
        st.query_params[INSTANCE_ID_KEY] = new_instance.id
    extracted_input_file = None
    if user_file:
        extracted_input_file = process_input_file(user_file)

    with chat_container.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)
    with chat_container.chat_message("assistant"):
        with st.spinner("Finding the answer ..."):
            try:
                pipeline = create_rag_app(
                    version_directory=version_directory,
                    version=selected_pipeline_version,
                    message_manager=session_state[MESSAGE_MANAGER_SYSTEM_KEY],
                )
                pipeline.query(
                    prompt,
                    with_retrieval=with_retrieval,
                    file_content=extracted_input_file,
                )
                st.rerun()
            except Exception as e:
                logger.error(e)
                st.error("Something went wrong.  Please try again.\n\n" + str(e))
