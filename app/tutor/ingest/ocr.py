"""OCR 읽기(ocr). tesseract를 하위 프로세스로 부르고, 결과를 믿을지 정한다."""

import subprocess

OCR_TIMEOUT = 10
OCR_MIN_CHARS = 20  # 공백을 뺀 글자 수
OCR_MAX_ODD = 0.1  # 한글·영문·숫자·기본 기호가 아닌 글자 비율
_PLAIN_EXTRA = "·…×÷≤≥≠“”‘’「」『』→←↑↓"


def run_ocr(image: bytes) -> str:
    """기기에 없거나 실패하거나 10초를 넘으면 빈 글이다(모델로 넘어간다)."""
    try:
        done = subprocess.run(
            # psm 4: 한 단 글. 기본(3)은 짧은 캡처에서 줄을 조각내 잡글을 만든다
            ["tesseract", "stdin", "stdout", "-l", "kor+eng", "--psm", "4"],
            input=image,
            capture_output=True,
            timeout=OCR_TIMEOUT,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout.decode("utf-8", "replace").strip()


def ocr_ok(text: str) -> bool:
    chars = [c for c in text if not c.isspace()]
    if len(chars) < OCR_MIN_CHARS:
        return False
    odd = sum(1 for c in chars if not (c.isascii() or "가" <= c <= "힣" or "ㄱ" <= c <= "ㅣ" or c in _PLAIN_EXTRA))
    return odd <= len(chars) * OCR_MAX_ODD
