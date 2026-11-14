# tutor — 튜터 엔진

LangGraph로 만든 튜터 엔진이다. 에이전트 하나가 폴더 하나다. 에이전트와 그래프, 블록 코드 확인이 지키는 것, 대화 원칙은 [Docs/architecture/tutor.md](../../Docs/architecture/tutor.md)에 있다. 이 문서는 코드에서 엔진을 부르는 법과 모듈·시험 지도다.

모델은 `app/llm`(`app.llm`)을 쓴다(`llm/client.py`). 필요한 패키지는 `langgraph`, PDF를 읽을 때만 `pypdf`다.

## 쓰기

```python
from tutor import Tutor, extract          # app/에서

body = extract("붙여 넣은 글", [("문제.png", png_bytes)])    # A1 문항 읽기
tutor = Tutor("tutor.db", check=verify, given=given)           # 기기 안 SQLite 파일 하나. check는 풀이 가이드의 정답 코드를 채점한다(없어도 된다). given(problem_id, language)은 정답 코드가 정해진 문제(기본 문제)의 풀이 가이드를 돌려준다(없어도 된다)
tutor.store.put_problem("p1", "python", body)
tutor.turn("p1", "chair", "start")                             # Outcome(status, body)
tutor.turn("p1", "chair", "message", text="이름을 세면 돼요")
tutor.turn("p1", "chair", "next")                              # 채우기로 열린 블록의 첫 질문(모델 0회)
tutor.followup("p1", "chair", quote_id="3", text="왜요?")
tutor.fill("p1", "b2", filled=[{"id": "b1", "code": "..."}])
tutor.explain("p1"); tutor.feedback("p1")                      # 해설, 피드백
tutor.session("p1")                                            # 세션 상태(모드 생략 가능)
tutor.debug("p1", code, report)                                # 틀린 코드와 채점 결과에서 틀린 곳 찾기(A13). text="…"로 사용자 말을 함께 줄 수 있다
tutor.prepare("p1")                                            # 문항 등록 직후 뼈대를 미리 뽑는다(첫 질문이 빨라진다)
tutor.adopt("p1", ready)                                       # 미리 만든 뼈대·풀이 가이드·블록 계획을 저장한다(기본 문제). 계획이 있으면 아무것도 안 한다
# 벡터 색인을 붙이려면: Tutor("tutor.db", index=open_index("vectors", model_dir="모델 폴더"))  (모델 폴더를 안 주면 ALGOBLOCK_EMBED_DIR. 패키지나 모델 파일이 없으면 색인은 None)
```

오류는 `Outcome(상태 코드, {"detail": {"code", "message"}})`다. 상태 코드 표는 `common/errors.py`의 `STATUS`.

응답의 `blocks`는 열린 블록만 이름이 있고 잠긴 블록은 `name: null`이다(해설 응답은 모두). 화면은 채우기 응답의 `open_count`가 늘었으면 `turn(..., "next")`를 불러 새 블록의 첫 질문을 받는다.

## 공통 모듈

| 파일 | 하는 일 | 쓰는 곳 |
| --- | --- | --- |
| `state.py` | 그래프가 주고받는 데이터 | 전부 |
| `llm/` | 모델 입구, 가짜 모델, 모양 맞추기 | 모델을 부르는 노드 |
| `store/` | SQLite 표(`schema.py`, 표 12개. 버전은 `MIGRATIONS`의 길이), 계획 JSON(`codec.py`), `Store` | A2, A12, `Tutor`의 일부 메서드, 화면 서버 |
| `common/scope.py` | 풀이 범위 15종, 설계 원칙 | A4, A5, A6–A10 |
| `llm/themes.py` | 과정 여덟(문제 읽기, 풀이 가이드, 블록 설계와 힌트, 대화, 판정, 해설, 피드백, 디버그 진단)마다 급과 추론 정도, 시리즈마다 최신 모델 이름 | 모델을 부르는 모든 노드(입구에서 고름) |
| `common/solution.py` | 풀이 가이드를 프롬프트 앞부분에 싣는다(`solution_of`, `solution_lines`) | 대화·판정·코드 확인·꼬리질문·채우기·해설·피드백 |
| `knowledge/ontology.py` | 기법 30, 패턴 31, 함정 32, 구현 기술 20, 입력 크기 규칙 | A4, A8, A10, A13 |
| `knowledge/index.py` | 벡터 색인(Qdrant 로컬), 열기(`open_index`), 임베딩 이름표 | A4 |
| `knowledge/embed.py` | 기기 안 임베딩 multilingual-e5-small: 파일 받기(`fetch`), 임베딩(`e5_embedder`). fastembed를 쓰지 않는다 | A4 |
| `common/verdict.py` | `[check]` 판정(근거 글자 t·e·g 포함), 16토큰 | A4, A6, A7, A10 |
| `common/assess.py` | 채점 기준표, 전략(50점 경계) | A4, A10 |
| `common/talk_rules.py` | 대화 원칙: 금지 표현, 인용 확인, 말풍선 검사, 대체 질문 | A4, A6–A8, A10 |
| `common/talk_prompts.py` | 대화 시스템 프롬프트, 판정 프롬프트 틀 | A6–A8 |
| `turn/` | 의자·가이드 공통 그래프, 질문 유형 표(`moves.py`), 블록 코드 판정 | A6, A7 |

## 시험

시험은 모델을 부르지 않는다(`test_live.py`만 `ALGOBLOCK_LIVE=1`일 때 실제 모델을 한 번 부른다). `qdrant-client`, 임베딩 모델 파일, `onnxruntime`·`tokenizers`가 없으면 그 시험은 건너뛴다. 돌리는 법은 [Docs/contributing/testing.md](../../Docs/contributing/testing.md).

| 파일 | 본다 |
| --- | --- |
| `test_backend_llm.py` | 모델 연결 공급자(`app.llm`)가 서버 안에서 그대로 도는지 |
| `test_rules.py` | 전략, 블록 검사, 힌트 다듬기, 해설 절, 펜스, 열린 블록 수, 판정 읽기, 대화 원칙, 피드백 검사, 요청 거절(모델 0회) |
| `test_moves.py` | 질문 유형 표 전부 |
| `test_pipeline.py` | 그래프 흐름(가짜 모델): 계획, 의자·가이드 턴, 대체 질문, 꼬리질문, 채우기, 피드백, 실패 |
| `test_tutor.py` | SQLite까지: 저장·질문 유형 기록, 재사용(모델 0회), 오류 시 저장 없음, 저장소 실패, 옛 DB 이전, 예전 문제가 가이드·블록 설계 프롬프트에 없음, 원칙을 어긴 블록 질문은 그 블록만 한 번 다시 받음(다시 받기 실패해도 계획을 만듦) |
| `test_ingest.py` | 글 잇기, PDF, OCR 판정, 장 실패 |
| `test_llm.py` | 모양 맞추기, 가짜 모델, backend 공급자 연결(기본 모델, 글 모드) |
| `test_design.py` | 폴더마다 단계 수와 노드 이름, 메인 순서, SQLite 경계, 상대 import |
| `test_live.py` | 실모델 한 건(`ALGOBLOCK_LIVE=1`) |
| `test_eval.py` | 평가기(규칙 검사, 근거 검증·다수결, 보정), 캐시 경계 표시 |
| `test_chatgpt_plan.py` | ChatGPT 요금제 로그인(인가 주소, 콜백, ID 토큰 서명 검증, 저장, 갱신)과 Responses 요청·스트림 |
| `test_knowledge.py` | 온톨로지(범위 15종): 단서, 엣지, 구현 기술 예가 실제 파이썬인지, 질문 씨앗에 기법 낱말이 없는지, 입력 크기 규칙 |
| `test_index.py` | 벡터 색인: 점수, 다시 채우기, 임베딩 이름표(다른 이름이나 이름표 없음이면 비움), 모델이 없을 때 None, 실제 모델의 벡터 성질 |

측정 도구(모델을 부른다): [eval](eval/README.md).
