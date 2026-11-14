# llm

노드가 모델을 부르는 입구다. 공급자 구현은 `app/llm`이다.

```python
llm(model_name()).use(messages, schema, task="plan.assess")
```

- 글 모드(`schema=None`)는 JSON을 요구하지 않고 모델 글을 그대로 돌려준다(판정 `[check]`, 말풍선).
- 모델은 task의 과정(`themes.py`)이 고른 급을 지금 연결의 그 시리즈 최신 이름으로 푼 것이다. `ALGOBLOCK_LLM_MODEL`이 있으면 모든 task가 그 모델을 쓴다. 앞부분이 공급자를 고른다(`claude/`, `openai/`, `chatgpt/`). 키는 공급자 환경 변수(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)를 먼저 보고, 없으면 `ALGOBLOCK_LLM_API_KEY`다.
- 한 번이 한 노드다. 제한은 60초(`ALGOBLOCK_LLM_TIMEOUT`). 오류는 `LlmNotConfigured`, `LlmTimeout`, `LlmFailed`.
- `cached_user(lines, head)`는 앞 `head`줄(문제 글 같은 고정 앞부분)을 캐시 대상으로 표시한 사용자 메시지를 만든다.

| 부르는 곳 | 가는 곳 |
| --- | --- |
| `use_llm(가짜)` 안 | 끼운 가짜. 시험이 쓴다 |
| 그 밖 | `app.llm.session.llm`. `app.llm`이 이미 import되는 곳이면 그것을 쓰고, 아니면 저장소 루트(`app/`의 위)를 경로에 더한다. 공급자 예외는 같은 이름의 예외로 바꾼다 |

`FakeLlm`은 task별 대본을 차례로 주고 `calls`에 입력을 남긴다.
