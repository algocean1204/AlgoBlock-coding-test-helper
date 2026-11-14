# 평가 세트와 평가기

튜터의 모델·과정 설정과 프롬프트를 바꿀 때 쓰는 측정 도구다. 앱 실행에는 필요 없다. 설치 파일에는 화면이 쓰는 `cli_client.py`, `drive.py`, `scenarios.py`만 들어간다.

- 대부분의 도구는 실제 모델을 부른다. 공급자 키(`ANTHROPIC_API_KEY` 등)가 있거나, `--cli`를 주고 이 PC에 설치·로그인된 Claude Code(`claude -p`)가 있어야 한다. 돈이 들 수 있다.
- 모델을 부르지 않는 것: `checks.py`(규칙 검사), `compare.py`, `cost.py`, `recall_hard run`, 뼈대 캐시가 있을 때의 `recall_bench`.
- 결과 파일은 `tutor/eval/results/`에 쓴다. 이 폴더는 git에 올리지 않는다(`.gitignore`).

`--cli`는 API 키 없이 Claude Code로 튜터·초보자·평가기를 돌린다(`cli_client.py`). 개발자의 평가 전용이다. 앱의 모델 연결이 아니다. 빼면 지금 연결한 공급자(`ALGOBLOCK_LLM_MODEL`, `ALGOBLOCK_THEME_<과정>`으로 바꾼다)로 돈다.

## 결정적 측정 (bench.py, debug_bench.py, recall_bench.py)

정답이 정해진 작은 세트를 실제 노드 프롬프트로 돌린다. 모델 평가기를 거치지 않는다.

```bash
cd app
python3 -m tutor.eval.bench judge --cli    # 판정 노드(chair.judge): 정답을 붙인 사용자 말을 맞게 나누는가
python3 -m tutor.eval.bench plan --cli     # 계획과 해설: 해설의 전체 코드가 채점기를 통과하는가
python3 -m tutor.eval.bench locate --cli   # 디버그 진단(debug_bench.py): 원인 줄을 맞추고, 고친 줄을 넣으면 채점기를 통과하는가
python3 -m tutor.eval.recall_bench --cli   # 비슷한 문항 찾기: 임베딩 모델별 P@1(1위가 같은 구조인 비율)
```

- `bench`는 `--repeat N`으로 같은 세트를 여러 번 돈다.
- `locate`는 온톨로지 함정 후보를 준 것과 안 준 것을 같이 잰다(`ALGOBLOCK_BENCH_NO_ONTOLOGY=1`이면 후보 없이).
- `ALGOBLOCK_BENCH_NO_GUIDE=1`을 주면 블록 설계가 풀이 가이드 없이 돈다(`plan/nodes.py`). 견주기용이다.
- 과정별 모델은 `ALGOBLOCK_THEME_<과정>=모델:정도`로 바꾼다(예: `ALGOBLOCK_THEME_JUDGE=claude/claude-sonnet-5-5:low`). 과정 이름은 `tutor/llm/themes.py`에 있다.
- `recall_bench`는 함정 문항 20개(구조 8 × 이야기 6)의 뼈대를 모델로 한 번 뽑아 `results/recall-specs.json`에 두고 다시 쓴다(`--cli`면 Claude Code, 빼면 연결한 공급자). `--model`은 fastembed 임베딩 모델 이름이고 여러 번 줄 수 있다. 빼면 표의 모델 전부다. `char-3gram`은 모델 없는 기준선이다. qdrant-client가 있어야 하고, fastembed 모델을 재려면 fastembed도 있어야 한다.

## 문제 넣기 모델 비교 (ingest_bench.py)

문제 넣기 과정의 모델을 바꾸기 전에 쓴다. 문제 파일(`[{id, theme, title, text, cases}]`, `ui/builtin.json`이 이 꼴이다)의 문제마다 새 저장소에서 미리 만들기(`Tutor.prepare`)를 그대로 돌리고, 채점 콜백으로 풀이 가이드를 확인한다. 모델을 부른다. 결과는 `results/ingest-<시각>-<모델>.json`이다.

```bash
cd app
python3 -m tutor.eval.ingest_bench ui/builtin.json --per-theme 1 --model claude/claude-opus-5-5:high
```

- 옵션: `--model`(문제 넣기 과정의 모델:추론 정도. 비우면 지금 설정), `--per-theme N`(주제마다 앞에서 N문제, 0은 전부), `--runs K`(기본 1), `--workers`(기본 4).
- 재는 것: 계획이 만들어졌나, 가이드 채점을 통과했나, 첫 시도에 통과했나, 풀이 가이드·블록·힌트 호출 수, 블록 수, 힌트가 빈 블록 수, 블록을 이으면 가이드 코드가 되는가, 시간, 토큰. 질문과 블록 이름의 말씨 품질은 재지 않는다.

## 어려운 측정 (recall_hard.py)

`recall_bench`의 함정 문항 20개에서 질의만 바꿔 잰다. 색인에는 원래 명세가 있고, 질의만 말씨와 틀이 달라진다.

먼저 `results/recall-specs.json`이 있어야 한다. 없으면 `python3 -m tutor.eval.recall_bench --cli`를 한 번 돌려 만든다.

```bash
cd app
python3 -m tutor.eval.recall_hard variants                          # 바꿔 쓴 명세를 만든다(모델을 부른다. 한 번만. results/recall-hard.json에 캐시)
python3 -m tutor.eval.recall_hard run --model char-3gram            # 글자 3-gram(모델 없음. 기준선)
python3 -m tutor.eval.recall_hard run --model app                   # 앱이 실제로 쓰는 길: ALGOBLOCK_EMBED_DIR의 model.onnx와 tokenizer.json(onnxruntime 직접)
python3 -m tutor.eval.recall_hard run --model intfloat/multilingual-e5-small   # fastembed 모델 이름
```

- `variants`만 모델을 부른다(연결한 공급자. `other` 조건의 다른 공급자 모델은 `ALGOBLOCK_HARD_OTHER`, 기본 `openai/gpt-6-luna`). `run`은 임베딩만 한다.
- `--model app`은 앱과 같은 실행기를 쓴다. `ALGOBLOCK_EMBED_DIR`에 파일이 있어야 한다.
- fastembed 이름으로 재려면 fastembed가 있어야 한다. 글자 3-gram과 `--model app`은 없어도 된다. fastembed 목록에 없는 e5-small은 ONNX 파일을 직접 등록한다(`ALGOBLOCK_HARD_E5_FILE`, 기본 `onnx/model.onnx`). 모델 캐시 위치는 `FASTEMBED_CACHE_PATH`다. 이 변수는 측정 도구에서만 쓴다.
- 결과는 표준 출력에 나온다. 파일로 남기지 않는다.
- 조건 일곱 개: `same`(원래 명세, 쉬운 기준), `para`(다른 낱말과 문장 순서), `terse`(명사형 한 줄), `other`(다른 공급자가 뽑은 명세), `english`(영어 명세), `leak`(이야기 낱말이 남은 명세끼리), `pool57`(바꿔 쓴 질의로 후보 57개에서 찾기).
- 점수는 두 가지다. 코사인만과 코사인 + 0.3 × 패턴 겹침(지금 색인의 점수식). 지표는 P@1이다.

## 평가기 (qa.py)

| 층 | 파일 | 보는 것 | 신뢰 근거 |
| --- | --- | --- | --- |
| 규칙 | `checks.py` | 펜스, 금지 표현, 3문장, 물음표, 참고 코드·뒤 블록 이름 유출, 지어낸 인용, 대체 질문, 같은 말 반복, 진행·막힘, 오류, 시간, 캐시 적중 | 모델 없음. 같은 입력이면 같은 결과. `tests/test_eval.py` |
| 모델 평가기 | `judge.py` | leak(뜻으로 새는 답), responsive(사용자 말을 받는가), novice_fit(초보자 눈높이), grounded(문제와 맞는 사실), verdict(내부 판정이 맞는가) | 아래 다섯 장치 |

평가기 task(`eval.judge`)는 '블록 설계와 힌트' 과정의 모델로 돈다(`tutor/llm/themes.py`의 `TASKS`). 튜터의 판정보다 센 모델이어야 평가를 믿을 수 있기 때문이다.

모델 평가기의 신뢰 장치:

1. 기준마다 pass·fail·na 이진 판정. 정의와 경계 예시를 프롬프트에 둔다.
2. fail은 근거 인용 필수. 인용이 튜터 말(판정은 사용자 말)에 글자 그대로 없으면 그 표는 무효다.
3. 같은 입력을 k번(기본 3) 따로 묻고 다수결. 과반이 없으면 uncertain.
4. 보정(`calibrate.py`): 정답이 구성으로 정해지는 사례(`golden.py`)에서 기준마다 정확도 0.85·카파 0.6 이상, 불확실 15% 이하, 6건 이상이어야 그 기준을 믿는다. 보지 않은 보류 세트(`HOLDOUT`)에서도 정확도 0.85 이상이어야 한다. 믿지 않는 기준은 보고서에 '참고'로만 나온다.
5. 평가기는 개선 전·후 어느 판인지 모른다(기록에 판 정보가 없다).

한계: 보정 세트와 보류 세트는 기준마다 몇 건에서 스무 건 남짓이라 통계적으로 작다. 평가기와 튜터가 같은 회사 모델이면 자기 선호가 섞일 수 있다. 사람이 본 판정은 `golden.HUMAN`에 더한다.

## 시나리오 (scenarios.py, drive.py)

기본 시나리오는 이 프로젝트에서 새로 쓴 글이다(`hash_library`, `stack_brackets`, `brute_pairs`와 그 변형). 다른 사이트의 문제는 저장소에 넣지 않는다. 쓰려면 `ALGOBLOCK_EVAL_EXTRA` 폴더에 JSON으로 두고 읽는다(`scenarios.load_extra`). 채점 케이스와 초보자 성격(아는 것, 틀린 생각 하나, 습관)은 시나리오마다 있다. 초보자는 모델이 연기한다.

세션(`drive.py`의 `Session`)은 튜터를 만들 때 채점 콜백(`check`)을 넘긴다. 풀이 가이드의 정답 코드가 이 시나리오의 케이스로 채점된다. 흐름: 시작 → 블록마다 대화 → 같은 블록에서 3번 막히면 꼬리질문, 5번이면 이 블록 채우기 → 끝까지 열리면 초보자가 전체 코드를 쓴다 → 채점기 제출 → 피드백 → 해설.

## 돌리기

```bash
cd app
python3 -m tutor.eval.qa calibrate --cli          # 평가기 보정. 결과 results/calibration-*.json
python3 -m tutor.eval.qa run --cli --modes chair  # 시나리오. results/qa-*.md(보고서), qa-*.jsonl(기록), qa-*-summary.json
python3 -m tutor.eval.qa run --cli --modes chair,bugs  # 의자 시나리오와 디버그 세션(debug_bench.BUGS)을 함께
python3 -m tutor.eval.compare results/qa-A.jsonl results/qa-B.jsonl   # 두 기록을 같은 규칙 검사로 다시 세어 나란히(모델 없음)
python3 tutor/eval/cost.py ui/data/usage.jsonl    # 모델 호출 기록을 과정별로 묶어 호출 수, 토큰, 캐시 적중률(모델 없음)
```

- 옵션: `--k`(평가기 반복, 기본 3), `--scenarios`(쉼표로 고른 시나리오), `--modes`(기본 `chair`).
- 평가기 모델은 `ALGOBLOCK_EVAL_JUDGE_MODEL`(공급자) 또는 `ALGOBLOCK_EVAL_JUDGE_CLI_MODEL`(`--cli`, 기본 `sonnet`)로 바꾼다.

## 블록 설계 평가 (run.py)

블록 설계만 실모델로 돌려 유형 분류를 본다. API 키가 필요하다.

`tutor/eval/problems/`에 문제 글을 마크다운으로 넣는다. 저장소에는 문제 글이 없다. 파일 이름이 정답 유형이다(예: `hash.md`, `stack_queue.md`, `heap.md`, `sort.md`, `brute_force.md`, `greedy.md`, `dp.md`, `dfs_bfs.md`, `binary_search.md`, `graph.md`). `out_of_scope.md`는 범위 밖으로 판정돼야 맞다.

```bash
cd app
ANTHROPIC_API_KEY=... python3 -m tutor.eval.run
```

결과는 `results/<날짜>.jsonl`에 한 문제 한 줄로 덧붙는다.
