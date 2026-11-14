"""파일 나누기(split_files)."""

from .state import IngestError

IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
DOC_TYPES = (".md", ".txt", ".pdf")
MAX_IMAGES = 20


def split_files(files: list[tuple[str, bytes]]) -> tuple[list, list]:
    docs, images = [], []
    for name, data in files:
        lower = name.lower()
        if lower.endswith(IMAGE_TYPES):
            images.append(data)
        elif lower.endswith(DOC_TYPES):
            docs.append((name, data))
        else:
            raise IngestError(f"올릴 수 없는 파일이에요({name}). 이미지, md·txt, PDF만 받아요.")
    if len(images) > MAX_IMAGES:
        raise IngestError(f"이미지는 {MAX_IMAGES}장까지 받아요.")
    return docs, images
