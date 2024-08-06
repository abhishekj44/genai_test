from src.util import DeploymentType
import os

if DeploymentType[os.environ.get("DEPLOYMENT_TYPE", "LOCAL")] in [
    DeploymentType.DEV,
    DeploymentType.PREPROD,
]:
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from chromadb.api.types import QueryResult
from openai.types.chat import ChatCompletion
from datetime import datetime

from src import queries
from src.util import DeploymentType, current_datetime

logger = logging.getLogger(__name__)

USER_NOT_DEFINED_ERROR = "User not defined"
INSTANCE_NOT_DEFINED_ERROR = "Instance not defined"

RAG_DATABASE_NAME = "rag.db"


class CompletionTokenUsage(TypedDict):
    completion_tokens: int
    prompt_tokens: int


@dataclass
class RAGMessage:
    """
    Attributes:
        role (str): The role of the entity sending the message (e.g., 'user', 'assistant').
        content (str): The actual content of the message.
        context (Optional[QueryResult]): Any additional context related to the message, if applicable.
        usage (Optional[CompletionTokenUsage]): Token usage statistics for the message, if applicable.
        model (Optional[str]): The name of the model used for generating the message, if applicable.
    """

    role: str
    content: str
    context: Optional[QueryResult] = None
    usage: Optional[CompletionTokenUsage] = None
    model: Optional[str] = None
    feedback: Optional[Dict] = None


@dataclass
class Instance:
    id: int
    name: str
    experiment_id: Optional[str] = None
    creation_datetime: Optional[datetime] = None
    messages: List[RAGMessage] = field(default_factory=list)
    shared: bool = False

    def __hash__(self):
        return hash((self.id, self.name, self.creation_datetime))

    def to_chat_messages(self) -> List[Dict[str, str]]:
        """
        Converts a ChatCompletion object to a RAGMessage object.

        Args:
        - completion (ChatCompletion): The ChatCompletion object to be converted.
        - context (Optional[QueryResult]): Optional context for the conversion.

        Returns:
        - RAGMessage: The converted RAGMessage object.
        """
        return [{"role": m.role, "content": m.content} for m in self.messages]


def load_message_str_to_RAG_message(stringified_messages: str):
    messages_data = json.loads(stringified_messages)
    return [RAGMessage(**msg) for msg in messages_data]


import sqlite3
from sqlite3 import Cursor, Connection


def str_instance_to_instance(instance: List):
    return Instance(
        id=instance[0],
        name=instance[1],
        messages=load_message_str_to_RAG_message(instance[2]),
        creation_datetime=datetime.strptime(instance[4], "%Y-%m-%d %H:%M:%S"),
        experiment_id=instance[3],
    )


class MessageHistory:
    """
    Manages the history of messages for a given user and instance.

    Attributes:
        user (str): The identifier of the user.
        instance (str): The identifier of the instance.
        storage_dir (Path): The version directory path where messages are stored in the message sub directory.
        messages (List[RAGMessage]): List of messages that have been logged.

    Methods:
        log_message: Adds a new message to the history and saves it to the storage.
        to_chat_messages: Converts the message history into a format suitable for chat display.
        change_user: Changes the current user and loads the corresponding message history.
        change_instance: Changes the current instance and loads the corresponding message history.
    """

    def __init__(
        self,
        storage_dir: Path,
        pipeline_version: str,
        eval: bool = False,
    ) -> None:
        """
        Initializes a new MessageHistory object with user, instance, and storage directory if not already existing.
        """
        self._storage_dir = storage_dir
        self._pipeline_version = pipeline_version
        self._eval = eval
        # if self._eval:
        self._create_tables_if_not_existing()

        self.user: Optional[str] = None
        self.instance: Optional[Instance] = None

    def _create_tables_if_not_existing(self):
        connection = self._open_connection()
        cur = connection.cursor()
        cur.execute(queries.CREATE_MESSAGE_TABLE)
        cur.execute(queries.CREATE_USER_TABLE)
        cur.execute(queries.CREATE_USER_PROFILES_TABLE)
        cur.execute(queries.CREATE_SHARED_PROFILES_TABLE)
        connection.commit()
        connection.close()

    def share_instance_with_user(self, user_to_share_with: str, instance_id: int):
        if instance_id not in self._shared_instance_ids_for_user(user_to_share_with):
            con = self._open_connection()
            cur = con.cursor()
            cur.execute(
                queries.INSERT_SHARED_INSTANCE_ID_FOR_USER,
                (user_to_share_with, instance_id),
            )
            con.commit()
            con.close()
            return "Successfully shared."
        else:
            return "User already has this chat."

    def get_shared_instances(self) -> List[Instance]:
        assert self.user
        con = self._open_connection()
        cur = con.cursor()
        res = cur.execute(
            queries.GET_SHARED_INSTANCES_FOR_USER, (self.user, self._pipeline_version)
        )
        instance_ids_names = res.fetchall()
        con.close()
        return [str_instance_to_instance(i) for i in instance_ids_names]

    def _open_connection(self):
        return sqlite3.connect(self._storage_dir / RAG_DATABASE_NAME)

    def _user_exists(self, new_user) -> bool:
        return new_user in self.user_list()

    def _instance_ids_for_user(self):
        assert self.user
        conn = self._open_connection()
        res = conn.cursor().execute(
            queries.GET_PROFILES_FOR_USER,
            (self.user,),
        )
        ids = res.fetchall()
        conn.close()
        return [i[0] for i in ids]

    def _shared_instance_ids_for_user(self, user: str):
        assert self.user
        conn = self._open_connection()
        res = conn.cursor().execute(
            queries.GET_SHARED_PROFILES_FOR_USER,
            (user,),
        )
        ids = res.fetchall()
        conn.close()
        return [i[0] for i in ids]

    def _valid_instance_id(self, instance_id: int) -> bool:
        assert self.user, USER_NOT_DEFINED_ERROR
        return instance_id in self._instance_ids_for_user()

    def _check_user_exists(self, new_user: str, assertion: bool = True):
        exists = self._user_exists(new_user)
        if assertion:
            assert exists, f"{new_user} not in user list"
        else:
            assert not exists, f"{new_user} in user list"

    def pop_message(self, index: int = -1):
        assert self.instance
        self.instance.messages.pop(index)
        self._save_messages()

    def log_message(self, msg: "RAGMessage"):
        """
        Logs a new message to the history and updates the storage.
        """
        assert self.instance
        self.instance.messages.append(msg)
        self._save_messages()

    def _save_messages(self):
        """
        Saves the current message history to a JSON file.
        """
        assert self.instance and self.instance.messages
        c = self._open_connection()
        c.cursor().execute(
            queries.UPDATE_MESSAGES_FOR_INSTANCE,
            (
                json.dumps([vars(msg) for msg in self.instance.messages]),
                self.instance.id,
            ),
        )
        c.commit()
        c.close()

    def user_list(self):
        """
        Returns a list of users with stored messages, excluding 'evaluation' if not in evaluation mode.  Evaluation is ignored as it contains messages created during evaluation of new pipeline
        """
        c = self._open_connection()
        cur = c.cursor()
        users = [u[0] for u in cur.execute(queries.GET_USER_IDS).fetchall()]
        c.commit()
        c.close()
        if not self._eval and "evaluation" in users:
            users.remove("evaluation")
        return users

    def load_instance(self, instance_id, shared=False):
        c = self._open_connection()
        res = c.execute(
            queries.GET_INSTANCE_BY_ID,
            (instance_id,),
        )
        instance = res.fetchone()
        c.close()
        return str_instance_to_instance(instance=instance)

    def load_instances(self) -> List[Instance]:
        """
        Returns a list of instances for the current user.
        """
        q = queries.GET_INSTANCES_FOR_USER_AND_EXPERIMENT
        c = self._open_connection()
        res = c.cursor().execute(q, (self.user, self._pipeline_version))
        instance_ids_names = res.fetchall()
        c.close()
        shared = self.get_shared_instances()
        for s in shared:
            s.shared = True
        return [str_instance_to_instance(i) for i in instance_ids_names] + shared

    @classmethod
    def completion_to_message(
        cls, completion: ChatCompletion, context: Optional[QueryResult] = None
    ) -> "RAGMessage":
        """
        Converts a ChatCompletion object to a RAGMessage object.
        """
        assert completion.choices[0].message.content is not None, "Bad completion"
        return RAGMessage(
            role="assistant",
            content=completion.choices[0].message.content,
            usage={
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
            },
            model=completion.model,
            context=context,
        )

    def create_user(self, new_user: str) -> None:
        self._check_user_exists(new_user, assertion=False)
        c = self._open_connection()

        c.cursor().execute(
            queries.INSERT_NEW_USER,
            (new_user,),
        )
        c.commit()
        c.close()

    def change_user(self, new_user: str) -> None:
        """
        Changes the user that the chat is managing.

        Args:
        - new_user (str): The new user to be associated with the message manager.

        Returns:
        - None
        """
        self._check_user_exists(new_user, assertion=True)
        self.user = new_user
        self.instance = None

    def default_instance(self):
        self.instance = None

    def create_instance(self, name_override: Optional[str] = None) -> Instance:
        assert self.user is not None
        now = current_datetime()
        if name_override:
            instance_name = name_override
        else:
            instance_name = now
        c = self._open_connection()
        cur = c.cursor()
        q = queries.INSERT_NEW_INSTANCE
        cur.execute(q, (instance_name, "[]", self._pipeline_version, now))
        last_inserted_id = cur.lastrowid
        assert last_inserted_id

        cur.execute(
            queries.INSERT_INSTANCE_ID_FOR_USER,
            (self.user, last_inserted_id),
        )
        c.commit()
        c.close()
        return Instance(id=last_inserted_id, name=instance_name)

    def change_instance(self, instance_id: int) -> None:
        assert self.user is not None, "User not defined"
        owned_ids = self._instance_ids_for_user()
        shared_ids = self._shared_instance_ids_for_user(self.user)
        assert instance_id in owned_ids + shared_ids
        self._instance_id = instance_id
        self.instance = self.load_instance(self._instance_id)

    def add_feedback(self, content_for_feedback: str, feedback: Dict):
        assert self.user
        assert self.instance and self.instance.messages
        for i in range(len(self.instance.messages)):
            if self.instance.messages[i].content == content_for_feedback:
                self.instance.messages[i].feedback = feedback
                break

        self._save_messages()
