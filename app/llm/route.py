"""모델 이름 앞부분으로 공급자와 인증을 고른다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    provider: str
    auth: str
    model: str


_PREFIXES = (
    ("openai-oauth/", "openai", "oauth"),
    ("chatgpt/", "openai", "oauth"),
    ("openai/", "openai", "api_key"),
    ("claude/", "claude", "api_key"),
    ("anthropic/", "claude", "api_key"),
)


def route(model: str, auth: str | None = None) -> Route:
    name = (model or "").strip()
    for prefix, provider, default_auth in _PREFIXES:
        if name.startswith(prefix):
            chosen = auth or default_auth
            if provider == "claude" and chosen == "oauth":
                chosen = "api_key"
            return Route(provider, chosen, name[len(prefix) :])
    if name.startswith("gpt-"):
        return Route("openai", auth or "api_key", name)
    if name.startswith("claude-"):
        return Route("claude", "api_key", name)
    return Route("", auth or "api_key", name)
