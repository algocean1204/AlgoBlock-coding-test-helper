"""튜터가 읽고 쓰는 SQLite. 요청 하나의 저장은 트랜잭션 하나다."""

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime

from ..knowledge.ontology import PITFALL_GROUPS
from ..state import BlockPlan, BlockState, ChatMessage, DebugState, Explain, FollowupThread, Solution, Submission, TutorContext
from .codec import explain_from_json, explain_to_json, plan_from_json, plan_to_json
from .schema import migrate

VERIFIED_STATES = (False, True, None)  # solution.verified 칸의 값: 0 통과하지 못함, 1 통과, 2 채점하지 못함(옛 자료의 0·1은 그대로 읽는다)


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        migrate(self.conn)

    def close(self) -> None:
        self.conn.close()

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO setting(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def get_setting(self, key: str) -> str:
        row = self.conn.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return "" if row is None else row["value"]

    def put_problem(
        self, problem_id: str, language: str, body: str, direct_code: str = "", title: str = ""
    ) -> None:
        self.conn.execute(
            "INSERT INTO problem(id, title, language, body, direct_code) VALUES(?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET title=excluded.title, language=excluded.language, "
            "body=excluded.body, direct_code=excluded.direct_code",
            (problem_id, title, language, body, direct_code),
        )
        self.conn.commit()

    def update_code(self, problem_id: str, direct_code: str) -> bool:
        cur = self.conn.execute(
            "UPDATE problem SET direct_code=? WHERE id=?", (direct_code, problem_id)
        )
        self.conn.commit()
        return cur.rowcount == 1

    def direct_code(self, problem_id: str) -> str | None:
        row = self.conn.execute("SELECT direct_code FROM problem WHERE id=?", (problem_id,)).fetchone()
        if row is None:
            return None
        return row["direct_code"]

    def set_language(self, problem_id: str, language: str) -> None:
        self.conn.execute("UPDATE problem SET language=? WHERE id=?", (language, problem_id))
        self.conn.commit()

    def delete_problem(self, problem_id: str) -> None:
        """문항과 그 문항의 모든 줄을 지운다. schema.py의 표는 모두 problem(id)를 ON DELETE CASCADE로 물고 있어 한 문장(한 트랜잭션)이면 된다."""
        with self.conn:
            self.conn.execute("DELETE FROM problem WHERE id=?", (problem_id,))

    def add_submission(self, problem_id: str, source: str, ok: bool, language: str = "python", status: str = "", detail: dict | None = None) -> str:
        """status는 채점 결과 종류(passed, failed, timeout, …), detail은 정확성·효율성 통과 수 같은 세부다(학습 보고서가 읽는다)."""
        submission_id = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO submission(id, problem_id, source, ok, at, language, status, detail_json) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (submission_id, problem_id, source, 1 if ok else 0, now(), language, status or ("passed" if ok else "failed"), json.dumps(detail or {}, ensure_ascii=False)),
        )
        self.conn.commit()
        return submission_id

    def submissions(self) -> list[dict]:
        """모든 제출(오래된 것부터). 학습 보고서가 쓴다. 코드는 싣지 않는다."""
        rows = self.conn.execute("SELECT problem_id, ok, at, language, status, detail_json FROM submission ORDER BY rowid").fetchall()
        return [{"problem_id": r["problem_id"], "ok": bool(r["ok"]), "at": r["at"], "language": r["language"],
                 "status": r["status"] or ("passed" if r["ok"] else "failed"), "detail": json.loads(r["detail_json"] or "{}")} for r in rows]

    STUDY = ("hints_seen", "solution_at", "solution_before_pass", "help_first_at", "help_after_reset_at", "reset_at", "hints_at_reset")

    def study(self, problem_id: str) -> dict:
        """학습 기록: 본 힌트 수(누적), 해설을 연 시각, 통과 전에 열었는지, 도움(튜터 기능·힌트·해설)을 처음 쓴 시각,
        마지막 '처음부터'(reset_at) 뒤에 도움을 처음 쓴 시각, 그 '처음부터' 때까지 본 힌트 수(이번 풀이에서 본 힌트 = hints_seen − hints_at_reset)."""
        row = self.conn.execute(f"SELECT {', '.join(self.STUDY)} FROM study WHERE problem_id=?", (problem_id,)).fetchone()
        out = {key: row[key] if row else None for key in self.STUDY}
        return {**out, "hints_seen": out["hints_seen"] or 0, "hints_at_reset": out["hints_at_reset"] or 0, "solution_before_pass": bool(out["solution_before_pass"])}

    def set_study(self, problem_id: str, **fields) -> None:
        """STUDY 가운데 준 것만 바꾼다."""
        now_ = {**self.study(problem_id), **fields}
        self.conn.execute(
            f"INSERT INTO study(problem_id, {', '.join(self.STUDY)}) VALUES(?{', ?' * len(self.STUDY)}) "
            f"ON CONFLICT(problem_id) DO UPDATE SET {', '.join(f'{key}=excluded.{key}' for key in self.STUDY)}",
            (problem_id, int(now_["hints_seen"]), now_["solution_at"], 1 if now_["solution_before_pass"] else 0, *(now_[key] for key in self.STUDY[3:6]), int(now_["hints_at_reset"])),
        )
        self.conn.commit()

    def mark_help(self, problem_id: str, this_try_only: bool = False) -> None:
        """도움(튜터 기능·힌트·해설)을 썼다: 처음 쓴 시각과 마지막 '처음부터' 뒤에 처음 쓴 시각을 비어 있을 때만 적는다.
        this_try_only: 이번 풀이에만 도움이다(처음 쓴 시각은 그대로. '처음부터' 앞에 내가 남긴 체크포인트를 되살렸을 때)."""
        study, at = self.study(problem_id), now()
        self.set_study(problem_id, help_first_at=study["help_first_at"] or (None if this_try_only else at), help_after_reset_at=study["help_after_reset_at"] or at)

    def mark_reset(self, problem_id: str) -> None:
        """'처음부터': 새 풀이가 시작된다(그 뒤의 도움을 다시 센다). 힌트는 이번 풀이에서 처음부터 다시 연다(본 힌트 수는 누적으로 남는다)."""
        self.set_study(problem_id, reset_at=now(), help_after_reset_at=None, hints_at_reset=self.study(problem_id)["hints_seen"])

    def latest_submission(self, problem_id: str) -> Submission | None:
        row = self.conn.execute(
            # 같은 초에 두 건이면 rowid가 나중 제출이다. id 문자열 순서는 쓰지 않는다.
            "SELECT id, source, ok FROM submission WHERE problem_id=? ORDER BY rowid DESC LIMIT 1",
            (problem_id,),
        ).fetchone()
        if row is None:
            return None
        return Submission(id=row["id"], source=row["source"], ok=bool(row["ok"]))

    def load(self, problem_id: str) -> TutorContext | None:
        problem = self.conn.execute("SELECT * FROM problem WHERE id=?", (problem_id,)).fetchone()
        if problem is None:
            return None
        session = self.conn.execute(
            "SELECT * FROM tutor_session WHERE problem_id=?", (problem_id,)
        ).fetchone()
        plan = plan_from_json(session["plan_json"]) if session else None
        canonical = self._solution(problem_id)
        own = Solution(**json.loads(session["solution_json"])) if session and session["solution_json"] else None
        explain = explain_from_json(session["explain_json"]) if session else None
        open_count = int(session["open_count"]) if session else 0
        return TutorContext(
            problem_id=problem_id,
            problem_text=problem["body"],
            title=problem["title"],
            language=problem["language"],
            direct_code=problem["direct_code"],
            plan=plan,
            open_count=open_count,
            chair=self._main_messages(problem_id, "chair"),
            guide=self._main_messages(problem_id, "guide"),
            followups=self._followups(problem_id),
            explain=explain,
            latest_submission=self.latest_submission(problem_id),
            block_states=self._block_states(problem_id),
            debug=self._thread(problem_id, "debug"),
            debug_state=self._debug_state(problem_id),
            **self._facts(problem_id),
            frequent_pitfalls=self._frequent_pitfalls(),
            level=self.learner_level(),
            solved=self._solved(problem_id),
            library=self._library(problem_id),
            solution=own or canonical,
            canonical=canonical,
            failed_submissions=[row["status"] or "failed" for row in self.conn.execute(
                "SELECT status FROM submission WHERE problem_id=? AND ok=0 ORDER BY rowid", (problem_id,))],
            hints_seen=self.study(problem_id)["hints_seen"] - self.study(problem_id)["hints_at_reset"],  # 이번 풀이(마지막 '처음부터' 뒤)에서 본 힌트
        )

    def _solution(self, problem_id: str) -> Solution | None:
        row = self.conn.execute("SELECT * FROM solution WHERE problem_id=?", (problem_id,)).fetchone()
        if row is None:
            return None
        return Solution(row["approach"], json.loads(row["steps_json"]), row["code"], VERIFIED_STATES[row["verified"]], json.loads(row["clues_json"]))

    def facts(self) -> list[dict]:
        """뼈대를 뽑아 둔 모든 문항(색인을 다시 채울 때 쓴다)."""
        return self._library("")

    def _library(self, problem_id: str) -> list[dict]:
        """뼈대를 뽑아 둔 다른 문항들(문항 → 패턴 엣지). 계획이 같은 패턴의 지난 문항을 찾는 데 쓴다.

        한계: 문항 전부를 읽는다(한 사람의 문항 수십~수백 개). 수천 개가 되면 패턴 엣지 표로 나눠 조인한다.
        """
        rows = self.conn.execute(
            "SELECT p.id, p.title, f.spec, f.patterns_json, s.plan_json, "
            "EXISTS (SELECT 1 FROM submission b WHERE b.problem_id=p.id AND b.ok=1) AS passed, "
            "EXISTS (SELECT 1 FROM submission b WHERE b.problem_id=p.id) AS tried "
            "FROM problem p JOIN problem_fact f ON f.problem_id=p.id LEFT JOIN tutor_session s ON s.problem_id=p.id WHERE p.id!=?",
            (problem_id,),
        ).fetchall()
        out = []
        for row in rows:
            plan = json.loads(row["plan_json"]) if row["plan_json"] else {}
            out.append({
                "problem_id": row["id"], "title": row["title"], "spec": row["spec"], "algorithm": plan.get("algorithm") or "",
                "patterns": json.loads(row["patterns_json"]), "passed": bool(row["passed"]), "tried": bool(row["tried"]),
                "flow": " → ".join(block.get("name", "") for block in plan.get("blocks") or []),
            })
        return out

    def _thread(self, problem_id: str, thread: str) -> list[ChatMessage]:
        rows = self.conn.execute(
            "SELECT * FROM message WHERE problem_id=? AND thread=? ORDER BY id", (problem_id, thread)
        ).fetchall()
        return [_message(row) for row in rows]

    def _debug_state(self, problem_id: str) -> DebugState | None:
        row = self.conn.execute("SELECT * FROM debug_state WHERE problem_id=?", (problem_id,)).fetchone()
        if row is None:
            return None
        return DebugState(row["code_hash"], row["kind"], row["line"], row["cause"], row["fixed_line"], row["step"], row["pitfall"])

    def _facts(self, problem_id: str) -> dict:
        row = self.conn.execute("SELECT * FROM problem_fact WHERE problem_id=?", (problem_id,)).fetchone()
        if row is None:
            return {}
        return {"spec": row["spec"], "patterns": json.loads(row["patterns_json"]), "skills": json.loads(row["skills_json"]), "size": int(row["size"])}

    FACT_SQL = (
        "INSERT INTO problem_fact(problem_id, spec, patterns_json, skills_json, size, level, tags_json) VALUES(?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(problem_id) DO UPDATE SET spec=excluded.spec, patterns_json=excluded.patterns_json, "
        "skills_json=excluded.skills_json, size=excluded.size, level=excluded.level, tags_json=excluded.tags_json"
    )

    def put_fact(self, problem_id: str, spec: str, patterns: list[str], skills: list[str] = (), size: int = 0, level: int = 0, tags: list[str] = ()) -> None:
        self.conn.execute(self.FACT_SQL, (problem_id, spec, json.dumps(list(patterns), ensure_ascii=False), json.dumps(list(skills)), int(size), int(level), json.dumps(list(tags))))
        self.conn.commit()

    def labels(self) -> dict[str, dict]:
        """문항 → 분석이 붙인 단계와 태그 {level, tags}(뼈대를 뽑은 문항만). 문제 목록이 쓴다."""
        return {row["problem_id"]: {"level": int(row["level"]), "tags": json.loads(row["tags_json"])}
                for row in self.conn.execute("SELECT problem_id, level, tags_json FROM problem_fact").fetchall()}

    def _frequent_pitfalls(self, limit: int = 5) -> list[tuple[str, int]]:
        """여러 문항에 걸쳐 이 사용자가 밟은 함정(제출 → 함정 엣지를 모아 센다). 뜻이 겹치는 함정은 대표 id 하나로 합쳐 센다(PITFALL_GROUPS)."""
        counts: dict[str, list] = {}
        for row in self.conn.execute("SELECT pitfall, COUNT(*) AS n, MAX(at) AS last FROM pitfall_hit GROUP BY pitfall").fetchall():
            seen = counts.setdefault(PITFALL_GROUPS.get(row["pitfall"], row["pitfall"]), [0, ""])
            seen[0], seen[1] = seen[0] + int(row["n"]), max(seen[1], row["last"] or "")
        return [(pid, n) for pid, (n, _) in sorted(counts.items(), key=lambda item: tuple(item[1]), reverse=True)][:limit]  # 많은 것, 같으면 최근 것 먼저

    def learner_level(self) -> str:
        """눈높이: 통과한 문항 수(solved)와 첫 제출 통과율(first). 도구가 없어 못 돌린 제출(toolchain_missing)은 세지 않는다."""
        rows = self.conn.execute("SELECT problem_id, ok FROM submission WHERE status!='toolchain_missing' ORDER BY rowid").fetchall()
        first: dict[str, bool] = {}
        for row in rows:
            first.setdefault(row["problem_id"], bool(row["ok"]))
        solved = len({row["problem_id"] for row in rows if row["ok"]})
        if solved < 5:
            return "beginner"
        return "advanced" if solved >= 25 and sum(first.values()) / len(first) >= 0.5 else "middle"

    def _solved(self, problem_id: str) -> dict[str, int]:
        """유형마다 통과한 다른 문항 수."""
        rows = self.conn.execute(
            "SELECT s.plan_json FROM tutor_session s WHERE s.problem_id!=? AND s.plan_json IS NOT NULL "
            "AND EXISTS (SELECT 1 FROM submission b WHERE b.problem_id=s.problem_id AND b.ok=1)", (problem_id,)
        ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            key = json.loads(row["plan_json"]).get("algorithm") or ""
            if key:
                counts[key] = counts.get(key, 0) + 1
        return counts

    def _block_states(self, problem_id: str) -> dict[str, BlockState]:
        rows = self.conn.execute(
            "SELECT * FROM block_state WHERE problem_id=?", (problem_id,)
        ).fetchall()
        return {
            row["block_id"]: BlockState(
                block_id=row["block_id"],
                code=row["code"],
                code_hash=row["code_hash"],
                verdict=row["verdict"],
                miss=row["miss"],
                tries=row["tries"],
                renames=json.loads(row["renames_json"]),
            )
            for row in rows
        }

    def _main_messages(self, problem_id: str, mode: str) -> list[ChatMessage]:
        rows = self.conn.execute(
            "SELECT * FROM message WHERE problem_id=? AND mode=? AND thread='main' ORDER BY id",
            (problem_id, mode),
        ).fetchall()
        return [_message(row) for row in rows]

    def _followups(self, problem_id: str) -> list[FollowupThread]:
        rows = self.conn.execute(
            "SELECT * FROM message WHERE problem_id=? AND thread LIKE 'quote:%' ORDER BY id",
            (problem_id,),
        ).fetchall()
        grouped: dict[str, list[ChatMessage]] = {}
        for row in rows:
            grouped.setdefault(row["quote_id"], []).append(_message(row))
        return [FollowupThread(quote_id=key, messages=value) for key, value in grouped.items()]

    def save_success(
        self,
        ctx: TutorContext,
        plan: BlockPlan | None,
        open_count: int,
        explain: Explain | None,
        messages: list[dict],
        feedback_body: dict | None,
        new_plan: bool = False,
        block_check: BlockState | list[BlockState] | None = None,
        debug_state: DebugState | None = None,
        fact: dict | None = None,
        solution: Solution | None = None,
        own_solution: bool = False,
    ) -> None:
        """요청 하나 = 트랜잭션 하나. 중간에 실패하면 모두 되돌린다."""
        with self.conn:
            if new_plan:
                # 블록 id는 계획마다 b1부터 다시 쓴다. 예전 계획의 블록 상태가 섞이지 않게 지운다.
                self.conn.execute("DELETE FROM block_state WHERE problem_id=?", (ctx.problem_id,))
            for item in (block_check if isinstance(block_check, list) else [block_check] if block_check is not None else []):
                self.conn.execute(
                    "INSERT INTO block_state(problem_id, block_id, code, code_hash, verdict, miss, tries, at, renames_json) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(problem_id, block_id) DO UPDATE SET "
                    "code=excluded.code, code_hash=excluded.code_hash, verdict=excluded.verdict, "
                    "miss=excluded.miss, tries=excluded.tries, at=excluded.at, renames_json=excluded.renames_json",
                    (
                        ctx.problem_id,
                        item.block_id,
                        item.code,
                        item.code_hash,
                        item.verdict,
                        item.miss,
                        item.tries,
                        now(),
                        json.dumps(item.renames, ensure_ascii=False),
                    ),
                )
            self.conn.execute(
                "INSERT INTO tutor_session(problem_id, plan_json, open_count, explain_json) "
                "VALUES(?, ?, ?, ?) ON CONFLICT(problem_id) DO UPDATE SET "
                "plan_json=excluded.plan_json, open_count=excluded.open_count, "
                "explain_json=excluded.explain_json",
                (ctx.problem_id, plan_to_json(plan), open_count, explain_to_json(explain)),
            )
            for item in messages:
                self.conn.execute(
                    "INSERT INTO message(problem_id, mode, thread, quote_id, block_index, role, text, at, move) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ctx.problem_id,
                        item["mode"],
                        item["thread"],
                        item.get("quote_id"),
                        item.get("block_index"),
                        item["role"],
                        item["text"],
                        item["at"],
                        item.get("move"),
                    ),
                )
            if new_plan:  # 새 계획이 사용자 방법을 따르면 그 가이드를 계획 옆에 두고, 정석 계획이면 비운다(정석 가이드를 본다)
                self.conn.execute("UPDATE tutor_session SET solution_json=? WHERE problem_id=?",
                                  (json.dumps(asdict(solution), ensure_ascii=False) if solution is not None and own_solution else None, ctx.problem_id))
            if solution is not None and not own_solution:
                self.conn.execute(
                    "INSERT INTO solution(problem_id, approach, steps_json, code, verified, clues_json) VALUES(?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(problem_id) DO UPDATE SET approach=excluded.approach, steps_json=excluded.steps_json, "
                    "code=excluded.code, verified=excluded.verified, clues_json=excluded.clues_json",
                    (ctx.problem_id, solution.approach, json.dumps(solution.steps, ensure_ascii=False), solution.code, VERIFIED_STATES.index(solution.verified),
                     json.dumps(solution.clues, ensure_ascii=False)),
                )
            if fact is not None:
                self.conn.execute(self.FACT_SQL, (ctx.problem_id, fact["spec"], json.dumps(fact["patterns"], ensure_ascii=False),
                                                  json.dumps(fact.get("skills") or []), int(fact.get("size") or 0), int(fact.get("level") or 0),
                                                  json.dumps(fact.get("tags") or [])))
            if debug_state is not None:
                d = debug_state
                self.conn.execute(
                    "INSERT INTO debug_state(problem_id, code_hash, kind, line, cause, fixed_line, step, pitfall) "
                    "VALUES(?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(problem_id) DO UPDATE SET code_hash=excluded.code_hash, "
                    "kind=excluded.kind, line=excluded.line, cause=excluded.cause, fixed_line=excluded.fixed_line, "
                    "step=excluded.step, pitfall=excluded.pitfall",
                    (ctx.problem_id, d.code_hash, d.kind, d.line, d.cause, d.fixed_line, d.step, d.pitfall),
                )
                if d.pitfall:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO pitfall_hit(problem_id, pitfall, code_hash, at) VALUES(?, ?, ?, ?)",
                        (ctx.problem_id, d.pitfall, d.code_hash, now()),
                    )
            if feedback_body is not None:
                self.conn.execute(
                    "INSERT INTO feedback(problem_id, submission_id, body_json) VALUES(?, ?, ?) "
                    "ON CONFLICT(problem_id) DO UPDATE SET "
                    "submission_id=excluded.submission_id, body_json=excluded.body_json",
                    (
                        ctx.problem_id,
                        feedback_body["submission_id"],
                        json.dumps(feedback_body, ensure_ascii=False),
                    ),
                )

    def get_feedback(self, problem_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT body_json FROM feedback WHERE problem_id=?", (problem_id,)
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["body_json"])

    def message_count(self, problem_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM message WHERE problem_id=?", (problem_id,)
        ).fetchone()
        return int(row["n"])


def _message(row: sqlite3.Row) -> ChatMessage:
    return ChatMessage(
        id=str(row["id"]),
        role=row["role"],
        text=row["text"],
        at=row["at"],
        block_index=row["block_index"],
        quote_id=row["quote_id"],
        move=row["move"],
    )
