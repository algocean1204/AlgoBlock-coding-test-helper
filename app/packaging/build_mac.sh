#!/bin/sh
# macOS 설치 파일(.dmg)을 만든다. 서명하지 않는다(받은 사람이 처음 여는 법은 Docs/guide/install.md).
# 쓰는 법: sh app/packaging/build_mac.sh     결과: app/packaging/dist/AlgoBlock-<버전>-<아키텍처>.dmg
# 개발용 앱: ALGOBLOCK_FLAVOR=dev sh app/packaging/build_mac.sh     결과: app/packaging/dist/AlgoBlock Dev.app(자료 폴더·포트가 따로고 업데이트하지 않는다)
# 릴리스에 올리는 고정 이름의 사본도 만든다: AlgoBlock-macos-arm64.dmg(Apple Silicon), AlgoBlock-macos-x86_64.dmg(Intel)
# 그 사본의 SHA-256을 dist/SHA256SUMS-macos-<아키텍처>에 적는다. 릴리스에는 빌드마다의 SHA256SUMS-*를 합친 SHA256SUMS 하나를 올린다(README)
set -e
cd "$(dirname "$0")"
VERSION=$(sed -n 's/^VERSION = "\([^"]*\)".*/\1/p' ../ui/updater.py)  # 앱의 버전은 updater.py 한 곳
test -n "$VERSION"
ARCH=$(uname -m)
uv venv -q --allow-existing --python 3.12 .build-venv
uv pip install -q --python .build-venv/bin/python pyinstaller langgraph pywebview qdrant-client pypdf onnxruntime tokenizers
.build-venv/bin/python ../tutor/knowledge/embed.py fetch models  # 임베딩 모델(약 250MB). 이미 있으면 받지 않는다
rm -rf build dist
.build-venv/bin/pyinstaller --noconfirm --clean --log-level WARN algoblock.spec
if [ "$ALGOBLOCK_FLAVOR" = "dev" ]; then  # 개발용 앱(ALGOBLOCK_FLAVOR=dev sh app/packaging/build_mac.sh): 이 기기에서만 쓰므로 dmg·해시를 만들지 않는다
  ls -d "dist/AlgoBlock Dev.app"
  exit 0
fi
DMG="dist/AlgoBlock-$VERSION-$ARCH.dmg"
STAGE=$(mktemp -d)
cp -R dist/AlgoBlock.app "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -quiet -volname "AlgoBlock" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"
cp "$DMG" "dist/AlgoBlock-macos-$ARCH.dmg"
(cd dist && shasum -a 256 "AlgoBlock-macos-$ARCH.dmg" > "SHA256SUMS-macos-$ARCH")
ls -lh "$DMG" "dist/AlgoBlock-macos-$ARCH.dmg"
cat "dist/SHA256SUMS-macos-$ARCH"
