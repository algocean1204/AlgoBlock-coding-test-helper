"""A1(문항 읽기) 노드: split_files, join_text, ocr, transcribe, merge."""

from ..llm import LlmNotConfigured
from . import ocr as ocr_tool
from .files import split_files as split
from .state import IngestError, IngestState
from .text import drop_overlap
from .text import join_text as join
from .transcribe import transcribe_page


def split_files(state: IngestState) -> dict:
    docs, images = split(state.files)
    return {"docs": docs, "pages": images}


def join_text(state: IngestState) -> dict:
    return {"text": join(state.text, state.docs), "index": 0, "parts": []}


def read_ocr(state: IngestState) -> dict:
    """모델로 못 읽은 장만 온다. 못 믿을 글이면 AI 연결이 없을 때는 연결 안내(LlmNotConfigured), 아니면 그 장의 실패."""
    got = ocr_tool.run_ocr(state.pages[state.index])
    if not ocr_tool.ocr_ok(got):
        if state.model_failed == "not_configured":
            raise LlmNotConfigured("이미지를 읽을 모델이 연결되어 있지 않습니다.")
        raise IngestError(f"{state.index + 1}번째 장을 읽지 못했어요. 다시 올리거나 그 장의 글을 직접 붙여 넣어 주세요.")
    failed = state.model_failed == "failed" or state.used_ocr == "ai_failed"  # AI가 있는데 못 읽은 장이 있다(화면이 다른 안내를 쓴다)
    return {"parts": [*state.parts, got], "index": state.index + 1, "used_ocr": "ai_failed" if failed else True, "ocr_pages": [*state.ocr_pages, state.index]}


READ_TRIES = 2  # 모델 읽기가 실패한 장은 한 번 더 읽는다(한 장이 tesseract로 넘어가 글이 깨졌다)


def transcribe(state: IngestState) -> dict:
    """AI가 연결돼 있으면 이미지는 모델로 읽는다(tesseract는 잘못 읽은 글자를 못 걸러 낸다). 두 번 다 실패한 장만 ocr로."""
    for _ in range(READ_TRIES):
        try:
            text = transcribe_page(state.index + 1, state.pages[state.index])
        except LlmNotConfigured:
            return {"model_failed": "not_configured"}
        except IngestError:  # 시간 초과, 호출 실패, 빈 글
            continue
        return {"model_failed": "", "parts": [*state.parts, text], "index": state.index + 1}
    return {"model_failed": "failed"}


def merge(state: IngestState) -> dict:
    """글과 장을 잇는다. 이미지 장끼리는 앞 장 끝과 겹친 줄을 뒤 장에서 뺀다(글 파일과 이미지 사이에는 하지 않는다)."""
    pages: list[str] = []
    for part in state.parts:
        if pages:
            pages[-1], part = drop_overlap(pages[-1], part)
        pages.append(part)
    body = "\n\n".join(part for part in [state.text, *pages] if part.strip())
    if not body:
        raise IngestError("문제 글이 비었어요. 글을 붙여 넣거나 파일을 올려 주세요.")
    return {"body": body}
