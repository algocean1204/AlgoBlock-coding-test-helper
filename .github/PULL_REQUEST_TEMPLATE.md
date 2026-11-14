<!-- 모든 칸을 채운다. 해당이 없으면 N/A와 그 까닭을 적는다. 바깥 기여자는 관련 이슈가 있어야 한다(오타·문서 한 줄은 예외). -->

## 쉬운 설명
<!-- 두세 문장. 전문용어 없이, 이 PR이 무엇을 바꾸는지 -->

## 무엇을 바꿨나
<!-- 사용자가 겪는 전과 후, 그리고 바꾼 곳(파일·함수) -->

## 왜 이 방법인가
<!-- 고려했다가 버린 다른 방법과 그 까닭 -->

## 관련 이슈
<!-- 예: Closes #12 -->

## 화면 증거
<!-- 화면이나 동작이 바뀌면 전·후 그림이나 영상을 이 PR에 붙인다(저장소 파일로 넣지 않는다). 아니면 N/A와 까닭 -->

## 확인한 것
<!-- 명령의 자세한 뜻: Docs/contributing/testing.md -->
- [ ] 엔진 시험: `cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B -m unittest discover -s tutor/tests -t .`
- [ ] 화면 서버 시험: `cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B ui/test_server.py`
- [ ] 구조와 공개 전 검사: `cd app && python3 -B ui/test_structure.py && python3 -B ui/test_publish.py`
- [ ] 채점기 시험(채점기를 고쳤을 때): `cd app/judge && python3 -B -m unittest test_check`
- [ ] 기본 문제 검사(문제를 더하거나 고쳤을 때): `cd app && python3 ui/problemkit.py check ui/problems/<주제>/<문제 폴더> --langs`
- [ ] 화면을 바꿨으면 밝은·어두운 모드에서 직접 눌러 봤다
- [ ] 더한 시험은 바꾼 것을 되돌리면 실패한다

## 어디서 돌려 봤나
- [ ] macOS
- [ ] Windows
- [ ] Linux

## 위험과 되돌리는 법
<!-- 무엇이 누구에게 깨질 수 있나. 데이터 폴더(SQLite, keys.json)나 app/ui/builtin.json 같은 저장물에 닿는가. 되돌리는 법 -->
- 수준: 낮음 / 중간 / 높음

## AI 사용
<!-- 썼다면 어떤 도구·모델을 썼고, 사람이 직접 확인한 범위는 어디까지인가. 쓰지 않았으면 "없음" -->

## 체크리스트
- [ ] 작고 한 가지 주제다
- [ ] 키·토큰·개인 경로를 넣지 않았다
- [ ] 다른 곳의 문제 글·예시를 옮기지 않았다
