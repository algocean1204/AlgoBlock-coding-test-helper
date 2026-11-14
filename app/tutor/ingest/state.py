from dataclasses import dataclass, field


@dataclass
class IngestState:
    """읽기 진행과 입력. 노드는 바뀐 필드만 돌려준다."""

    text: str = ""  # 입력 글 → join_text 뒤에는 이은 글
    files: list = field(default_factory=list)  # 문항 파일 목록 (이름, 바이트)
    docs: list = field(default_factory=list)  # 글 파일 목록
    pages: list = field(default_factory=list)  # 이미지 목록
    index: int = 0  # 장 위치
    parts: list = field(default_factory=list)  # 장 글 목록
    model_failed: str = ""  # 이 장을 모델로 못 읽은 까닭: not_configured(AI 연결 없음), failed(시간 초과 등). 비면 읽었다
    used_ocr: bool | str = False  # 본문에 tesseract로 읽은 장이 있다: True(AI 연결 없음), "ai_failed"(AI로 두 번 읽지 못한 장이 있음)
    ocr_pages: list = field(default_factory=list)  # tesseract로 읽은 장의 번호(0부터). 나머지 장은 AI가 읽었다
    body: str = ""  # 문항 본문


class IngestError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "ingest_failed"
