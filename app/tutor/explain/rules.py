from ..state import EXPLAIN_TITLES, ErrorInfo, Explain


def check_sections(explain: Explain) -> ErrorInfo | None:
    """제목을 고정 제목에 맞춘다. 모델이 제목 글자만 바꿔 해설 전체가 실패하던 것을 막는다.

    고정 제목이 순서만 섞여 오면 제목 순서대로 다시 놓고, 네 절인데 제목이 다르면 자리대로 고정 제목을 붙인다.
    """
    titles = [section.title.strip() for section in explain.sections]
    if sorted(titles) == sorted(EXPLAIN_TITLES):
        explain.sections.sort(key=lambda section: EXPLAIN_TITLES.index(section.title.strip()))
    elif len(explain.sections) == len(EXPLAIN_TITLES):
        for section, title in zip(explain.sections, EXPLAIN_TITLES):
            section.title = title
    if tuple(section.title for section in explain.sections) != EXPLAIN_TITLES:
        return ErrorInfo("invalid_output", "해설 절 순서가 아닙니다.")
    if any(not section.body.strip() for section in explain.sections):
        return ErrorInfo("invalid_output", "해설 절이 비었습니다.")
    return None
