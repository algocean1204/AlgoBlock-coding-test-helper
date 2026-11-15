"""ChatGPT 요금제 로그인: 기기 아이디, 루프백 콜백, 코드 교환, ID 토큰 검증, 저장, 갱신.

저장 파일(ALGOBLOCK_LLM_AUTH_DIR, 0600, 원자적으로 쓴다):
- chatgpt-host.json  이 기기의 ext_agent_host_id(urn:uuid). 첫 로그인 전에 만들고 계속 쓴다.
- chatgpt.json       발급 client_id와 검증한 계정, 토큰, 허락된 범위. 다시 로그인할 때 발급 client_id를 쓴다.
예전 방식의 토큰 파일(openai-oauth.json)은 읽지 않는다.
"""

import hmac
import html
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from app.llm.errors import LlmError, LlmFailed, LlmNotConfigured, LlmTimeout
from app.llm.openai.oauth import idtoken
from app.llm.openai.oauth.pkce import ISSUER, PLAN_SCOPE, REGISTER_CLIENT, RESOURCE, TOKEN_URL, authorize_url, make_pkce
from app.llm.wire import timeout_seconds

# OpenAI 동의 화면이 "현재 워크스페이스와 플랜으로 계속할 수 없습니다"를 띄우는 계정은 연결할 수 없다. 앱은 그 화면을 볼 수 없으니
# 막힌 뒤의 안내에 이 경우를 함께 적는다(취소하면 access_denied, 그대로 계속하면 코드 교환이 invalid_grant로 끝난다)
PLAN_HINT = "OpenAI 동의 화면에 지금 워크스페이스나 플랜으로는 계속할 수 없다는 안내가 있었다면, 이 계정으로는 연결할 수 없어요. 그때는 API 키를 넣어 주세요."
PORT = 1455  # 쓰고 있으면 빈 포트를 쓴다(바뀌어도 되는 것은 포트뿐이다)
CALLBACK = "/auth/callback"
REFRESH_BEFORE = 120  # 만료 이만큼(초) 전부터 갱신한다
DEAD_REFRESH = {"invalid_grant", "invalid_refresh_token", "token_expired", "refresh_token_expired", "refresh_token_invalidated", "refresh_token_reused"}
RELOGIN = "ChatGPT 연결이 끝났어요. ‘ChatGPT로 로그인’으로 다시 로그인해 주세요."
NO_PLAN = "ChatGPT 요금제 사용을 허락하지 않아 튜터에 쓸 수 없어요. ‘ChatGPT로 로그인’으로 다시 허락하거나 API 키를 넣어 주세요."
OLD = "예전 방식의 ChatGPT 로그인은 더 쓰지 않아요. ‘ChatGPT로 로그인’으로 다시 로그인해 주세요."
DONE = "연결됐어요. 이 창을 닫고 AlgoBlock으로 돌아가 주세요."

_login = {"server": None, "error": None, "pending": None}
_lock = threading.Lock()
_refresh_lock = threading.Lock()  # ponytail: 한 프로세스 안에서만 갱신을 줄 세운다. 앱 두 개를 함께 띄우면 파일 잠금이 필요하다


class Refused(LlmFailed):
    """토큰 주소가 거절했다. code는 응답의 오류 코드(없으면 빈 글)."""

    def __init__(self, code: str, status: int):
        super().__init__(f"ChatGPT 로그인 서버가 거절했어요({code or f'상태 {status}'}).")
        self.code = code


def auth_dir() -> Path:
    raw = os.environ.get("ALGOBLOCK_LLM_AUTH_DIR", "").strip()
    if not raw:
        raise LlmNotConfigured("모델이나 키가 없습니다.")
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def token_path() -> Path:
    return auth_dir() / "chatgpt.json"


def host_id() -> str:
    """이 기기의 ext_agent_host_id. 없으면 UUIDv4로 한 번 만들어 둔다(사람을 알아볼 수 있는 값을 넣지 않는다)."""
    path = auth_dir() / "chatgpt-host.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("ext_agent_host_id")
    except (OSError, ValueError, AttributeError):
        value = None
    if isinstance(value, str) and value.startswith("urn:uuid:"):
        return value
    value = f"urn:uuid:{uuid.uuid4()}"
    _write(path, {"ext_agent_host_id": value})
    return value


def _record() -> dict:
    try:
        data = json.loads(token_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def usable(record: dict) -> bool:
    """토큰이 있고, 요금제 사용 범위를 허락받았고, 막힌 까닭(note)이 없다."""
    return bool(record.get("access_token") or record.get("refresh_token")) and PLAN_SCOPE in (record.get("scopes") or []) and not record.get("note")


def login_status() -> dict:
    try:
        record = _record()
        old = not record and (auth_dir() / "openai-oauth.json").exists()
    except LlmError:
        record, old = {}, False
    connected = usable(record)
    error = _login["error"]
    if not connected and not error:
        error = record.get("note") or (NO_PLAN if record.get("access_token") or record.get("refresh_token") else OLD if old else None)
    return {"connected": connected, "error": error}


def begin_login(timeout: float = 300) -> dict:
    """리스너를 먼저 띄우고, 이번 시도의 state·nonce·PKCE로 인가 주소를 만든다. 사용자는 돌려받은 url을 시스템 브라우저로 연다."""
    _stop()
    host = host_id()
    saved = _record()
    client = saved.get("client_id") or ""
    server = _listen()
    redirect = f"http://127.0.0.1:{server.server_address[1]}{CALLBACK}"
    verifier, challenge = make_pkce()
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    pending = {"state": state, "nonce": nonce, "verifier": verifier, "redirect": redirect, "client_id": client, "host": host,
               "subject": saved.get("subject") or ""}
    with _lock:
        _login.update(server=server, error=None, pending=pending)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    timer = threading.Timer(timeout, _stop, args=(server,))
    timer.daemon = True
    timer.start()
    url = authorize_url(client_id=client, host_id=host, redirect=redirect, state=state, nonce=nonce, challenge=challenge,
                        id_token_hint=saved.get("id_token") or "", login_hint=saved.get("email") or "",
                        consent=bool(client) and PLAN_SCOPE not in (saved.get("scopes") or []))
    return {"url": url, "state": state}


def finish_login(query: dict, pending: dict) -> dict:
    """state는 부르는 쪽이 이미 견줬다. 오류 → 발급 client_id → 코드 교환 → ID 토큰 검증 → 저장."""
    if query.get("error") == "access_denied":
        raise LlmFailed(f"ChatGPT에서 허락하지 않아 연결하지 않았어요. {PLAN_HINT}")
    if query.get("error"):
        raise LlmFailed(f"ChatGPT 로그인이 끝나지 않았어요({query['error'][:60]}).")
    client, given = pending["client_id"], query.get("client_id") or ""
    if client and given and given != client:
        raise LlmFailed("다른 등록의 응답이라 받지 않았어요. 다시 시도해 주세요.")
    if not client:
        if not given or given == REGISTER_CLIENT:
            raise LlmFailed("ChatGPT 등록이 끝나지 않았어요. 다시 시도해 주세요.")
        client = given
        _write(token_path(), {"issuer": ISSUER, "client_id": client, "ext_agent_host_id": pending["host"]})  # 교환이 실패해도 다음 시도는 이 client_id로 한다
    if not query.get("code"):
        raise LlmFailed("ChatGPT 로그인이 끝나지 않았어요. 다시 시도해 주세요.")
    try:
        payload = _token({"grant_type": "authorization_code", "client_id": client, "code": query["code"],
                          "code_verifier": pending["verifier"], "redirect_uri": pending["redirect"], "resource": RESOURCE})
    except Refused as exc:
        if exc.code == "invalid_grant":
            raise LlmFailed(f"ChatGPT 로그인을 마치지 못했어요. 로그인 코드가 지났다면 다시 시도해 주세요. {PLAN_HINT}") from exc
        raise
    claims = idtoken.verify(payload.get("id_token") or "", client_id=client, nonce=pending["nonce"])
    if pending["subject"] and claims["sub"] != pending["subject"]:
        raise LlmFailed("처음 연결한 ChatGPT 계정과 달라요. 그 계정으로 로그인해 주세요.")
    record = {"email": claims.get("email") or "", "issuer": ISSUER, "subject": claims["sub"], "client_id": client,
              "ext_agent_host_id": pending["host"], "id_token": payload["id_token"], **_tokens(payload, {})}
    _write(token_path(), record)
    return record


def _tokens(payload: dict, old: dict) -> dict:
    """토큰 응답에서 함께 바꿀 값들(액세스 토큰, 만료, 범위, 갱신 토큰). 빠진 값은 이전 값을 둔다."""
    scope = payload.get("scope")
    return {"access_token": payload["access_token"], "refresh_token": payload.get("refresh_token") or old.get("refresh_token") or "",
            "token_type": payload.get("token_type") or "Bearer", "expires_in": int(payload.get("expires_in") or 3600),
            "scopes": sorted(scope.split()) if isinstance(scope, str) else old.get("scopes") or [],
            "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _expires_at(record: dict) -> float:
    try:
        return datetime.fromisoformat(record["saved_at"]).timestamp() + int(record["expires_in"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def access_token() -> str:
    """만료가 가까우면 갱신한다. 갱신 토큰을 더 쓸 수 없으면 토큰을 지우고 다시 로그인하라고 한다."""
    record = _record()
    if not usable(record):
        raise LlmNotConfigured(login_status()["error"] or "ChatGPT가 연결되어 있지 않아요.")
    if record.get("access_token") and _expires_at(record) > time.time() + REFRESH_BEFORE:
        return record["access_token"]
    with _refresh_lock:
        record = _record()  # 다른 요청이 먼저 갱신했을 수 있다
        if record.get("access_token") and _expires_at(record) > time.time() + REFRESH_BEFORE:
            return record["access_token"]
        if not record.get("refresh_token"):
            mark(RELOGIN)
            raise LlmNotConfigured(RELOGIN)
        try:
            payload = _token({"grant_type": "refresh_token", "client_id": record["client_id"],
                              "refresh_token": record["refresh_token"], "resource": RESOURCE})
        except Refused as exc:
            if exc.code in DEAD_REFRESH:
                _write(token_path(), {**record, "access_token": "", "refresh_token": "", "note": RELOGIN})
                raise LlmNotConfigured(RELOGIN) from exc
            if exc.code == "invalid_client":
                raise LlmFailed("ChatGPT 등록 설정이 맞지 않아요(invalid_client).") from exc
            raise
        record = {**record, **_tokens(payload, record)}
        _write(token_path(), record)
    if not usable(record):
        raise LlmNotConfigured(NO_PLAN)
    return record["access_token"]


def mark(note: str) -> None:
    """이 연결을 더 쓰지 않는다(까닭을 남긴다). 토큰은 지우지 않는다. 다시 로그인하면 새 기록으로 바뀐다."""
    record = _record()
    if record:
        _write(token_path(), {**record, "note": note})


def _code_of(raw: bytes) -> str:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    error = data.get("error")
    if isinstance(error, dict):
        error = error.get("code") or error.get("type")
    return str(error or data.get("code") or "")[:80]


def _token(form: dict) -> dict:
    request = urllib.request.Request(TOKEN_URL, data=urlencode(form).encode("utf-8"),
                                     headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise Refused(_code_of(exc.read()), exc.code) from None
    except TimeoutError as exc:
        raise LlmTimeout("60초를 넘겼습니다.") from exc
    except urllib.error.URLError as exc:
        raise LlmFailed("ChatGPT 로그인 서버에 연결하지 못했어요.") from exc
    except ValueError as exc:
        raise LlmFailed("ChatGPT 로그인 서버의 답 모양이 맞지 않아요.") from exc
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise LlmFailed("ChatGPT 로그인 서버의 답 모양이 맞지 않아요.")
    return payload


def _write(path: Path, data: dict) -> None:
    """같은 폴더의 임시 파일(0600)에 다 쓴 뒤 바꿔 끼운다."""
    temp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data))
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temp, 0o600)
    os.replace(temp, path)


def _listen() -> HTTPServer:
    for port in (PORT, 0):
        try:
            server = HTTPServer(("127.0.0.1", port), _Callback)
        except OSError:
            continue
        return server
    raise LlmFailed("로그인을 받을 포트를 열 수 없어요.")


def _stop(server: HTTPServer | None = None) -> None:
    """지금 리스너(또는 넘겨받은 리스너)를 닫는다."""
    with _lock:
        current = _login["server"]
        if current is None or (server is not None and server is not current):
            return
        _login.update(server=None, pending=None)
    current.shutdown()
    current.server_close()


class _Callback(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        with _lock:
            pending = _login["pending"]
            if url.path != CALLBACK or not pending or not hmac.compare_digest(query.get("state", "").encode(), pending["state"].encode()):
                pending = None
            else:
                _login["pending"] = None  # 한 번만 쓴다
        if pending is None:  # 이 시도의 응답이 아니다. 리스너는 그대로 둔다
            self.send_error(404)
            return
        try:
            finish_login(query, pending)
            error = None
        except (LlmError, OSError, ValueError, KeyError) as exc:
            error = str(exc) or "ChatGPT 로그인을 끝내지 못했어요."
        _login["error"] = error
        text = error or login_status()["error"] or DONE
        body = f"<!doctype html><meta charset='utf-8'><title>AlgoBlock</title><p>{html.escape(text)}</p>".encode("utf-8")
        self.send_response(400 if error else 200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        # 같은 스레드에서 shutdown하면 멈추므로 따로 닫는다.
        threading.Thread(target=_stop, args=(self.server,), daemon=True).start()

    def log_message(self, *args):  # 주소에 코드가 실리므로 남기지 않는다
        pass
