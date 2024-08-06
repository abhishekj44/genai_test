import os
from pathlib import Path
from typing import List, Set
import pandas as pd
import streamlit as st
import plotly.express as px
import sqlite3
from components.authentication import Roles, authenticate, role_selector, validate_role
from components.theme import (
    backgroundImage,
    custom_css,
    set_png_as_page_bg,
    static_chat_history_head,
)
from src import queries
from src.messages import str_instance_to_instance
from src.util import strip_text_out_of_html

VERSION = "Version"
USER = "User"
CHAT = "Chat"
CREATION_DATE_TIME = "Chat Creation Date Time"
CREATION_DATE = "Creation Date"
MESSAGE_LOG = "Messages"
MSG_NUMBER = "#"
ROLE = "Role"
CONTENT = "Content"
CONTENT_UNFORMATTED = "Content Unformatted"
CONTEXT = "Context"
PROMPT_TOKENS = "Prompt Tokens"
COMPLETION_TOKENS = "Completion Tokens"
MODEL = "Model"
RATING = "Rating"
FEEDBACK = "Feedback"

st.set_page_config(
    page_icon="📈",
    page_title="Chat History",
    layout="wide",
    initial_sidebar_state="expanded",
)
custom_css()
set_png_as_page_bg("style/assets/logo.png")
backgroundImage()
authenticate()

static_chat_history_head()


if "user_info" in st.session_state:
    with st.sidebar:
        role_selector()

if not validate_role(valid_roles=[Roles.SUPERUSER, Roles.ADMIN]):
    st.write("Your role does not have the privilege to access this page.")
    st.stop()

version_directory = Path(os.environ["RAG_VERSION_DIR"])


def retrieve_messages_as_df(version_dir: Path) -> List[dict]:
    conn = sqlite3.connect(version_dir / "rag.db")
    cur = conn.cursor()
    res = cur.execute(queries.GET_ALL_CHATS_WITH_USERS)
    all_chats = res.fetchall()
    instances = [str_instance_to_instance(i) for i in all_chats]
    users = [i[5] for i in all_chats]
    conn.close()
    # st.write(instances)
    # st.write(users)

    message_log = []

    for i, instance in enumerate(instances):
        for j, message in enumerate(instance.messages):
            message_log.append(
                {
                    VERSION: instance.experiment_id,
                    USER: users[i],
                    CHAT: instance.name,
                    CREATION_DATE_TIME: instance.creation_datetime,
                    CREATION_DATE: instance.creation_datetime.date(),
                    MSG_NUMBER: j,
                    ROLE: message.role,
                    CONTENT: message.content,
                    CONTENT_UNFORMATTED: strip_text_out_of_html(message.content),
                    CONTEXT: message.context,
                    PROMPT_TOKENS: (
                        message.usage["prompt_tokens"] if message.usage else None
                    ),
                    COMPLETION_TOKENS: (
                        message.usage["completion_tokens"] if message.usage else None
                    ),
                    MODEL: message.model,
                    RATING: (message.feedback["score"] if message.feedback else None),
                    FEEDBACK: (message.feedback["text"] if message.feedback else None),
                }
            )
    return message_log


#
# with st.container(border=True):
#     versions = list_versions(version_directory)
#     selected_versions = st.multiselect("Versions", versions, default=versions)
#     all_users = list_users(version_directory, selected_versions)
#     selected_users = st.multiselect("Users", all_users, default=all_users)

st.header("Message Log")
msg_list = retrieve_messages_as_df(
    version_dir=version_directory  # , s_versions=selected_versions, s_users=selected_users
)
df = pd.DataFrame(msg_list)
st.dataframe(df)

st.header("Analysis Charts")
key = st.selectbox("Key", options=[VERSION, USER])
fig = px.bar(
    df.groupby([CREATION_DATE, key])[[CHAT]].count().reset_index(),
    x=CREATION_DATE,
    y=CHAT,
    color=key,
).update_layout(yaxis_title="# Messages")
st.plotly_chart(fig, use_container_width=True)

fig = px.bar(df, x=CREATION_DATE, y=PROMPT_TOKENS, color=key)
st.plotly_chart(fig, use_container_width=True)

fig = px.bar(df, x=CREATION_DATE, y=COMPLETION_TOKENS, color=key)
st.plotly_chart(fig, use_container_width=True)

fig = px.bar(
    df.groupby([CREATION_DATE, RATING])[[CHAT]].count().reset_index(),
    x=CREATION_DATE,
    y=CHAT,
    color=RATING,
).update_layout(yaxis_title="# Messages")
st.plotly_chart(fig, use_container_width=True)
