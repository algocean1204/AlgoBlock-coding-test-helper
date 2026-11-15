"""API 키 확인: 그 공급자의 공식 주소에 모델 목록 조회를 한 번 보낸다(요금이 들지 않는다).

결과는 여섯 가지다.
- ok: 200. 쓸 수 있는 키
- invalid: 401. 키가 틀림
- denied: 403. 키는 있지만 모델 목록을 볼 권한이 없음
- limited: 429. 키는 맞지만 지금 요청 한도에 걸림
- server: 5xx·529. 공급자 쪽이 답하지 않음
- offline: 연결하지 못함, 시간 초과, 리다이렉트, 그 밖의 응답
주소는 이 모듈의 상수뿐이다(환경 변수로 바꾸지 않는다). 다시 보내지 않고, 리다이렉트는 따라가지 않는다(키 헤더가 다른 주소로 넘어가지 않게).
키 값은 반환값과 예외에 싣지 않는다. 시험은 `opener`를 가짜로 갈아 끼운다.
"""

import urllib.error
import urllib.request

from app.llm.claude.api_key.messages import MODELS_URL as CLAUDE_URL
from app.llm.openai.api_key.chat import MODELS_URL as OPENAI_URL

TIMEOUT = 10.0  # 초
OK, INVALID, DENIED, LIMITED, SERVER, OFFLINE = "ok", "invalid", "denied", "limited", "server", "offline"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # 따라가지 않으면 urllib가 3xx를 HTTPError로 낸다


OPENER = urllib.request.build_opener(_NoRedirect)


def request_for(provider: str, key: str) -> urllib.request.Request:
    if provider == "claude":
        return urllib.request.Request(CLAUDE_URL, headers={"x-api-key": key, "anthropic-version": "2023-06-01"}, method="GET")
    if provider == "openai":
        return urllib.request.Request(OPENAI_URL, headers={"Authorization": f"Bearer {key}"}, method="GET")
    raise ValueError("지원하지 않는 공급자예요.")


def check(provider: str, key: str, opener=OPENER.open, timeout: float = TIMEOUT) -> str:
    """키가 쓸 수 있는지 본다. 어떤 실패도 예외로 내보내지 않고 결과 글자 하나로 돌려준다."""
    request = request_for(provider, key)
    try:
        with opener(request, timeout=timeout) as response:
            return OK if 200 <= response.status < 300 else OFFLINE
    except urllib.error.HTTPError as exc:
        code = exc.code
        return INVALID if code == 401 else DENIED if code == 403 else LIMITED if code == 429 else SERVER if code >= 500 else OFFLINE
    except Exception:  # noqa: BLE001 - 연결 실패·시간 초과 등. 예외 글에 키가 든 주소·헤더가 있을 수 있어 글은 버린다
        return OFFLINE
