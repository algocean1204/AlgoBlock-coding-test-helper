"""기기 안 임베딩 모델 하나: multilingual-e5-small(MIT). 키도 네트워크도 없이 누구에게나 같은 벡터가 나온다.

폴더 하나에서 파일 둘(model.onnx, tokenizer.json)을 읽는다. 돌릴 때는 내려받지 않는다: 파일이 없으면 벡터 검색을 끈다.
설치 파일에는 같이 들어 있다. 소스로 돌릴 때는 한 번 받아 둔다:
  python3 tutor/knowledge/embed.py fetch <폴더>      (app에서. 표준 라이브러리만 쓴다. 약 250MB)
받은 파일은 크기와 SHA-256을 아래 값과 견준다(다른 파일이 섞이면 색인의 벡터가 달라져 답이 바뀐다).

모델 파일은 반정밀(fp16, 235MB)이다. eval/recall_hard.py(질의 120개)로 재 보면 원본(470MB)과 모든 조건에서 점수가 같고,
arm64와 x86에서 같은 글의 벡터가 같았다(코사인 1.0000). 더 작은 8비트 파일(118MB)은 쓰지 않는다: CPU 종류에 따라 벡터가 달라졌고
(코사인 0.993~0.996) x86에서 점수가 조금 흔들렸다. 모두에게 같은 결과가 이 모델을 고른 이유라서 크기보다 이것이 먼저다.
e5 계열은 글 앞에 "query: "를 붙여 넣어야 한다(양쪽 모두 붙이는 대칭 비교).
"""

import hashlib
import sys
import threading
import urllib.request
from pathlib import Path

REPO = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
NAME = f"{REPO}@{REVISION[:7]}/fp16"  # 색인에 적어 두는 이름. 모델이나 파일을 바꾸면 이 이름이 바뀌고 색인을 다시 만든다
DIM = 384
# 저장 이름 → (저장소 안 경로, 크기, SHA-256)
FILES = {
    "model.onnx": ("onnx/model_O4.onnx", 235052531, "4654c156f3e4171abc9c716cdb771bf9116455d15ac1aab364aeeede0e3205b0"),
    "tokenizer.json": ("tokenizer.json", 17082730, "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39"),
}
MAX_TOKENS = 512


def present(directory) -> bool:
    """파일 둘이 제 크기로 있는가(해시는 받을 때 한 번만 본다)."""
    return all((Path(directory) / name).is_file() and (Path(directory) / name).stat().st_size == size for name, (_, size, _) in FILES.items())


def fetch(directory) -> None:
    """없는 파일만 받는다. 크기나 해시가 다르면 지우고 멈춘다."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    for name, (remote, size, digest) in FILES.items():
        path = target / name
        if path.is_file() and path.stat().st_size == size:
            continue
        part, seen = path.with_suffix(".part"), hashlib.sha256()
        with urllib.request.urlopen(f"https://huggingface.co/{REPO}/resolve/{REVISION}/{remote}", timeout=60) as response, open(part, "wb") as out:
            while chunk := response.read(1 << 20):
                out.write(chunk)
                seen.update(chunk)
        if part.stat().st_size != size or seen.hexdigest() != digest:
            part.unlink()
            raise RuntimeError(f"{name}: 받은 파일이 기대한 것과 다릅니다.")
        part.replace(path)


def e5_embedder(directory):
    """글 목록 → 길이 1로 맞춘 384차원 벡터 목록. 모델은 처음 부를 때 올린다(1초 안팎)."""
    loaded, lock = [], threading.Lock()

    def embed(texts: list[str]) -> list[list[float]]:
        with lock:
            if not loaded:
                import numpy
                import onnxruntime
                from tokenizers import Tokenizer

                tokenizer = Tokenizer.from_file(str(Path(directory) / "tokenizer.json"))
                tokenizer.enable_truncation(MAX_TOKENS)
                tokenizer.enable_padding(pad_id=tokenizer.token_to_id("<pad>"), pad_token="<pad>")
                session = onnxruntime.InferenceSession(str(Path(directory) / "model.onnx"), providers=["CPUExecutionProvider"])
                loaded.append((numpy, tokenizer, session, {item.name for item in session.get_inputs()}))
        np, tokenizer, session, wanted = loaded[0]
        rows = tokenizer.encode_batch(["query: " + text for text in texts])
        ids = np.array([row.ids for row in rows], dtype=np.int64)
        mask = np.array([row.attention_mask for row in rows], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": mask, "token_type_ids": np.zeros_like(ids)}
        hidden = session.run(None, {key: value for key, value in feed.items() if key in wanted})[0]
        weight = mask[..., None].astype(hidden.dtype)
        pooled = (hidden * weight).sum(axis=1) / weight.sum(axis=1)  # 채움 토큰을 뺀 평균
        return (pooled / np.linalg.norm(pooled, axis=1, keepdims=True)).tolist()

    return embed


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "fetch":
        sys.exit("쓰는 법: python3 tutor/knowledge/embed.py fetch <폴더>")
    fetch(sys.argv[2])
    print(f"{NAME}: {sys.argv[2]}")
