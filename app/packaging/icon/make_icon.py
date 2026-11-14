"""앱 아이콘 파일을 만든다: app/ui/icon.svg → 탭 아이콘(favicon.svg), macOS용 icon.icns, Windows용 icon.ico.

쓰는 법(macOS, rsvg-convert와 iconutil이 있어야 한다):  python3 app/packaging/icon/make_icon.py
그림을 고치려면 app/ui/icon.svg만 고치고 이 스크립트를 다시 돌린다. 만든 파일은 저장소에 넣는다(Windows 빌드는 만든 파일만 쓴다).
"""

import struct
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "ui" / "icon.svg"


def png(size: int) -> bytes:
    return subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(SOURCE)], check=True, capture_output=True).stdout


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    # 탭 아이콘은 16px로 보이므로 둘레 여백을 잘라 그림을 키운다(같은 그림, 보이는 범위만 다르다)
    assert 'viewBox="0 0 1024 1024"' in text
    SOURCE.with_name("favicon.svg").write_text(text.replace('viewBox="0 0 1024 1024"', 'viewBox="100 100 824 824"', 1), encoding="utf-8")

    with tempfile.TemporaryDirectory() as folder:  # macOS: 크기별 PNG 묶음 → icns
        iconset = Path(folder) / "icon.iconset"
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            (iconset / f"icon_{size}x{size}.png").write_bytes(png(size))
            (iconset / f"icon_{size}x{size}@2x.png").write_bytes(png(size * 2))
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(HERE / "icon.icns")], check=True)

    sizes = (16, 24, 32, 48, 64, 128, 256)  # Windows: PNG를 그대로 담은 ico(비스타부터 읽는다)
    images = [png(size) for size in sizes]
    head = struct.pack("<HHH", 0, 1, len(sizes))
    offset = len(head) + 16 * len(sizes)
    entries = b""
    for size, data in zip(sizes, images):
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)  # 256은 0으로 적는다
        offset += len(data)
    (HERE / "icon.ico").write_bytes(head + entries + b"".join(images))
    print("만듦:", *(str(p.relative_to(HERE.parents[2])) for p in (SOURCE.with_name("favicon.svg"), HERE / "icon.icns", HERE / "icon.ico")))


if __name__ == "__main__":
    main()
