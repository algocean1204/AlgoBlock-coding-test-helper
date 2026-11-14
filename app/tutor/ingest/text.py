"""글 잇기(join_text). 입력 글 → md·txt·PDF를 올린 순서대로 빈 줄 하나로 잇는다. 모델이 없다.
나눠 찍은 이미지 장끼리 겹친 줄 빼기(merge가 쓴다)도 여기 둔다."""

import io
import re
from difflib import SequenceMatcher

from .state import IngestError


def decode(name: str, data: bytes) -> str:
    """UTF-8(BOM 포함)로 읽고, 안 되면 CP949로 읽는다."""
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise IngestError(f"{name} 파일을 읽지 못했어요. 다시 올려 주세요.")


def pdf_text(name: str, data: bytes) -> str:
    """페이지별 글을 잇는다. 스캔본처럼 글이 없으면 실패."""
    from pypdf import PdfReader  # PDF를 올릴 때만 필요하다

    try:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    except Exception:  # 깨진 파일은 종류를 가리지 않고 같은 실패로 알린다
        raise IngestError(f"{name} 파일을 읽지 못했어요. 다시 올려 주세요.") from None
    if not text.strip():
        raise IngestError(f"{name}에서 글을 찾지 못했어요. 이미지로 올려 주세요.")
    return tidy(text)


def tidy(text: str) -> str:
    """탭·줄바꿈을 뺀 제어 문자는 공백으로(크롬 'PDF로 저장'은 공백을 U+0001로 뽑는다), 줄 안의 연속 공백은 하나로. 줄 앞 들여쓰기는 둔다."""
    return re.sub(r"(?<=\S) {2,}", " ", re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text))


def read_doc(name: str, data: bytes) -> str:
    return pdf_text(name, data) if name.lower().endswith(".pdf") else decode(name, data)


def join_text(text: str | None, docs: list[tuple[str, bytes]]) -> str:
    parts = [text or "", *(read_doc(name, data) for name, data in docs)]
    return "\n\n".join(part.strip() for part in parts if part.strip())


_RULE = re.compile(r"[|: -]*-{3,}[|: -]*")  # 마크다운 표의 구분 줄 |---|:--|
OVERLAP = 30  # 겹침을 찾는 가장 많은 줄 수


def _rows(text: str) -> list[tuple[str, int]]:
    """(정규화한 줄, 원래 줄 번호). 빈 줄과 표 구분 줄은 건너뛴다."""
    rows = []
    for number, line in enumerate(text.splitlines()):
        key = re.sub(r"\s+", " ", line).strip()
        if key and not _RULE.fullmatch(key):
            rows.append((key, number))
    return rows


def _same(x: str, y: str) -> bool:
    """거의 같으면 같은 줄. 글자 읽기(tesseract)는 겹친 줄을 장마다 조금씩 다르게 읽는다. 짧은 줄은 우연히 비슷할 수 있어 그대로 견준다.
    한 줄이 다른 줄의 앞부분이면(반만 읽힌 줄) 같은 줄이 아니다(drop_overlap의 반쪽 줄 갈래가 다룬다)."""
    if x == y or x.startswith(y) or y.startswith(x):
        return x == y
    return min(len(x), len(y)) >= 6 and SequenceMatcher(None, x, y, autojunk=False).ratio() >= 0.85


def _same_rows(xs: list[str], ys: list[str]) -> bool:
    return len(xs) == len(ys) and all(map(_same, xs, ys))


def drop_overlap(before: str, after: str) -> tuple[str, str]:
    """위·아래로 나눠 찍은 두 장. 뒤 장의 첫 k줄이 앞 장의 마지막 k줄과 같으면(가장 큰 k. 줄마다 거의 같으면 같다) 뒤 장에서 뺀다.
    앞 장 마지막 줄이 반만 읽혔으면(뒤 장 어느 줄의 앞부분이고 그 앞 줄들은 겹친다) 그 반쪽 줄을 지우고 뒤 장은 그 줄부터 쓴다. 겹침이 없으면 그대로."""
    a, b = _rows(before), _rows(after)
    keys_a, keys_b = [key for key, _ in a], [key for key, _ in b]
    for k in range(min(OVERLAP, len(a), len(b)), 0, -1):
        if _same_rows(keys_a[-k:], keys_b[:k]):
            return before, "\n".join(after.splitlines()[b[k - 1][1] + 1 :])
    last = keys_a[-1] if keys_a else ""
    if len(last) >= 4:  # 아주 짧은 줄은 우연히 앞부분이 같을 수 있다
        for j in range(min(OVERLAP, len(b))):
            if keys_b[j] != last and keys_b[j].startswith(last) and _same_rows(keys_b[:j], keys_a[len(keys_a) - 1 - j : -1]):
                return "\n".join(before.splitlines()[: a[-1][1]]), "\n".join(after.splitlines()[b[j][1] :])
    return before, after
