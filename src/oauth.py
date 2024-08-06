"""OAuth2 configuration."""

import os
from typing import List, Literal, Optional, Set, TypedDict

from dotenv import find_dotenv, load_dotenv
from httpx_oauth.oauth2 import BaseOAuth2

# Load environment variables
load_dotenv(find_dotenv(".env.local"), verbose=True)

# Constants for OAuth configuration
AUTHORIZE_ENDPOINT: str = os.getenv("AUTHORIZATION_ENDPOINT", "")
ACCESS_TOKEN_ENDPOINT: str = os.getenv("TOKEN_ENDPOINT", "")
BASE_SCOPE: str = os.getenv("SCOPE", "")
BASE_SCOPES = [scope for scope in BASE_SCOPE.split(",") if scope]
CLIENT_ID: str = os.getenv("CLIENT_ID", "")
AUDIENCE: str = os.getenv("AUDIENCE", "")
CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
REDIRECT_URI: str = os.getenv("REDIRECT_URI", "")
ALLOWED_GROUP: str = os.getenv("ALLOWED_GROUP", "")
ALLOWED_GROUPS: Set[str] = {ALLOWED_GROUP} if ALLOWED_GROUP else set()


class OAuth2AuthorizeParams(TypedDict):
    """OAuth2 authorize endpoint parameters."""

    access_type: Literal["online", "offline"]
    include_granted_scopes: bool
    login_hint: str
    prompt: Literal["none", "consent", "select_account"]


class OAuth2(BaseOAuth2[OAuth2AuthorizeParams]):
    """OAuth2 configuration.

    Attributes:
        display_name: Display name of the OAuth2 configuration.
        client_id: Client ID of the OAuth2 configuration.
        client_secret: Client secret of the OAuth2 configuration.
        scopes: Scopes of the OAuth2 configuration.
        name: Name of the OAuth2 configuration.
    """

    display_name: str = "[stage oauth] RAG CHATBOT"

    def __init__(
        self,
        client_id: str = CLIENT_ID,
        client_secret: str = CLIENT_SECRET,
        scopes: List[Optional[str]] = None,
        name: str = "[stage oauth] RAG CHATBOT",
    ):
        if scopes is None:
            scopes = BASE_SCOPES
        filtered_scopes = [scope for scope in scopes if scope]

        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint=AUTHORIZE_ENDPOINT,
            access_token_endpoint=ACCESS_TOKEN_ENDPOINT,
            name=name,
            base_scopes=filtered_scopes,
        )

    async def write_access_token(self, redirect_uri: str, code: str) -> str:
        """Write access token."""
        token = await self.get_access_token(code, redirect_uri)
        return token


# Example usage
