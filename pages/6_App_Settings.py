import os
from pathlib import Path
import streamlit as st
from components.authentication import Roles, authenticate, role_selector, validate_role
from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_admin_head,
)
from src.pipeline_versions import VersionManager

st.set_page_config(
    page_icon=":space_invader:",
    page_title="GPS Chat",
    layout="wide",
    initial_sidebar_state="expanded",
)

custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()
static_admin_head()

if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()

version_directory = Path(os.environ["RAG_VERSION_DIR"])

vm = VersionManager(version_directory)

selected_default_pipeline = st.selectbox(
    "Default app version",
    options=vm.app_versions,
    index=vm.app_versions.index(vm.default),
)

if selected_default_pipeline and (selected_default_pipeline != vm.default):
    vm.save_default_version(selected_default_pipeline)
