"""A1 문항 읽기 그래프. 메인 튜터 그래프 밖이다(입력이 다르다). 실패는 IngestError로 올린다.

split_files → join_text -- 이미지 있음 --> transcribe -- 읽음 --> (다음 장) transcribe | merge
                                                       -- 모델 없음·두 번 실패 --> ocr -- 믿음 --> (다음 장) transcribe | merge
                                                                                -- 못 믿음 --> 실패
                       -- 이미지 없음 --> merge
"""

from functools import cache

from langgraph.graph import END, START, StateGraph

from .nodes import join_text, merge, read_ocr, split_files, transcribe
from .transcribe import transcribe_page
from .state import IngestState

STEPS = {"N1": "split_files", "N2": "join_text", "N3": "ocr", "N4": "transcribe", "N5": "merge"}


def next_page(state: IngestState) -> str:
    return "transcribe" if state.index < len(state.pages) else "merge"


def after_transcribe(state: IngestState) -> str:
    return "ocr" if state.model_failed else next_page(state)


@cache
def graph():
    g = StateGraph(IngestState)
    g.add_node("split_files", split_files)
    g.add_node("join_text", join_text)
    g.add_node("ocr", read_ocr)
    g.add_node("transcribe", transcribe)
    g.add_node("merge", merge)
    g.add_edge(START, "split_files")
    g.add_edge("split_files", "join_text")
    g.add_conditional_edges("join_text", next_page, {"transcribe": "transcribe", "merge": "merge"})
    g.add_conditional_edges("transcribe", after_transcribe, {"ocr": "ocr", "transcribe": "transcribe", "merge": "merge"})
    g.add_conditional_edges("ocr", next_page, {"transcribe": "transcribe", "merge": "merge"})
    g.add_edge("merge", END)
    return g.compile()


def read_pages(text: str | None, files: list[tuple[str, bytes]]) -> dict:
    """extract_with_note와 같이 읽고 읽은 상태를 통째로 준다(body, used_ocr, pages, parts, ocr_pages, text). 읽기 검증(check)과 다시 읽기(reread)가 쓴다."""
    return dict(graph().invoke(IngestState(text=text or "", files=list(files)), {"recursion_limit": 100}))


def reread(done: dict, index: int) -> str:
    """AI가 읽은 장 하나를 한 번 더 읽어(모델 1회) 그 장의 글을 바꾸고 다시 잇는다. 바뀐 본문을 돌려준다(done도 바꾼다). 실패하면 IngestError."""
    parts = list(done["parts"])
    parts[index] = transcribe_page(index + 1, done["pages"][index])
    done["parts"] = parts
    done["body"] = merge(IngestState(text=done["text"], parts=parts))["body"]
    return done["body"]


def extract(text: str | None, files: list[tuple[str, bytes]]) -> str:
    """입력 글과 (이름, 바이트) 파일에서 문항 본문 하나. 실패면 IngestError."""
    return extract_with_note(text, files)[0]


def extract_with_note(text: str | None, files: list[tuple[str, bytes]]) -> tuple[str, bool | str]:
    """extract와 같고, 본문에 tesseract로 읽은 장이 들었는지(틀린 글자가 많을 수 있다)를 함께 준다.
    False: 쓰지 않음, True: AI가 연결되지 않아 씀, "ai_failed": AI가 있는데 두 번 읽지 못한 장이 있어 씀(참으로 읽혀 예전 화면도 그대로 돈다)."""
    # 이미지 20장 × (transcribe, ocr) + 앞뒤 노드. 상한을 넘기 전에 split_files가 거른다.
    done = graph().invoke(IngestState(text=text or "", files=list(files)), {"recursion_limit": 100})
    return done["body"], done["used_ocr"]
