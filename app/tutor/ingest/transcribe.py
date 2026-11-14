"""장 옮겨 적기(transcribe). 그 장 이미지 하나만 이미지 모델에 넘긴다."""

import re

from ..llm import LlmError, LlmNotConfigured, llm, model_name
from ..state import PageText
from .state import IngestError


# 장마다 이미지 하나만 넘기는데 'N번째 장'을 옮기라고 하자 '[2번째 장이 보이지 않습니다…]'가 문제 글에 들어갔다
_NOT_READ = re.compile(r"\[[^\]\n]*[가-힣][^\]\n]*\]|[^\n]*(보이지 않습니다|이미지가 없습니다)[^\n]*")  # 대괄호로 감싼 한글 설명 한 줄(예시 '[1, 2]'는 글이다)


def transcribe_messages(page: int) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                f"이 이미지 한 장에 보이는 글만 그대로 옮겨 적어라(여러 장 가운데 {page}번째 장이라는 것은 참고만 한다). 문제를 지어내지 마라.\n"
                "제목이 보이면 ## 제약, ## 입력, ## 출력처럼 붙여라. 표는 마크다운 표로 옮겨라. 읽히지 않는 글자는 [?]로 둬라.\n"
                '출력: {"readable": true, "text": "옮겨 적은 글"}. 그림이 없거나 글을 읽을 수 없으면 {"readable": false, "text": ""}(설명이나 사과를 적지 마라).\n'
                '좋은 답: {"readable": true, "text": "## 입력\\n첫 줄에 두 정수 a, b"}\n'
                '나쁜 답: {"text": "이 문제는 두 수를 더하는 문제입니다. 예를 들어…"}(요약과 지어낸 예)'
            ),
        }
    ]


def transcribe_page(page_no: int, image: bytes) -> str:
    try:
        got = llm(model_name()).use(transcribe_messages(page_no), PageText, images=[image], task="ingest.transcribe")
    except LlmNotConfigured:
        raise
    except LlmError:
        raise IngestError(f"{page_no}번째 장을 읽지 못했어요. 다시 올리거나 그 장의 글을 직접 붙여 넣어 주세요.") from None
    if not got.readable or not got.text.strip() or _NOT_READ.fullmatch(got.text.strip()):  # 글 대신 모델의 설명 한 줄이면 못 읽은 것이다(다시 읽는다)
        raise IngestError(f"{page_no}번째 장을 읽지 못했어요. 다시 올리거나 그 장의 글을 직접 붙여 넣어 주세요.")
    return got.text.strip()
