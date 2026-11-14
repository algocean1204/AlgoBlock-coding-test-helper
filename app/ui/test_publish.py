"""공개 전 검사: git이 추적하는 파일에 키, 개인 경로·이메일·작업 경로, 과정 글(몇 바퀴째·언제 돌렸다·몇 개 중 몇 개), 큰 파일이 없는지, 공개에 필요한 파일과 링크가 맞는지 본다. 표준 라이브러리만 쓴다.

실행: cd app && python3 ui/test_publish.py            # 지금 추적하는 파일
      cd app && python3 ui/test_publish.py history    # 지금 브랜치의 모든 커밋의 모든 파일(걸리면 커밋과 경로를 내고 1로 끝난다)
"""

import ast
import posixpath
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_structure  # noqa: E402  (내부 폴더·파일 이름은 한 곳에 둔다)

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
REPO = "algocean1204/AlgoBlock-coding-test-helper"
MAX_BYTES = 50 * 1024 * 1024

KEY_SHAPES = re.compile(
    r"sk-ant-[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}"
    r"|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)
PERSONAL = re.compile(r"/Users/(?!Shared/)[^/\s\"'`]+|/home/(?!runner/)[a-z][^/\s\"'`]*/|[A-Za-z]:\\\\?Users\\\\?[^\\\s\"'`]+")
EMAIL = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63}){0,5}\.[A-Za-z]{2,24}")  # 길이를 묶어 긴 글자 줄에서 느려지지 않게
EMAIL_OK = re.compile(r"@(?:example\.(?:com|org)|users\.noreply\.github\.com)$")  # 예시 주소와 GitHub이 가리는 주소만
WORK_PATH = re.compile(r"(?<![\w.])/tmp/[A-Za-z0-9._-]{3,}")  # 작업하다 쓴 폴더(시험 속 가짜 경로 /tmp/x 같은 짧은 이름은 된다)
# 과정 글: 만드는 동안의 기록이 코드·문서에 남은 것. 몇 번째 돌림인가, 몇 개 중 몇 개였나(재 본 결과), 재 본 점수, 언제 무엇을 돌렸나
PROCESS_TEXT = re.compile(
    r"(?<!\d)\d{1,3} ?(?:바퀴|회차|번째 돌)"
    r"|\d+개 중 \d+개"
    r"|(?:P@\d+|MRR) ?\d\.\d"
    r"|사용자 결정|결함 \d"
    r"|20\d\d-[01]\d-[0-3]\d(?:에|까지|부터|\))?\s?(?:한 번 |처음 )?(?:측정|결정|QA|돌렸|돌려|쟀|재 봄|재 보|빌드|추가|실사용|검수)"  # 가격 확인 날짜는 된다
)
PROBLEM_CONTENT = ("app/ui/problems/", "app/ui/builtin.json")  # 문제 글·가이드는 내용이다(바퀴 수나 개수가 문제 글에 나올 수 있다). 과정 글은 거기서 보지 않는다
INTERNAL_PATH = re.compile(  # 구조 시험의 INTERNAL(내부 폴더·파일 이름)은 internal_path가 따로 본다
    r"(?:^|/)(?:agents\.md|agent\.md|claude\.md|gemini\.md|\.mcp\.json|\.env|keys\.json|auth|\.claude|\.cursor|\.codex|\.grok|\.agents)(?:/|$)"
    r"|\.(?:db|sqlite3?|log|pem|key|p12|pfx|dmg|exe)$|(?:^|/)usage\.jsonl$|^app/tutor/eval/results/",
    re.IGNORECASE,
)

def internal_path(path: str) -> bool:
    return bool(INTERNAL_PATH.search(path)) or bool(test_structure.INTERNAL & {part.lower() for part in path.split("/")})


BINARY = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns", ".woff", ".woff2", ".ttf", ".otf", ".onnx", ".pdf", ".zip"}
MD_LINK = re.compile(r"\]\(([^)\s]+)\)|<img[^>]*\ssrc=\"([^\"]+)\"")


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotepath=off", *args], capture_output=True, text=True, check=True).stdout


def tracked() -> list[str]:
    """올라갈 파일: 추적하는 파일과 무시되지 않은 새 파일(공개는 이 상태를 그대로 첫 커밋으로 한다)."""
    return sorted({path for path in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0") if path and (ROOT / path).exists()})


def text_of(data: bytes, path: str) -> str | None:
    if Path(path).suffix.lower() in BINARY or b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", "replace")


def problems_in(path: str, text: str) -> list[str]:
    """한 파일의 글에서 걸리는 것: [종류: 찾은 글]."""
    found = [f"키 모양: {m.group()[:12]}…" for m in KEY_SHAPES.finditer(text)]
    found += [f"개인 경로: {m.group()}" for m in PERSONAL.finditer(text)]
    found += [f"이메일: {m.group()}" for m in EMAIL.finditer(text) if not EMAIL_OK.search(m.group()) and not m.group().startswith("git@")]
    found += [f"작업 경로: {m.group()}" for m in WORK_PATH.finditer(text)]
    if not path.startswith(PROBLEM_CONTENT):
        found += [f"과정 글: {m.group()}" for m in PROCESS_TEXT.finditer(text)]
    return found


class Publish(unittest.TestCase):
    maxDiff = 0
    paths = tracked()

    def test_no_internal_paths(self):
        self.assertEqual([path for path in self.paths if internal_path(path) and path != ".env.example"], [])

    def test_contents(self):
        found = []
        for path in self.paths:
            file = ROOT / path
            if path != SELF and file.is_file() and (text := text_of(file.read_bytes(), path)) is not None:
                found += [f"{path}: {what}" for what in problems_in(path, text)]
        self.assertEqual(found, [], "\n".join(found[:40]))

    def test_process_text_shapes(self):
        """과정 글의 종류(몇 번째 돌림, 언제 돌렸나, 몇 개 중 몇 개, 재 본 점수)는 잡고, 쓰는 사람 문서의 정상 문장은 잡지 않는다."""
        caught = ["어긋난다. 2바퀴에서 실제로 그랬다", "9회차에 확인", "3번째 돌림", "안내 말 30개 중 22개가 틀렸다", "재 보니 P@1 0.50이었다", "MRR 0.8",
                  "방법: 2026-11-13에 한 번 돌렸다.", "2026-11-13 측정", "2026-11-13에 재 봄", "작업 폴더 /tmp/work-1/out"]
        fine = ["트랙을 한 바퀴 돌면", "k개 중 가장 느린 기록", "공개 예시 ${total}개 중 ${n}개 통과", "(2026-11-13 확인)", "지표는 P@1(1위가 같은 구조인 비율)이다",
                "시험 속 가짜 경로 /tmp/x/main.py", "날짜 2026-10-15T00:00:00+09:00", "한 번 더 돌렸어요", "되돌렸어요"]
        self.assertEqual([text for text in caught if not problems_in("a.md", text)], [])
        self.assertEqual([(text, problems_in("a.md", text)) for text in fine if problems_in("a.md", text)], [])
        self.assertEqual(problems_in("app/ui/problems/x/problem.json", "트랙을 3바퀴 돌았고 5개 중 2개"), [])  # 문제 글은 내용이다

    def test_no_big_files(self):
        self.assertEqual([path for path in self.paths if (ROOT / path).is_file() and (ROOT / path).stat().st_size > MAX_BYTES], [])

    def test_license(self):
        self.assertIn("LICENSE", self.paths)
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text(encoding="utf-8"))

    def test_env_example_matches_code(self):
        """.env.example의 키 이름이 서버가 읽는 키 이름(server.py의 KEYS)과 같고, 값이 비어 있다."""
        rows = [line.split("=", 1) for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        tree = ast.parse((ROOT / "app/ui/server.py").read_text(encoding="utf-8"))
        keys = next(node.value for node in tree.body if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "KEYS")
        self.assertEqual({name.strip() for name, _ in rows}, set(ast.literal_eval(keys).values()))
        self.assertEqual([name for name, value in rows if value.strip()], [])

    def test_links(self):
        """마크다운 문서의 상대 링크는 추적하는 파일·폴더를, 내려받기 링크는 이 저장소의 릴리스와 패키징이 만드는 이름을 가리킨다."""
        folders = {p.rsplit("/", i)[0] for p in self.paths for i in range(1, p.count("/") + 1)}
        names = set(re.findall(r"AlgoBlock-[A-Za-z0-9.-]+\.(?:dmg|exe|zip)", "".join((ROOT / p).read_text(encoding="utf-8") for p in self.paths if p.startswith("app/packaging/") and p.endswith((".py", ".sh", ".ps1", ".spec")))))
        bad = []
        for doc in [path for path in self.paths if path.endswith(".md")]:
            for m in MD_LINK.finditer((ROOT / doc).read_text(encoding="utf-8")):
                link = (m.group(1) or m.group(2)).split("#")[0]
                if link.startswith("https://github.com/algocean1204/"):
                    if not link.startswith(f"https://github.com/{REPO}"):
                        bad.append(f"{doc}: 다른 저장소 {link}")
                    elif "/releases/latest/download/" in link and link.rsplit("/", 1)[1] not in names:
                        bad.append(f"{doc}: 패키징이 만들지 않는 파일 {link}")
                    continue
                if not link or re.match(r"[a-z]+:", link):
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(doc), link))
                if target not in self.paths and target not in folders:
                    bad.append(f"{doc}: 없는 경로 {link}")
        self.assertEqual(bad, [], "\n".join(bad))


def history() -> int:
    """지금 브랜치의 모든 커밋에 든 모든 파일(경로와 내용)을 본다. 걸린 것이 없으면 0."""
    commits = git("rev-list", "HEAD").split()
    blob_paths: dict[str, set[str]] = {}
    commit_blobs: dict[str, set[str]] = {}
    bad_paths: dict[str, set[str]] = {}
    for commit in commits:
        rows = [row.split("\t", 1) for row in git("ls-tree", "-r", "-z", commit).split("\0") if row]
        commit_blobs[commit] = {meta.split()[2] for meta, _ in rows}
        for meta, path in rows:
            blob_paths.setdefault(meta.split()[2], set()).add(path)
            if internal_path(path) and path != ".env.example":
                bad_paths.setdefault(path, set()).add(commit)
    bad_blobs: dict[str, list[str]] = {}
    batch = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"], input="\n".join(blob_paths).encode() + b"\n", capture_output=True, check=True).stdout
    at = 0
    while at < len(batch):
        head_end = batch.index(b"\n", at)
        sha, _, size = batch[at:head_end].decode().split()
        data = batch[head_end + 1: head_end + 1 + int(size)]
        at = head_end + 1 + int(size) + 1
        path = sorted(blob_paths[sha])[0]
        if SELF in blob_paths[sha] or any(internal_path(p) for p in blob_paths[sha]) or (text := text_of(data, path)) is None:
            continue
        if found := problems_in(path, text):
            bad_blobs[sha] = found
    content_commits = {c for c, blobs in commit_blobs.items() if blobs & bad_blobs.keys()}
    path_commits = set().union(*bad_paths.values()) if bad_paths else set()
    content_paths = sorted({p for sha in bad_blobs for p in blob_paths[sha]})
    print(f"커밋 {len(commits)}개, 서로 다른 파일 내용 {len(blob_paths)}개를 봤다.")
    print(f"내부 경로: 경로 {len(bad_paths)}개, 커밋 {len(path_commits)}개")
    for path in sorted(bad_paths)[:30]:
        print(f"  {path}  (커밋 {len(bad_paths[path])}개, 예: {sorted(bad_paths[path])[0][:9]})")
    print(f"내용(키·개인 경로·이메일·작업 경로·과정 글): 경로 {len(content_paths)}개, 커밋 {len(content_commits)}개")
    kinds: dict[str, int] = {}
    for found in bad_blobs.values():
        for what in found:
            kinds[what.split(":")[0]] = kinds.get(what.split(":")[0], 0) + 1
    print("  종류별 걸린 수:", kinds)
    for path in content_paths[:30]:
        print(f"  {path}")
    print(f"걸린 커밋 모두: {len(path_commits | content_commits)}개")
    return 1 if bad_paths or bad_blobs else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["history"]:
        sys.exit(history())
    unittest.main()
