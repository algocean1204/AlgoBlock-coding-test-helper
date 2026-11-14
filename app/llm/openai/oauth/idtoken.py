"""ID 토큰(RS256 JWT)을 OpenAI가 공개한 JWKS로 검증한다. 표준 라이브러리만 쓴다(RSASSA-PKCS1-v1_5 + SHA-256을 pow로 푼다)."""

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from app.llm.errors import LlmFailed
from app.llm.openai.oauth.pkce import ISSUER, JWKS_URL
from app.llm.wire import timeout_seconds

SKEW = 5  # 시계 어긋남 허용(초)
SHA256_INFO = bytes.fromhex("3031300d060960864801650304020105000420")  # DigestInfo(SHA-256) 머리
_keys: dict[str, tuple[int, int]] = {}  # kid → (n, e). 모르는 kid가 오면 다시 받는다


def _b64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _fail(why: str) -> LlmFailed:
    return LlmFailed(f"ChatGPT 로그인을 확인하지 못했어요({why}). 다시 시도해 주세요.")


def fetch_jwks() -> dict:
    try:
        with urllib.request.urlopen(JWKS_URL, timeout=timeout_seconds()) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise _fail("확인 키를 받지 못함") from exc


def _key(kid: str, fetch) -> tuple[int, int]:
    if kid not in _keys:
        _keys.clear()
        for row in fetch().get("keys") or []:
            if isinstance(row, dict) and row.get("kty") == "RSA" and row.get("kid") and row.get("use", "sig") == "sig":
                _keys[row["kid"]] = (int.from_bytes(_b64(row["n"]), "big"), int.from_bytes(_b64(row["e"]), "big"))
    if kid not in _keys:
        raise _fail("모르는 키")
    return _keys[kid]


def rs256_ok(signed: bytes, signature: bytes, n: int, e: int) -> bool:
    """RFC 8017 8.2.2: s^e mod n을 펼쳐 기대하는 EMSA-PKCS1-v1_5 모양과 통째로 견준다."""
    size = (n.bit_length() + 7) // 8
    if len(signature) != size or int.from_bytes(signature, "big") >= n:
        return False
    tail = SHA256_INFO + hashlib.sha256(signed).digest()
    if size < len(tail) + 11:
        return False
    expected = b"\x00\x01" + b"\xff" * (size - len(tail) - 3) + b"\x00" + tail
    return hmac.compare_digest(pow(int.from_bytes(signature, "big"), e, n).to_bytes(size, "big"), expected)


def verify(id_token: str, *, client_id: str, nonce: str, now: float | None = None, fetch=fetch_jwks) -> dict:
    """서명·iss·aud(발급 client_id)·exp·iat·nonce·sub를 본다. 맞으면 클레임을 돌려준다."""
    try:
        head_part, body_part, sig_part = id_token.split(".")
        head, claims, signature = json.loads(_b64(head_part)), json.loads(_b64(body_part)), _b64(sig_part)
    except (AttributeError, ValueError) as exc:
        raise _fail("모양") from exc
    if not isinstance(head, dict) or not isinstance(claims, dict) or head.get("alg") != "RS256":
        raise _fail("서명 방식")
    n, e = _key(str(head.get("kid") or ""), fetch)
    if not rs256_ok(f"{head_part}.{body_part}".encode("ascii"), signature, n, e):
        raise _fail("서명")
    now = time.time() if now is None else now
    aud = claims.get("aud")
    audiences = aud if isinstance(aud, list) else [aud]
    if claims.get("iss") != ISSUER:
        raise _fail("발급자")
    if not client_id or client_id not in audiences or (len(audiences) > 1 and claims.get("azp") != client_id):
        raise _fail("대상")
    if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] + SKEW <= now or not isinstance(claims.get("iat"), (int, float)):
        raise _fail("만료")
    if not nonce or not hmac.compare_digest(str(claims.get("nonce") or "").encode(), nonce.encode()):
        raise _fail("nonce")
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise _fail("계정")
    return claims
