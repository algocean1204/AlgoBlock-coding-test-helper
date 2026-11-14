"""OpenAI 임베딩. 플랫폼 키로만 부를 수 있다(ChatGPT 구독 토큰으로는 안 된다)."""

from app.llm.errors import LlmFailed
from app.llm.openai.api_key.chat import _key
from app.llm.wire import post_json

URL = "https://api.openai.com/v1/embeddings"
MODEL = "text-embedding-3-small"  # 1536차원


def embed(texts: list[str], model: str = MODEL) -> list[list[float]]:
    payload = post_json(URL, {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"}, {"model": model, "input": texts})
    rows = sorted(payload.get("data") or [], key=lambda row: row.get("index", 0))
    if len(rows) != len(texts):
        raise LlmFailed("공급자 오류")
    return [row["embedding"] for row in rows]
