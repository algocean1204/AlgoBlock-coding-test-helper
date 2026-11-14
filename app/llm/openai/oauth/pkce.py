"""Sign in with ChatGPT(오픈소스 앱의 ChatGPT 요금제 사용) 인가 요청. 공개 클라이언트라 비밀값이 없다."""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

ISSUER = "https://auth.openai.com"
AUTHORIZE_URL = f"{ISSUER}/api/accounts/authorize"
TOKEN_URL = f"{ISSUER}/api/accounts/oauth/token"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"
RESOURCE = "https://api.openai.com/v1"
REGISTER_CLIENT = "dynamic_agent_client"  # 첫 등록의 입구일 뿐이다. 저장하거나 토큰 교환에 쓰지 않는다
AGENT_NAME = "AlgoBlock"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
SCOPE = f"openid profile email offline_access resource.invoke {PLAN_SCOPE}"


def make_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def authorize_url(*, client_id: str, host_id: str, redirect: str, state: str, nonce: str, challenge: str,
                  id_token_hint: str = "", login_hint: str = "", consent: bool = False) -> str:
    """client_id가 비면 첫 등록(dynamic_agent_client + agent_name_hint), 있으면 다시 로그인(힌트를 붙인다)."""
    query = {"client_id": client_id or REGISTER_CLIENT}
    if not client_id:
        query["agent_name_hint"] = AGENT_NAME
    query["ext_agent_host_id"] = host_id
    if client_id and id_token_hint:
        query["id_token_hint"] = id_token_hint
    if client_id and login_hint:
        query["login_hint"] = login_hint
    query.update(response_type="code", redirect_uri=redirect, scope=SCOPE, resource=RESOURCE, state=state, nonce=nonce,
                 code_challenge_method="S256", code_challenge=challenge)
    if consent:  # 요금제 사용을 거절했던 등록에서 다시 허락을 묻는다
        query["prompt"] = "consent"
    return f"{AUTHORIZE_URL}?{urlencode(query)}"
