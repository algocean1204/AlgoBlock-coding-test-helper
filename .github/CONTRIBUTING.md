# 기여 안내

버그 신고, 기본 문제 오류 신고, 기능 제안, 코드와 문서 수정을 받는다. 보안 문제는 이슈로 올리지 말고 [SECURITY.md](SECURITY.md)를 따른다.

모든 참여자는 [행동 강령](CODE_OF_CONDUCT.md)을 따른다.

## 어떤 기여를 어디로

| 하려는 것 | 갈 곳 |
| --- | --- |
| 버그, 기본 문제 오류, 기능 제안 | 이슈(양식을 고른다) |
| 쓰는 법이나 설정에 관한 질문 | Discussions의 Q&A |
| 코드 수정 | 먼저 이슈로 방향을 맞춘 뒤 PR. 오타와 문서 한 줄 수정은 이슈 없이 PR |
| 보안 문제 | 비공개 취약점 신고([SECURITY.md](SECURITY.md)) |

한국어가 기본이고 영어도 받는다.

## 시작하기

- 개발 환경과 실행: [Docs/contributing/dev-setup.md](../Docs/contributing/dev-setup.md)
- 시험과 무엇을 고칠 때 무엇을 돌리나: [Docs/contributing/testing.md](../Docs/contributing/testing.md)
- 기본 문제를 더하거나 고치기: [Docs/contributing/add-builtin-problem.md](../Docs/contributing/add-builtin-problem.md)
- 채점 언어 더하기: [Docs/contributing/add-language.md](../Docs/contributing/add-language.md)
- 구조: [Docs/architecture/overview.md](../Docs/architecture/overview.md)

## PR 흐름

유지자도 이 흐름을 그대로 따른다. 변경은 **작업 브랜치 → `develop` → `main` → 릴리스** 순서로 간다. 기본 브랜치는 `develop`이고 PR의 대상도 `develop`이다. `develop`과 `main`은 PR로만 바뀐다. 보호 규칙의 원본은 `.github/rulesets/develop.json`·`main.json`(브랜치)과 `.github/rulesets/tags.json`(릴리스 태그)이다. GitHub 룰셋 형식이다.

1. 이슈를 먼저 연다(오타나 문서 한 줄은 이슈 없이 PR만).
2. `develop`에서 브랜치를 만든다. 이름은 `<접두사>/<이슈 번호>-<짧은 이름>`이다(예: `fix/12-empty-code-message`). 접두사는 `feature/`(새 기능), `fix/`(고침), `refactor/`(동작이 같은 정리), `chore/`(빌드·설정), `docs/`(문서), `problem/`(기본 문제) 가운데 하나, 짧은 이름은 소문자·숫자·하이픈. 이슈가 없는 PR은 번호를 뺀다. 이 저장소 안에서 올린 PR은 CI가 이름을 검사한다. 합친 브랜치는 지운다.
3. 작게, 한 가지 주제만 바꾼다. 있는 코드를 재사용하고 표준 라이브러리를 먼저 쓴다. 새 의존성은 꼭 필요할 때만 넣는다.
4. [PR 양식](PULL_REQUEST_TEMPLATE.md)의 모든 칸을 채운다.
5. CI의 `ci-passed`가 통과해야 합친다. 이 작업은 엔진·화면 서버·채점기 시험, 공개 전 검사, 비밀 검사, 브랜치 이름 검사가 모두 통과했는지 모은다. 제목 검사 `pr-title`은 따로 필수다. 검토에서 달린 글타래는 모두 해결돼야 한다.
6. `develop`에 스쿼시로 합친다. PR 제목이 `develop`의 커밋 제목이 된다. 제목은 아래 [커밋과 PR 제목](#커밋과-pr-제목) 꼴로 쓴다. CI의 `pr-title`이 제목을 검사하고, 제목을 고치면 다시 돈다. 유지자는 합칠 때 제목을 고칠 수 있다.
7. 유지자는 변경을 요청하는 대신 PR 위에 커밋을 더해 마무리할 수 있다. 다른 방법이 낫다고 보면 새 PR로 다시 하고, 원래 PR을 그 PR에 적어 공로를 남긴다.

## develop, main, 릴리스

- `develop`: 합친 변경이 모이는 곳. 작업 브랜치에서 온 PR을 스쿼시로 받는다.
- `main`: 릴리스한 상태. `develop`에서 온 PR만 받고(CI의 `main-source`가 본다), `develop`과 기록이 갈라지지 않게 merge commit으로 합친다. 유지자가 한다.
- 릴리스: `main`의 커밋에 `v<버전>` 태그를 단다. 태그는 릴리스를 만들 때 생긴다.
- 버전은 1.0.0 전까지 `0.x.y`다. 큰 업데이트(새 기능, 화면이나 저장 자료의 꼴이 바뀜)는 둘째 숫자를, 작은 고침은 셋째 숫자를 올린다. 버전의 원본은 `app/ui/updater.py`의 `VERSION` 한 곳이고, `develop` → `main` PR에서 올린다. CI가 `0.x.y` 꼴인지와 마지막 릴리스보다 큰지 본다.

## 커밋과 PR 제목

[Conventional Commits 1.0.0](https://www.conventionalcommits.org/ko/v1.0.0/)을 따른다. 꼴은 `<종류>(<범위>)!: <설명>`이고 범위와 `!`는 빼도 된다.

| 종류 | 쓸 때 |
|---|---|
| `feat` | 새 기능, 기본 문제 더하기 |
| `fix` | 버그 고침 |
| `docs` | 문서만 |
| `refactor` | 동작이 같은 정리 |
| `perf` | 빠르게 하기 |
| `test` | 시험만 |
| `build` | 설치 파일 만들기(`app/packaging`) |
| `ci` | `.github/workflows`, Dependabot |
| `chore` | 그 밖의 설정·관리 |
| `style` | 줄 바꿈·공백 같은 꼴만 |
| `revert` | 되돌리기 |

- 범위는 소문자·숫자·하이픈이다. 자주 쓰는 것: `ui`, `tutor`, `judge`, `llm`, `packaging`, `update`, `problems`.
- 저장된 자료나 설정을 예전 버전이 못 읽게 되는 것처럼 깨지는 변경이면 콜론 앞에 `!`를 붙이고 본문에 `BREAKING CHANGE:`로 까닭을 적는다.
- 설명은 한국어나 영어로, 한 줄에 무엇이 바뀌는지 쓴다.
- 브랜치 접두사와 종류는 대개 이렇게 맞는다: `feature/` → `feat`, `fix/` → `fix`, `refactor/` → `refactor`, `chore/` → `chore`·`ci`·`build`, `docs/` → `docs`, `problem/` → `feat(problems)`·`fix(problems)`.
- 예: `fix(judge): 빈 입력에서 시간 초과로 보이던 것을 고침`, `feat(problems): 구간 합 문제 더하기`, `ci: actions/checkout 갱신`.

- 되돌리기는 GitHub의 Revert 단추가 만드는 이름(`revert-…` 브랜치, `Revert "…"` 제목)이 검사에 걸린다. `fix/<번호>-revert-<짧은 이름>` 브랜치에 `revert: <원래 제목>`으로 올린다.

브랜치 안의 커밋은 스쿼시로 하나가 되므로 꼴을 따로 검사하지 않는다. 그래도 같은 꼴로 쓰면 검토하기 쉽다.

바깥 기여자의 PR에서는 유지자가 승인한 뒤에 CI가 돈다. 제목만 고쳐도 다시 승인을 기다리니 제목은 처음부터 꼴에 맞게 쓴다.

## 폴더 구조는 고정이다

저장소 루트의 항목은 `README.md`, `LICENSE`, `.gitignore`, `.env.example`, `.github`, `app`, `Docs`뿐이다. `app/`과 `Docs/`의 바로 아래 항목도 정해져 있다. `app/ui/test_structure.py`가 이것을 검사하므로 새 최상위 폴더나 파일이 필요하면 먼저 이슈로 이야기한다.

공개 전 검사(`app/ui/test_publish.py`)는 키 모양의 글자, 개인 경로와 이메일, 50MB가 넘는 파일을 막는다. 걸리면 그 내용을 지우고 다시 올린다.

## AI 에이전트로 기여할 때

이 저장소는 에이전트 지시 파일을 두지 않는다(`.gitignore`가 뺀다). 에이전트를 쓴다면 이 절을 지시로 준다.

- 위의 PR 흐름과 [시험 방침](../Docs/contributing/testing.md)을 따른다. 시험을 돌린 결과를 PR의 '확인한 것'에 적는다.
- 가장 작은 변경을 한다. 쓰지 않는 추상화, 앞날을 위한 설정, 요청하지 않은 정리를 더하지 않는다.
- 화면은 라이브러리 없이 HTML, CSS, JS로 고친다(처음 안내의 데모 묶음만 예외, [stageshow](../app/ui/stageshow/README.md)).
- API 키, 토큰, 개인 경로를 코드, 로그, 시험, PR 글에 넣지 않는다. 시험은 모델을 부르지 않는다.
- `app/ui/builtin.json`을 손으로 고치지 않는다. 문제 폴더를 고치고 묶는다.
- 다른 곳의 문제 글, 예시, 숫자를 옮기지 않는다.
- PR 양식의 'AI 사용'에 쓴 도구·모델과 사람이 확인한 범위를 적는다.

## 라벨

| 묶음 | 라벨 |
| --- | --- |
| 종류 | `bug`, `problem`(기본 문제의 글·채점·해설 오류), `enhancement`, `documentation`, `question` |
| 영역 | `area:engine`, `area:ui`, `area:judge`, `area:llm`, `area:packaging` |
| 운영체제 | `os:macos`, `os:windows`, `os:linux` |
| 분류 상태 | `needs-triage`(양식이 붙인다), `needs-repro`, `waiting-for-reporter` |
| 입문 | `good first issue`, `help wanted` |
| 결론 | `duplicate`, `invalid`, `wontfix` |

## 라이선스와 릴리스

- 들어온 기여는 저장소와 같은 [MIT 라이선스](../LICENSE)를 따른다. 따로 서명할 문서(CLA)는 없다.
- 버전과 릴리스는 유지자가 정한다. 설치 파일은 저장소에 넣지 않고 GitHub Releases에 올린다.
