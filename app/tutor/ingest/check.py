"""A1 읽기 검증: AI가 읽은 장의 숫자를 글자 읽기(tesseract)와 견준다(모델 0회). 다른 자리를 모은다.
글자 읽기가 없거나 못 믿을 글이면(ocr_ok) 견주지 않는다. 표·제한사항 같은 글 전체의 규칙 검사는 화면 서버(table_cases)가 한다."""

import re

from . import ocr as ocr_tool

NUMBER = re.compile(r"\d+(?:,\d{3})*")


def numbers(text: str) -> set[str]:
    return {found.replace(",", "") for found in NUMBER.findall(text)}


def ocr_doubts(done: dict) -> list[dict]:
    """[{where: 'n번째 장', page, ai: AI 읽기에만 있는 수, ocr: 글자 읽기에만 있는 수}]. 양쪽에 저마다 없는 수가 있을 때만 어긋난 것으로 본다
    (글자 읽기는 작은 글자·위 첨자를 자주 빠뜨린다. 한쪽에만 빠진 것은 잡지 않는다). 읽은 글자 읽기 결과는 done["ocr_text"]에 둔다(다시 견줄 때 쓴다)."""
    seen = done.setdefault("ocr_text", {})
    out = []
    for index, (page, part) in enumerate(zip(done.get("pages") or [], done.get("parts") or [])):
        if index in (done.get("ocr_pages") or []):
            continue
        if index not in seen:
            seen[index] = ocr_tool.run_ocr(page)
        if not ocr_tool.ocr_ok(seen[index]):
            continue
        ai, ocr = numbers(part), numbers(seen[index])
        if ai - ocr and ocr - ai:
            out.append({"where": f"{index + 1}번째 장", "page": index, "ai": " ".join(sorted(ai - ocr, key=lambda n: (len(n), n))),
                        "ocr": " ".join(sorted(ocr - ai, key=lambda n: (len(n), n)))})
    return out
