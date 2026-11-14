"""HTTP JSON. 테스트는 set_transport로 갈아 끼운다."""

import json
import os
import time
import urllib.error
import urllib.request

from app.llm.errors import LlmFailed, LlmNotConfigured, LlmTimeout

_transport = None


def timeout_seconds() -> float:
    raw = os.environ.get("ALGOBLOCK_LLM_TIMEOUT", "60")
    try:
        return float(raw)
    except ValueError:
        return 60.0


def set_transport(fn):
    global _transport
    _transport = fn


RETRY_STATUS = (408, 409, 429, 500, 502, 503, 504, 529)  # 잠깐 뒤 다시 하면 되는 응답(한도 초과, 과부하 등)
RETRIES = 2


def post_json(url: str, headers: dict, body: dict, timeout: float | None = None) -> dict:
    """JSON을 보내고 JSON을 받는다. 한도 초과·과부하는 제한 시간 안에서 두 번까지 다시 보낸다(1초, 2초 쉬고). body가 None이면 GET이다(모델 목록)."""
    limit = timeout_seconds() if timeout is None else timeout
    if _transport is not None:
        return _transport(url, headers, body, limit)
    data = None if body is None else json.dumps(body).encode("utf-8")
    began = time.monotonic()
    for attempt in range(RETRIES + 1):
        left = limit - (time.monotonic() - began)
        if left <= 0:
            raise LlmTimeout("60초를 넘겼습니다.")
        request = urllib.request.Request(url, data=data, headers=headers, method="GET" if body is None else "POST")
        try:
            with urllib.request.urlopen(request, timeout=left) as response:
                return json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise LlmTimeout("60초를 넘겼습니다.") from exc
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_STATUS and attempt < RETRIES:
                after = (exc.headers.get("retry-after") or "").strip()  # 초 대신 날짜 글이 오면 기본 간격을 쓴다
                wait = min(float(after) if after.isdigit() else attempt + 1, 5.0)
                if time.monotonic() - began + wait < limit:
                    time.sleep(wait)
                    continue
            if exc.code in (401, 403):
                raise LlmNotConfigured(f"키를 확인해 주세요({exc.code}).") from exc
            raise LlmFailed(f"공급자 오류({exc.code})") from exc
        except urllib.error.URLError as exc:
            if "timed out" in str(exc).lower():
                raise LlmTimeout("60초를 넘겼습니다.") from exc
            raise LlmFailed("공급자에 연결하지 못했습니다.") from exc
    raise LlmFailed("공급자 오류")
