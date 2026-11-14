"""과정(테마): task 이름 → (모델, 추론 정도). 노드는 모델을 고르지 않는다. 입구(llm().use)가 이 표로 고른다.

과정은 사용자가 고르는 단위다(화면 '과정별 모델'). 과정마다 급(작음·가운데·큼)과 추론 정도를 고르고,
모델 이름은 부를 때 지금 연결의 그 시리즈에서 가장 최신 이름으로 푼다(Claude: Haiku·Sonnet·Opus, OpenAI: Luna·Terra·Sol).
그래서 연결을 바꿔도 고른 급이 그대로 간다.
- read     문제 읽기(이미지에서 글).
- guide    풀이 가이드(뼈대, 채점 기준, 풀이).
- blocks   블록 설계와 힌트(같은 구조 판정 포함). 평가기 eval.judge도 여기다(튜터의 판정보다 센 모델이어야 평가를 믿는다).
- talk     대화. 매 턴 나가는 말(질문, 꼬리질문, 블록 채우기, 디버그 질문). 빠른 응답이 먼저다.
- judge    판정. 한 줄 [check].
- explain  해설.
- feedback 피드백.
- debug    디버그 진단(틀린 줄 찾기).
표에 없는 task는 talk다.

고르는 순서(뒤가 이긴다): 기본값 → 사용자가 고른 값(choose) → 환경 변수 ALGOBLOCK_THEME_<과정>=모델:정도(측정용. 예전 이름 INGEST·EXPLAIN도 받는다) → ALGOBLOCK_LLM_MODEL(모든 task를 한 모델로).
"""

import json
import os
import re
from pathlib import Path

EFFORTS = ("low", "medium", "high")
TIERS = ("small", "middle", "large")  # 작음·가운데·큼

# 연결마다 급 → 시리즈. ChatGPT 로그인과 OpenAI 키는 같은 OpenAI 시리즈다
SERIES = {"claude": ("haiku", "sonnet", "opus"), "chatgpt": ("luna", "terra", "sol"), "openai": ("luna", "terra", "sol")}
PREFIX = {"claude": "claude/", "chatgpt": "chatgpt/", "openai": "openai/"}
# 시리즈마다 지금 아는 최신 이름. 공급자 목록을 받지 못하면(오프라인, 권한 없음, ChatGPT 로그인) 이 이름을 쓴다.
# OpenAI 이름은 두 곳에서 확인했다: OpenAI 키의 모델 목록(/v1/models)과 Codex 공개 목록(codex-rs/models-manager/models.json). gpt-6-terra·gpt-6.1-luna는 둘 다에 없다
KNOWN = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5",
         "luna": "gpt-6-luna", "terra": "gpt-6.1-terra", "sol": "gpt-6.1-sol"}
# 버전을 읽을 수 있는 이름 꼴. 날짜가 붙은 스냅숏(claude-haiku-4-5-20251001)과 미리보기는 꼴이 맞지 않아 고르지 않는다
NAME_FORMS = (re.compile(r"claude-(haiku|sonnet|opus)-(\d+)(?:-(\d{1,2}))?"), re.compile(r"gpt-(\d+)(?:\.(\d+))?-(luna|terra|sol)"))
NEWEST: dict[str, dict[str, str]] = {}  # 공급자 목록에서 고른 시리즈마다 최신 이름 {연결: {시리즈: 이름}}. 서버가 채운다

# 과정 → (화면 이름, 기본 급, 기본 추론 정도). 문제 넣기 세 과정은 정확도를 먼저 보아 '중간'·high, 나머지는 측정으로 정했다. '큼'은 기본값으로 쓰지 않는다
THEMES = {
    "read": ("문제 읽기", "middle", "high"),
    "guide": ("풀이 가이드", "middle", "high"),
    "blocks": ("블록 설계와 힌트", "middle", "high"),
    "talk": ("대화", "small", "low"),
    "judge": ("판정", "small", "low"),
    "explain": ("해설", "small", "medium"),
    "feedback": ("피드백", "small", "medium"),
    "debug": ("디버그 진단", "small", "medium"),
}
TASKS = {"ingest.transcribe": "read", "plan.abstract": "guide", "plan.assess": "guide", "plan.solve": "guide", "plan.brute": "guide", "plan.cases": "guide",
         "plan.gate": "blocks", "plan.draft_blocks": "blocks", "plan.hints": "blocks", "eval.judge": "blocks",
         "explain.write": "explain", "feedback.assess": "feedback", "feedback.analyze": "feedback", "debug.locate": "debug"}
JUDGE_SUFFIX = (".judge", ".check_code")
# 예전 테마 다섯 → 새 과정. 저장된 설정을 옮기고, 측정용 환경 변수의 예전 이름(ALGOBLOCK_THEME_INGEST 등)을 받는 데 쓴다
OLD = {"ingest": ("read", "guide", "blocks"), "explain": ("explain", "feedback"), "talk": ("talk",), "judge": ("judge",), "debug": ("debug",)}

CHOSEN: dict[str, dict] = {}  # 사용자가 고른 값 {과정: {"tier": 급 또는 빈 글, "effort": 정도 또는 빈 글}}. 프로세스에 하나


def provider() -> str:
    """ALGOBLOCK_LLM_PROVIDER로 정한다. 안 정하면 가진 것을 본다: Claude 키 → ChatGPT 로그인 → OpenAI 키."""
    chosen = os.environ.get("ALGOBLOCK_LLM_PROVIDER", "").strip()
    if chosen in SERIES:
        return chosen
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return "claude"
    auth = os.environ.get("ALGOBLOCK_LLM_AUTH_DIR", "").strip()
    if auth and _plan_ready(Path(auth) / "chatgpt.json"):
        return "chatgpt"
    return "openai" if os.environ.get("OPENAI_API_KEY", "").strip() else "claude"


def _plan_ready(path: Path) -> bool:
    """ChatGPT 요금제 로그인 기록을 쓸 수 있는가(app/llm/openai/oauth/token.py의 usable과 같은 조건. 튜터는 app.llm을 바로 부르지 않는다)."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(record, dict) and bool(record.get("access_token") or record.get("refresh_token")) \
        and "chatgpt.tokens.use.direct" in (record.get("scopes") or []) and not record.get("note")


def theme_of(task: str | None) -> str:
    name = task or ""
    return TASKS.get(name) or ("judge" if name.endswith(JUDGE_SUFFIX) else "talk")


def version(name: str) -> tuple[str, int, int | None] | None:
    """(시리즈, 큰 수, 작은 수(없으면 None)). 꼴이 맞지 않으면 None."""
    for form in NAME_FORMS:
        found = form.fullmatch(name)
        if found:
            parts = found.groups()
            series, (major, minor) = (parts[0], parts[1:]) if parts[0].isalpha() else (parts[2], parts[:2])
            return series, int(major), None if minor is None else int(minor)
    return None


def newest(names) -> dict[str, str]:
    """모델 이름들에서 시리즈마다 버전이 가장 높은 이름 {시리즈: 이름}."""
    best: dict[str, tuple] = {}
    for name in names:
        found = version(name) if isinstance(name, str) else None
        if found:
            series, major, minor = found
            if series not in best or (major, minor or 0) > best[series][0]:
                best[series] = ((major, minor or 0), name)
    return {series: name for series, (_, name) in best.items()}


def model_of(tier: str, here: str | None = None) -> str:
    """이 연결에서 이 급의 모델 이름(앞부분 포함): 그 시리즈의 최신 이름."""
    here = here or provider()
    series = SERIES[here][TIERS.index(tier)]
    return PREFIX[here] + ((NEWEST.get(here) or {}).get(series) or KNOWN[series])


def label(model: str) -> str:
    """화면 이름: claude/claude-sonnet-5-5 → Sonnet 5.5, openai/gpt-6.1-terra → Terra (GPT-6.1). 꼴이 다르면 이름 그대로."""
    name = model.rpartition("/")[2]
    found = version(name)
    if found is None:
        return name
    series, major, minor = found
    number = str(major) if minor is None else f"{major}.{minor}"
    return f"{series.title()} {number}" if name.startswith("claude-") else f"{series.title()} (GPT-{number})"


def default(theme: str) -> tuple[str, str]:
    """이 과정의 기본 (급, 추론 정도)."""
    _, tier, effort = THEMES[theme]
    return tier, effort


def choose(settings: dict) -> None:
    """사용자가 고른 값을 통째로 바꿔 넣는다. 모르는 과정·급·정도는 버린다. 빈 값은 기본값을 쓴다는 뜻이다."""
    CHOSEN.clear()
    for theme, row in (settings or {}).items():
        if theme in THEMES and isinstance(row, dict):
            tier, effort = str(row.get("tier") or "").strip(), str(row.get("effort") or "").strip()
            CHOSEN[theme] = {"tier": tier if tier in TIERS else "", "effort": effort if effort in EFFORTS else ""}


def from_old(settings) -> dict:
    """예전 설정(테마 다섯, 모델 이름)을 새 과정의 급으로 옮긴다. 표에 있는 모델 이름만 급으로 바꾸고, 그 밖의 이름(Grok·OpenRouter, 직접 적은 이름)은 버린다(기본값)."""
    tiers = {name: TIERS[SERIES[here].index(series)] for here in ("claude", "openai") for series, name in KNOWN.items() if series in SERIES[here]}
    out = {}
    for old, row in (settings if isinstance(settings, dict) else {}).items():
        if old in OLD and isinstance(row, dict):
            tier = tiers.get(str(row.get("model") or "").rpartition("/")[2], "")
            out.update({theme: {"tier": tier, "effort": row.get("effort") or ""} for theme in OLD[old]})
    return out


def chosen(theme: str) -> tuple[str, str]:
    """기본값 위에 사용자가 고른 값을 얹은 (급, 추론 정도)."""
    tier, effort = default(theme)
    row = CHOSEN.get(theme) or {}
    return (row.get("tier") or tier), (row.get("effort") or effort)


def pick(task: str | None) -> tuple[str, str]:
    """(모델, 추론 정도)."""
    theme = theme_of(task)
    tier, effort = chosen(theme)
    model = model_of(tier)
    old = next(name for name, themes in OLD.items() if theme in themes)
    raw = (os.environ.get(f"ALGOBLOCK_THEME_{theme.upper()}", "") or os.environ.get(f"ALGOBLOCK_THEME_{old.upper()}", "")).strip()
    if raw:
        model, _, wanted = raw.partition(":")
        effort = wanted or effort
    override = os.environ.get("ALGOBLOCK_LLM_MODEL", "").strip()
    return (override or model), effort
