import asyncio
import json
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

import jwt
import requests
import streamlit as st
from httpx_oauth.oauth2 import OAuth2Token

from src.oauth import (
    ALLOWED_GROUPS,
    AUDIENCE,
    AUTHORIZE_ENDPOINT,
    BASE_SCOPES,
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    OAuth2,
)


async def _get_authorization_url(
    client: OAuth2, redirect_uri: str, state: Optional[str] = None
) -> str:
    """Get authorization URL with redirect back to the application."""
    extras_params = {"access_type": "offline"}
    return await client.get_authorization_url(
        redirect_uri, scope=BASE_SCOPES, state=state, extras_params=extras_params
    )


async def _get_authorization_token(
    client: OAuth2, redirect_uri: str, code: str
) -> OAuth2Token:
    """Get authorization token from the provided code."""
    return await client.get_access_token(code, redirect_uri)


def _get_json_web_key(token: Union[str, bytes]) -> Optional[str]:
    """Retrieve relevant public JSON Web Key from Azure Active Directory."""
    uuid = AUTHORIZE_ENDPOINT.split("/")[3]
    openid_config_url = (
        f"https://sts.windows.net/{uuid}/.well-known/openid-configuration"
    )
    jwks_uri = requests.get(openid_config_url).json()["jwks_uri"]
    jwks_keys = requests.get(jwks_uri).json()

    kid = jwt.get_unverified_header(token)["kid"]
    return next(
        (
            jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
            for jwk in jwks_keys["keys"]
            if jwk["kid"] == kid
        ),
        None,
    )


def _verify_authorization_token(
    authorization_token: Dict[str, Any],
    page_name: Optional[str] = None,
    query_string: Optional[str] = None,
) -> None:
    """Verify authorization token provided by Azure Active Directory."""
    st.session_state["user_info"] = None
    token = authorization_token.get("access_token")
    key = _get_json_web_key(token)
    try:
        payload = jwt.decode(
            jwt=token, key=key, algorithms=["RS256"], audience=AUDIENCE
        )
        payload.setdefault("PRID", "n/a")
        groups = payload.get("groups", [])
        if ALLOWED_GROUPS and not ALLOWED_GROUPS.intersection(groups):
            raise ValueError("Access not allowed for user group.")
    except Exception as e:
        st.error("Unable to authenticate, please try again.")
        st.error(e)
        st.stop()
    else:
        st.session_state.update(
            {
                "user_info": {
                    "name": payload["name"],
                    "email": payload["upn"],
                    "prid": payload["PRID"],
                    "roles": payload["roles"],
                },
                "authenticated": True,
                "admin": "APP-ADMIN" in groups,
            }
        )


def redirect(url: str) -> None:
    """Redirect to the given URL."""
    st.write(
        f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True
    )


def authenticate_user() -> None:
    """Authenticate a user using the OAuth protocol."""
    if (
        "authorization_token" not in st.session_state
        or st.session_state.authorization_token.is_expired()
    ):
        client = OAuth2(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        authorization_url = asyncio.run(
            _get_authorization_url(client=client, redirect_uri=REDIRECT_URI)
        )
        code, state, extra_params = _extract_query_params()
        if not code:
            redirect(authorization_url + "?" + urlencode(extra_params))
        else:
            try:
                authorization_token = asyncio.run(
                    _get_authorization_token(client, REDIRECT_URI, code)
                )
            except Exception:
                # st.write("Error during authentication. Please try again.")
                redirect(authorization_url)
            else:
                if authorization_token.is_expired():
                    # st.write("Login session has ended, please log in again.")
                    redirect(authorization_url)
                else:
                    st.session_state["authorization_token"] = authorization_token
                    _verify_authorization_token(
                        authorization_token,
                        page_name=state.get("page"),
                        query_string=urlencode(state),
                    )
    else:
        _verify_authorization_token(st.session_state.authorization_token)


def _extract_query_params() -> Tuple[Optional[str], Dict[str, Any], Dict[str, str]]:
    """Extract query parameters for authorization."""
    params = st.query_params
    extra_params = {}
    version = params.get("version")
    instance = params.get("instance")
    if version:
        extra_params["version"] = version
    if instance:
        extra_params["instance"] = instance
    try:
        code = params.get("code")
        state = (
            json.loads(params.get("state", [None])[0].replace("'", '"'))
            if "state" in params
            else {}
        )

        return code, state, extra_params
    except json.JSONDecodeError:
        return None, {}, extra_params
