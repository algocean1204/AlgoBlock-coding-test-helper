# 함께 쓰거나 묶어 배포하는 것

이 저장소의 코드와 기본 문제(문제 글, 채점 데이터, 풀이)는 [MIT 라이선스](../LICENSE)를 따른다. 아래는 다른 사람이 만든 것으로, 저마다의 라이선스를 따른다.

## 저장소에 들어 있는 것

| 이름 | 쓰는 곳 | 라이선스 |
| --- | --- | --- |
| Pretendard Variable (글꼴. Kil Hyung-jin, Source의 Adobe, Inter의 The Inter Project Authors, M PLUS 1의 The M+ FONTS Project Authors) | `app/ui/PretendardVariable.woff2` | SIL Open Font License 1.1 — 전문과 저작권 표기는 `app/ui/PretendardVariable-LICENSE.txt` |
| Phosphor Icons (아이콘, bold) | `app/ui/index.html` 안의 기호(`i-*`) | MIT — 전문은 아래 'Phosphor Icons 라이선스' |
| Stageshow 키트 (Benji Taylor) | 처음 안내의 움직이는 데모와 README 그림. 사본은 `app/ui/stageshow/kit/`와 `scripts/`(다른 회사 로고 그림은 뺐다), 빌드한 묶음 `app/ui/tour-demos.js`·`tour-demos.css`에도 들어 있다 | MIT — 전문은 `app/ui/stageshow/LICENSE-stageshow.txt`, 고지는 `NOTICE-stageshow.md` |
| React, React DOM 18.3.1 (scheduler 0.23.2 포함) | `app/ui/tour-demos.js`에 묶여 있다(안내 데모만 쓴다) | MIT |
| lucide-react 0.468.0 (아이콘) | `app/ui/tour-demos.js`에 묶여 있다(안내 데모의 자물쇠·체크 기호) | ISC (일부는 Feather에서 온 MIT) |

안내 데모를 다시 빌드할 때만 쓰는 도구(Vite, TypeScript, @vitejs/plugin-react, playwright-core)는 저장소와 설치 파일에 들어가지 않는다(`app/ui/stageshow/package.json`).

## 설치 파일(.dmg, .exe)에 함께 묶이는 것

저장소에는 없고, 설치 파일을 만들 때 받아서 묶는다(`app/packaging/README.md`).

| 이름 | 쓰는 곳 | 라이선스 |
| --- | --- | --- |
| multilingual-e5-small (임베딩 모델, intfloat). 리비전 `614241f622f53c4eeff9890bdc4f31cfecc418b3`의 `onnx/model_O4.onnx`와 `tokenizer.json`(`app/tutor/knowledge/embed.py`가 받고 크기와 SHA-256을 확인한다) | 비슷한 문제 찾기 | MIT |
| LangGraph | 튜터 엔진의 흐름 | MIT |
| pywebview | 앱 창 | BSD-3-Clause |
| qdrant-client | 기기 안 벡터 색인 | Apache-2.0 |
| onnxruntime | 임베딩 모델 실행 | MIT |
| tokenizers | 임베딩 모델의 토큰 나누기 | Apache-2.0 |
| pypdf | PDF 문제 읽기 | BSD-3-Clause |
| NumPy | onnxruntime이 쓴다 | BSD-3-Clause |
| Python | 앱 자체의 실행 환경(PyInstaller가 묶는다. 채점용 Python은 묶지 않는다) | PSF License |

채점은 사용자 기기에 설치된 언어 도구(Python, Node.js, JDK, g++/clang, Go, Kotlin, Rust)를 부른다. 이미지 문제를 AI 없이 읽을 때는 기기의 `tesseract`를 부른다. 이 도구들은 묶지 않는다.

## 설치 파일에 묶이는 파이썬 패키지

아래 표는 설치 파일을 한 번 만들었을 때 PyInstaller가 실은 패키지와 그 버전이다. 라이선스는 각 패키지 메타데이터(`License-Expression`, 없으면 `License`, 그것도 없으면 `License ::` 분류자, 그것도 없으면 `*.dist-info`의 LICENSE 첫 줄)에서 읽은 글 그대로다. 빌드 스크립트는 패키지 버전을 고정하지 않으므로 다시 빌드하면 버전이 달라질 수 있다. 빌드에 쓰지만 묶이지 않는 것: altgraph, filelock, flatbuffers, fsspec, hf-xet, huggingface-hub, macholib, pyinstaller, pyinstaller-hooks-contrib, pyobjc-framework-Quartz, pyobjc-framework-Security.

| 이름 | 버전(macOS / Windows) | 라이선스 |
| --- | --- | --- |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.16.0 | MIT |
| bottle | 0.13.4 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| cffi | — / 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.1 | BSD-3-Clause |
| clr_loader | — / 0.3.1 | MIT License(LICENSE 파일) |
| colorama | — / 0.4.6 | BSD License |
| distro | 1.9.0 | Apache License, Version 2.0 |
| grpcio | 1.85.1 | Apache-2.0 |
| h11 | 0.16.0 | MIT |
| h2 | 4.4.1 | MIT |
| hpack | 4.2.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httpcore2 | 2.16.0 | BSD-3-Clause |
| httpx | 0.28.1 | BSD-3-Clause |
| httpx2 | 2.16.0 | BSD-3-Clause |
| hyperframe | 6.1.0 | MIT License |
| idna | 3.20 | BSD-3-Clause |
| jsonpatch | 1.45 / 1.47 | BSD-3-Clause |
| jsonpointer | 3.10 / 3.12 | Modified BSD License / BSD-3-Clause |
| langchain-core | 1.7.6 / 1.8.0 | MIT |
| langchain-protocol | 0.0.21 | MIT |
| langgraph | 1.2.20 | MIT |
| langgraph-checkpoint | 4.3.1 | MIT |
| langgraph-prebuilt | 1.1.1 | MIT |
| langgraph-sdk | 0.4.14 | MIT |
| langsmith | 0.14.17 | MIT |
| numpy | 2.5.4 / 1.26.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 / BSD License |
| onnxruntime | 1.31.1 | MIT License |
| orjson | 3.13.0 | MPL-2.0 AND (Apache-2.0 OR MIT) |
| ormsgpack | 1.13.1 | Apache-2.0 OR MIT |
| packaging | 26.3 / 24.1 | Apache-2.0 OR BSD-2-Clause / Apache Software License, BSD License |
| portalocker | 4.4.2 | BSD-3-Clause |
| protobuf | 7.36.2 | 3-Clause BSD License |
| proxy_tools | 0.1.0 | MIT |
| pycparser | — / 3.12 | BSD-3-Clause |
| pydantic | 2.14.3 | MIT |
| pydantic_core | 2.50.4 | MIT |
| pyobjc-core | 13.0 / — | MIT |
| pyobjc-framework-Cocoa | 13.0 / — | MIT |
| pyobjc-framework-UniformTypeIdentifiers | 13.0 / — | MIT |
| pyobjc-framework-WebKit | 13.0 / — | MIT |
| pypdf | 7.0.0 / 7.0.1 | BSD-3-Clause |
| pythonnet | — / 3.2.1 | MIT |
| pywebview | 6.2.1 | BSD License |
| PyYAML | 6.0.3 | MIT |
| qdrant-client | 1.20.0 | Apache-2.0 |
| requests | 2.34.2 | Apache-2.0 |
| requests-toolbelt | 1.0.0 | Apache 2.0 |
| setuptools | 84.2.1 / 75.1.0 | MIT / MIT License |
| sniffio | 1.3.1 | MIT OR Apache-2.0 |
| tenacity | 9.2.1 | Apache-2.0 |
| tokenizers | 0.23.3 | Apache Software License |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| truststore | 0.10.5 | MIT |
| typing-inspection | 0.4.5 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
| uuid_utils | 0.19.0 | BSD-3-Clause |
| websockets | 17.4 | BSD-3-Clause |
| xxhash | 4.1.0 | BSD-2-Clause |
| zstandard | 0.25.0 | BSD-3-Clause |
| PyInstaller(실행 파일의 부트로더와 시작 코드) | 6.22.3 / 6.10.0 | GPLv2-or-later with a special exception which allows to use PyInstaller to build and distribute non-free programs |

버전이 하나만 적힌 것은 두 설치 파일에서 같다. `—`는 그 OS의 설치 파일에 없다는 뜻이다. Windows exe에는 파이썬과 함께 Microsoft Visual C++ 런타임(`vcruntime140.dll`, `vcruntime140_1.dll`)도 들어 있다.

## 측정 도구에만 쓰는 것

설치 파일에 묶이지 않는다. 측정 도구(`app/tutor/eval/`)를 돌릴 때만 선택으로 쓴다.

| 이름 | 쓰는 곳 | 라이선스 |
| --- | --- | --- |
| fastembed | `app/tutor/eval/recall_bench.py`, `recall_hard.py`가 선택으로 import한다 | Apache-2.0 |

## 기본 문제

기본 문제는 널리 알려진 알고리즘 유형을 참고해 이 프로젝트에서 새로 썼다(이야기, 문장, 숫자, 예시). 다른 곳의 문제 글이나 예시를 옮기지 않았다. 옮긴 것으로 보이는 문제를 찾으면 이슈로 알려 주기 바란다.

## Phosphor Icons 라이선스

```text
MIT License

Copyright (c) 2023 Phosphor Icons

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
