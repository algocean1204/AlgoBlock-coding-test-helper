"""평가·QA 전용 모델 연결: 이 PC에 사용자가 설치하고 로그인한 공식 Claude Code(`claude -p`)를 부른다.

API 키 없이 개발자 본인이 평가를 돌릴 때만 쓴다. 제품(배포 앱)의 모델 연결이 아니다(구독 자격증명을 앱이 다루지 않는다).
FakeLlm과 같은 모양(run)이라 use_llm(ClaudeCli())로 끼운다. 사용자 CLAUDE.md·도구·MCP는 싣지 않는다.
제약: max_tokens·cache_control을 정할 수 없다(Claude Code가 자체 캐시를 붙인다). 공급자 요청 모양 검증은 tests의 가짜 HTTP가 맡는다.
"""

import json
import os
import subprocess
import tempfile
import threading
import time

from ..llm.client import coerce, record_usage
from ..llm.errors import LlmFailed, LlmTimeout



class ClaudeCli:
    def __init__(self, tutor_model: str = "haiku", judge_model: str | None = None, parallel: int = 6, timeout: float = 180):
        self.tutor_model = tutor_model
        self.judge_model = judge_model or os.environ.get("ALGOBLOCK_EVAL_JUDGE_CLI_MODEL", "sonnet")
        self.gate = threading.Semaphore(parallel)
        self.timeout = timeout
        self.calls: list[dict] = []
        self.lock = threading.Lock()

    def model_for(self, task: str, params: dict) -> str:
        """평가기는 따로 정한 모델, 튜터 작업은 과정표가 고른 급(큼·가운데·작음)을 CLI 이름(opus·sonnet·haiku)으로. OpenAI 이름도 급으로 옮긴다."""
        if task.startswith("eval.judge"):
            return self.judge_model
        if task.startswith("eval."):
            return self.tutor_model
        model = str(params.get("model") or "")
        return next((cli for cli, words in (("opus", ("opus", "-sol")), ("sonnet", ("sonnet", "-terra"))) if any(word in model for word in words)), "haiku")

    def run(self, task, messages, schema, images=None, params=None):
        if images:  # 이 연결은 그림을 넘기지 못한다. 글만 보내면 모델이 보지 못한 그림을 설명하는 글이 문제 글이 된다(읽기는 기기의 글자 읽기로 넘어간다)
            raise LlmFailed("이 연결은 그림을 넘기지 못합니다.")
        system = "\n".join(m["content"] for m in messages if m.get("role") == "system")
        user = "\n\n".join(m["content"] for m in messages if m.get("role") != "system")
        if schema is not None:
            user += "\n\nJSON만 반환. 키: " + ", ".join(getattr(schema, "__dataclass_fields__", {}))
        params = params or {}
        model = self.model_for(task, params)
        cmd = ["claude", "-p", "--model", model, "--tools", "", "--system-prompt", system or "너는 도우미다.",
               "--no-session-persistence", "--setting-sources", "", "--strict-mcp-config", "--output-format", "json"]
        if params.get("effort") and not task.startswith("eval."):
            cmd += ["--effort", params["effort"]]  # 등급표의 추론 정도 그대로
        began = time.monotonic()
        with self.gate:
            try:
                done = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=self.timeout,
                                      cwd=tempfile.gettempdir())
            except subprocess.TimeoutExpired as exc:
                raise LlmTimeout("시간을 넘겼습니다.") from exc
        try:
            out = json.loads(done.stdout)
        except json.JSONDecodeError as exc:
            raise LlmFailed(f"CLI 출력이 JSON이 아닙니다: {done.stderr[-200:]}") from exc
        if out.get("is_error"):
            raise LlmFailed(str(out.get("result"))[:200])
        usage = out.get("usage") or {}
        # 사용 기록에는 'cli/<급>'으로 남긴다: 호출 수와 과정 이름은 남고 금액은 0이다(구독으로 돈다. eval/cost.py)
        record_usage(task, f"cli/{model}", usage, time.monotonic() - began, effort=params.get("effort"))
        with self.lock:
            self.calls.append({
                "task": task, "model": model, "thread": threading.current_thread().name,
                "seconds": round(time.monotonic() - began, 2),
                "input": int(usage.get("input_tokens") or 0),
                "cache_read": int(usage.get("cache_read_input_tokens") or 0),
                "cache_write": int(usage.get("cache_creation_input_tokens") or 0),
                "output": int(usage.get("output_tokens") or 0),
            })
        text = out.get("result") or ""
        if schema is None:
            return text
        raw = text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        start, end = raw.find("{"), raw.rfind("}")
        try:
            return coerce(schema, json.loads(raw[start : end + 1]))
        except (json.JSONDecodeError, ValueError) as exc:
            raise LlmFailed("모양이 맞지 않습니다.") from exc
