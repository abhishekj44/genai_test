from enum import Enum
import os
from typing import List

from src.authenticate import authenticate_user
from src.util import DeploymentType
import streamlit as st

DISCLAIMER_KEY = "disclaimer_accepted"


def authenticate():
    deployment_type = os.environ.get("DEPLOYMENT_TYPE", "LOCAL")

    if DeploymentType[deployment_type] in [
        DeploymentType.DEV,
        DeploymentType.PREPROD,
        DeploymentType.LOCAL,
    ]:
        authenticate_user()
        if st.session_state.get("authenticated", False):
            pass
        else:
            st.text("Please log in to access the application.")
    elif DeploymentType[deployment_type] == DeploymentType.TEST:
        st.session_state["user_info"] = {
            "prid": "test_prid",
            "name": "test_name",
            "email": "test_email",
            "roles": [Roles.STANDARDUSER],
        }
        st.session_state["role"] = Roles.STANDARDUSER


def save_name():
    assert "user_info" in st.session_state
    return (
        st.session_state.user_info["prid"]
        + " "
        + "".join(st.session_state.user_info["name"].split(","))
    )


class Roles(str, Enum):
    ADMIN = "Admin"
    SUPERUSER = "SuperUser"
    STANDARDUSER = "StandardUser"


def role_selector():
    if "role" not in st.session_state:
        if st.session_state["user_info"]["roles"]:
            st.session_state["role"] = st.session_state["user_info"]["roles"][0]
        else:
            st.session_state["role"] = "No Role"
    role_options = st.session_state["user_info"]["roles"] + ["No Role"]
    selected_role = st.selectbox(label="Select Role", options=role_options)
    if selected_role:
        st.session_state["role"] = selected_role

    # st.session_state["role"] = None
    # st.write(st.session_state["role"])


def validate_role(valid_roles: List[Roles]):
    if not "user_info" in st.session_state:
        return False
    return st.session_state["role"] in valid_roles


def validate_privacy_notice():
    if DISCLAIMER_KEY not in st.session_state:
        st.session_state[DISCLAIMER_KEY] = False
    return st.session_state[DISCLAIMER_KEY]


def privacy_notice():
    with st.container(border=True):
        st.write(
            "By using this service, you confirm that you have read and understood the terms and warnings (below), and will not enter any sensitive personal information."
        )
        st.warning(
            """
            - You must not use this tool in any country that prohibits the use of Large Language Models, such as Russia, Iran & Syria
            - This is a solution powered by GenAI still in development, so results may be incorrect or misleading.
            - This application is only to be used for testing purposes and not as a source of truth.
            - Users are responsible for reviewing the output and should not use it as the sole basis for decision-making.
            - Be careful when using the outputs of this tool to make and/or inform decisions which can have a material impact (i.e. on patients, employees, business processes, finances etc.).
            """,
            icon="⚠️",
        )
        # col1, col2 = st.columns([1, 1])
        # with col1:
        #     with st.container(border=True):
        #         st.write("Features")

        st.warning(
            "This application does record your PRID for purposes of storing chat histories both both future retrieval for personal use, and for improvement of the application.  Please keep in mind that your PRID will be associated with any chats or other inputs provided to this system.",
            icon="⚠️",
        )

        st.write("Please click the button below to confirm your understanding.")
        if st.button("I Understand"):
            st.session_state[DISCLAIMER_KEY] = True
            st.rerun()


def re_open_privacy_notice():
    if st.button("Privacy Notice"):
        st.session_state[DISCLAIMER_KEY] = False
        st.rerun()
