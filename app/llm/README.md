# app/llm

모델 공급자 연결 코드다. 튜터는 `tutor/llm`을 거쳐 이 폴더의 `session.llm`을 부른다. 부르는 형태는 `llm("claude/claude-sonnet-5-5").use(messages, schema, task=...)`다. 연결 방식과 모델 고르기의 전체 그림은 [Docs/architecture/models-and-cost.md](../../Docs/architecture/models-and-cost.md)에 있다.

| 폴더 | 하는 일 |
| --- | --- |
| `openai/api_key` | 플랫폼 키(`OPENAI_API_KEY`). Responses `https://api.openai.com/v1/responses` |
| `openai/oauth` | ChatGPT 요금제(OpenAI의 Sign in with ChatGPT, 오픈소스 앱 흐름. 미리 보기 단계). 로그인은 `pkce.py`·`token.py`, ID 토큰 검증은 `idtoken.py`. Responses `https://api.openai.com/v1/responses`에 `store: false`, `stream: true`로 보낸다(`chat.py`) |
| `claude/api_key` | `ANTHROPIC_API_KEY`(`x-api-key`). Messages API |
| `openai/api_key/embed.py` | 임베딩(text-embedding-3-small). `https://api.openai.com/v1/embeddings`. 플랫폼 키 전용이다. 앱의 색인은 이것을 쓰지 않는다. 측정 도구(`tutor/eval/recall_bench.py`)만 쓴다 |

모델 이름 앞부분이 공급자와 인증을 고른다(`route.py`): `claude/`(또는 `anthropic/`), `openai/`, `chatgpt/`(또는 `openai-oauth/`, ChatGPT 요금제). 키는 공급자 환경 변수를 먼저 보고 없으면 `ALGOBLOCK_LLM_API_KEY`다. 지원하는 공급자는 Claude와 OpenAI 둘이다.

키 경로는 모델 목록도 준다: `claude.api_key.messages.models()`(`GET /v1/models?limit=1000`), `openai.api_key.chat.models()`(`GET /v1/models`). 돈이 들지 않는다. 화면 서버가 시리즈마다 최신 이름을 고르는 데 쓴다(`tutor/llm/themes.py`의 `newest`). ChatGPT 요금제 경로는 `openai.oauth.chat.models()`(`GET /v1/models`의 `models` 가운데 `visibility`가 `list`인 `slug`)다.

## 구독 로그인

- ChatGPT: `openai.oauth.token.begin_login()`이 콜백 리스너(`http://127.0.0.1:1455/auth/callback`, 쓰고 있으면 빈 포트)를 먼저 띄우고 `{"url", "state"}`를 돌려준다. 사용자는 그 주소를 시스템 브라우저로 연다.
  - 인가 요청: 처음은 `client_id=dynamic_agent_client`와 `agent_name_hint=AlgoBlock`, 다음부터는 저장한 발급 `client_id`와 `id_token_hint`·`login_hint`. 늘 기기 아이디 `ext_agent_host_id`(`urn:uuid:`, `chatgpt-host.json`), 범위 `openid profile email offline_access resource.invoke chatgpt.tokens.use.direct`, `resource=https://api.openai.com/v1`, 시도마다 새 `state`·`nonce`·PKCE(S256).
  - 콜백: `state`를 먼저 견준다(다르면 무시하고 리스너를 둔다). `error=access_denied`면 멈춘다. 처음 등록은 콜백의 발급 `client_id`를 저장한다. 코드를 `https://auth.openai.com/api/accounts/oauth/token`에서 바꾸고, ID 토큰을 OpenAI의 JWKS로 서명 검증(RS256, 표준 라이브러리)한 뒤 `iss`·`aud`·`exp`·`nonce`를 본다.
  - 저장: `ALGOBLOCK_LLM_AUTH_DIR/chatgpt.json`(0600, 임시 파일에 쓴 뒤 바꿔 끼운다)에 계정·발급 `client_id`·토큰·허락된 범위·받은 시각. 허락된 범위에 `chatgpt.tokens.use.direct`가 없으면 로그인은 남기되 연결로 보지 않는다. 예전 방식의 `openai-oauth.json`은 읽지 않는다.
  - 갱신: 만료 2분 전부터 `grant_type=refresh_token`(발급 `client_id`, `resource`). 갱신 토큰을 더 쓸 수 없으면(`invalid_grant` 등) 토큰을 지우고 다시 로그인하라고 알린다.
  - `login_status()`가 `{"connected", "error"}`를 돌려준다. `error`는 연결되지 않은 까닭(사람 말)이고 화면의 연결 창에 보인다.
- 연결 방식별 모델(`tutor/llm/themes.py`): 과정마다 고른 급(작음·가운데·큼)을 Claude 연결은 Haiku·Sonnet·Opus, ChatGPT 구독 로그인과 OpenAI 키는 Luna·Terra·Sol의 최신 이름으로 푼다. 목록을 받지 못하면 `KNOWN`의 이름을 쓴다.
- Claude: 구독(Free·Pro·Max) OAuth는 두지 않는다. Anthropic 정책이 제3자 앱의 claude.ai 로그인과 구독 자격증명 경유를 금지한다([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)). Claude는 API 키로만 쓴다.

## 캐시

메시지에 `cache_prefix`(글자 수)가 있으면 그 메시지의 앞부분(문제 글 같은 고정 앞부분)이 캐시 대상이다. 튜터는 `tutor/llm`의 `cached_user(lines, head)`로 붙인다. `session`이 표시를 떼어 공급자마다 맞게 보낸다.

| 공급자 | 하는 일 |
| --- | --- |
| Claude | 경계에서 글을 두 블록으로 나눠 앞 블록에 `cache_control: ephemeral`을 붙인다. `ALGOBLOCK_LLM_CACHE_TTL=1h`면 1시간, 아니면 기본 5분이다 |
| OpenAI 키·ChatGPT 요금제 | 앞부분 해시를 `prompt_cache_key`로 보낸다. 캐시는 공급자가 자동으로 한다 |

호출마다 사용량이 `usage.RECENT`에 남는다: `task, model, effort, seconds, retry, input(캐시 뺀 새 입력), cache_read, cache_write, output`. `ALGOBLOCK_LLM_USAGE_LOG`가 있으면 그 파일에 한 줄씩 덧붙인다. 키와 프롬프트 글은 적지 않는다.

`ALGOBLOCK_LLM_PROMPT_DIR`이 있으면 보낸 프롬프트와 받은 답을 호출마다 그 폴더에 파일 하나로 남긴다(측정용. 기본은 꺼져 있다). 화면 서버는 이 폴더가 데이터 폴더 안이면 끈다.

## 생각(thinking)

- Claude: 답 길이 목표(`max_tokens`, 기본 16000)가 1024 미만(판정 `[check]` 한 줄 등)이면 생각 몫 2048토큰을 더한다. 추론 정도는 `output_config.effort`로 보낸다. 답 길이 목표가 1024 이상일 때 `stop_reason`이 `max_tokens` 또는 `refusal`이면 `LlmFailed`를 올린다. `temperature` 같은 샘플링 값은 보내지 않는다.
- OpenAI 경로(`openai/api_key`, `openai/oauth`)는 추론 정도를 `reasoning: {effort}`로 보낸다.
- JSON 답의 모양이 깨지면(`schema`가 있을 때) `session`이 같은 요청을 한 번 더 보낸다.

## 재시도와 오류

`wire.py`의 `post_json`이 HTTP JSON 호출을 맡는다(본문이 없으면 GET: 모델 목록). Claude, OpenAI 키 경로와 임베딩이 쓴다. ChatGPT 요금제 경로(`openai/oauth/chat.py`의 `post_sse`)는 다시 보내지 않는다. 오류 코드마다: 사용 한도(`subscription_sharing_usage_limit_exceeded`)는 ChatGPT 설정의 사용량 안내를 `llm_rate_limited`로, 자격 없음·계정 확인 실패(401)는 이 연결을 멈추고 까닭을 연결 창에 남긴다(`llm_not_configured`), 잠깐의 장애(503 등)는 `llm_failed`다. `response.completed` 없이 끝난 스트림도 실패다.

- 상태 408·409·429·500·502·503·504·529이면 최대 2번 다시 보낸다. 제한 시간(`ALGOBLOCK_LLM_TIMEOUT`, 기본 60초) 안에서만 다시 보낸다.
- 기다리는 시간은 `retry-after`가 초 단위 숫자면 그 값, 아니면 1초·2초다. 한 번에 기다리는 시간은 5초가 상한이다.
- 다시 보내도 실패하면 예외를 올린다.
  - 401·403: `LlmNotConfigured`("키를 확인해 주세요(상태 코드).").
  - 그 밖의 상태 코드: `LlmFailed`("공급자 오류(상태 코드)").
  - 연결 실패: `LlmFailed`("공급자에 연결하지 못했습니다.").
  - 시간 제한 초과: `LlmTimeout`("60초를 넘겼습니다.").
- 화면에 가는 오류 코드는 `tutor/common/errors.py`의 `llm_error`가 정한다.

| 경우 | 오류 코드(상태) |
| --- | --- |
| 시간 초과 | `llm_timeout`(504). 글은 "60초를 넘겼습니다."로 고정이다 |
| 공급자 401·403 | `llm_auth_failed`(401) |
| 공급자 429(다시 보내도 실패) | `llm_rate_limited`(429) |
| 키나 모델이 없음 | `llm_not_configured`(503) |
| 그 밖 | `llm_failed`(502) |
