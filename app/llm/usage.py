"""호출마다 토큰 사용량(캐시 읽기·쓰기 포함)을 남긴다. 평가 도구가 캐시 적중률을 잰다.

ALGOBLOCK_LLM_USAGE_LOG(파일 경로)가 있으면 한 줄씩 JSON으로 덧붙인다(서버가 자료 폴더의 usage.jsonl로 정한다).
적는 것은 과정·모델·토큰·시간·다시 시도 여부뿐이다. 키와 프롬프트 글은 적지 않는다(eval/cost.py가 묶어 본다).
"""

import json
import os
import threading
import time
from collections import deque

RECENT: deque = deque(maxlen=2000)  # 한계: 메모리 안 최근 기록만. 영구 통계가 필요하면 SQLite로
_LOCK = threading.Lock()


def tokens(payload: dict) -> dict:
    """공급자 응답의 usage를 한 모양으로. input은 캐시를 뺀 새 입력이다."""
    raw = payload.get("usage") or {}
    if "input_tokens_details" not in raw:
        # Anthropic 모양: input_tokens는 이미 캐시를 뺀 값
        return {
            "input": int(raw.get("input_tokens") or 0),
            "cache_read": int(raw.get("cache_read_input_tokens") or 0),
            "cache_write": int(raw.get("cache_creation_input_tokens") or 0),
            "output": int(raw.get("output_tokens") or 0),
        }
    details = raw.get("input_tokens_details") or {}
    cached = int(details.get("cached_tokens") or 0)
    total_in = int(raw.get("input_tokens") or 0)
    return {
        "input": max(total_in - cached, 0),
        "cache_read": cached,
        "cache_write": 0,
        "output": int(raw.get("output_tokens") or 0),
    }


def record(task: str | None, model: str, payload: dict, seconds: float, retry: bool = False, effort: str | None = None) -> None:
    """retry: 모양이 깨진 답을 다시 받은 호출(같은 요청을 한 번 더 보냈다)."""
    row = {"task": task, "model": model, "effort": effort, "seconds": round(seconds, 2), "retry": retry, **tokens(payload)}
    RECENT.append(row)
    path = os.environ.get("ALGOBLOCK_LLM_USAGE_LOG", "").strip()
    if not path:
        return
    line = json.dumps({"at": round(time.time(), 3), **row}, ensure_ascii=False)
    try:
        with _LOCK, open(path, "a", encoding="utf-8") as file:
            file.write(line + "\n")
    except OSError:  # 기록을 못 남겨도 호출은 그대로 쓴다
        pass
