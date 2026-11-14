"""채점 확인 실행기.

샘플: python3 run.py python [--mode function|program] [--case 1]
제출: python3 run.py python --source 내코드.py --cases cases.json [--problem 문제.md] [--mode …]
      cases.json은 케이스 목록이거나 {"function": [...], "program": [...]}다.
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_judge():
    key = "algoblock_check_judge"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, ROOT / "judge.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


judge = load_judge()
LANGUAGES = judge.LANGUAGES


def show(report):
    head = f"[{report['language']}/{report['mode'] or '-'}] {report['status']}"
    if report.get("fallback_from"):
        head += f" ({report['fallback_from']} → {report['mode']})"
    print(head)
    if report.get("reason"):
        print(f"  이유: {report['reason']}")
    if report.get("compile"):
        print(report["compile"].get("stderr", "").rstrip(), file=sys.stderr)
    for case in report["cases"]:
        print(f"  case {case['id']}: {case['status']} ({case['time_ms']}ms)")
        if case["status"] != "passed":
            print(f"    기대: {case['expected']!r}\n    출력: {case['stdout'].strip()!r}")
            if case.get("stderr"):
                print(case["stderr"].rstrip(), file=sys.stderr)


def run_samples(language, modes, case_id=None):
    lang = judge.load_language(language)
    reports = []
    for mode in modes:
        folder = ROOT / language / mode
        source = (folder / lang.SAMPLE[mode]).read_text(encoding="utf-8")
        cases = json.loads((folder / "cases.json").read_text(encoding="utf-8"))
        if case_id:
            cases = [case for case in cases if case["id"] == case_id]
        report = judge.judge(language, source, cases, mode=mode)
        show(report)
        reports.append(report)
    return reports


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=LANGUAGES)
    parser.add_argument("--mode", choices=("function", "program"))
    parser.add_argument("--case")
    parser.add_argument("--source", help="채점할 제출 파일")
    parser.add_argument("--cases", help="케이스 JSON 파일")
    parser.add_argument("--problem", help="문제 설명 파일(모드를 정할 때 본다)")
    args = parser.parse_args()

    if args.source:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8")) if args.cases else []
        problem = Path(args.problem).read_text(encoding="utf-8") if args.problem else ""
        source = Path(args.source).read_text(encoding="utf-8")
        reports = [judge.judge(args.language, source, cases, problem=problem, mode=args.mode)]
        show(reports[0])
    else:
        modes = (args.mode,) if args.mode else ("function", "program")
        reports = run_samples(args.language, modes, args.case)
    return 0 if all(r["status"] in {"passed", "toolchain_missing"} for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
