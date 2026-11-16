"""표 설계. 한 기기에 DB 파일 하나, setting을 뺀 모든 표가 problem_id로 나뉜다. 문항을 지우면 그 문항의 줄이 같이 지워진다."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS setting (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS problem (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '',
  language TEXT NOT NULL,
  body TEXT NOT NULL,
  direct_code TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS tutor_session (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  plan_json TEXT,
  open_count INTEGER NOT NULL DEFAULT 0,
  explain_json TEXT
);
CREATE TABLE IF NOT EXISTS message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  problem_id TEXT NOT NULL REFERENCES problem(id) ON DELETE CASCADE,
  mode TEXT NOT NULL,
  thread TEXT NOT NULL,
  quote_id TEXT,
  block_index INTEGER,
  role TEXT NOT NULL,
  text TEXT NOT NULL,
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS message_by_problem ON message(problem_id, mode, thread, id);
CREATE TABLE IF NOT EXISTS feedback (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  submission_id TEXT NOT NULL,
  body_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submission (
  id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL REFERENCES problem(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  ok INTEGER NOT NULL,
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS submission_by_problem ON submission(problem_id);
CREATE TABLE IF NOT EXISTS block_state (
  problem_id TEXT NOT NULL REFERENCES problem(id) ON DELETE CASCADE,
  block_id TEXT NOT NULL,
  code TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('Y', 'N')),
  miss INTEGER,
  tries INTEGER NOT NULL DEFAULT 1,
  at TEXT NOT NULL,
  PRIMARY KEY (problem_id, block_id)
);
"""

# user_version 순서대로 한 번씩 돈다. 바꿀 때는 뒤에 ALTER 문을 붙인다. 앞의 것은 고치지 않는다.
MIGRATIONS = [
    SCHEMA,
    # 2: 서비스 말의 질문 유형(open, clue, trace, assume, edge, basis, recap, blank, tool, shape, run, followup)
    "ALTER TABLE message ADD COLUMN move TEXT;",
    # 3: 디버그 진단, 문항 뼈대(명세·패턴), 함정 기록(제출 → 함정 엣지)
    """
CREATE TABLE IF NOT EXISTS debug_state (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,
  kind TEXT NOT NULL,
  line INTEGER NOT NULL,
  cause TEXT NOT NULL,
  fixed_line TEXT NOT NULL,
  step INTEGER NOT NULL DEFAULT 0,
  pitfall TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS problem_fact (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  spec TEXT NOT NULL,
  patterns_json TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS pitfall_hit (
  problem_id TEXT NOT NULL REFERENCES problem(id) ON DELETE CASCADE,
  pitfall TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  at TEXT NOT NULL,
  PRIMARY KEY (problem_id, pitfall, code_hash)
);
""",
    # 4: 문항 뼈대에 구현 기술과 입력 크기
    "ALTER TABLE problem_fact ADD COLUMN skills_json TEXT NOT NULL DEFAULT '[]'; ALTER TABLE problem_fact ADD COLUMN size INTEGER NOT NULL DEFAULT 0;",
    # 5: 풀이 가이드. solution은 문제마다 하나인 정석 가이드(단서, 방향, 단계, 정답 코드)이고,
    #    tutor_session.solution_json은 사용자 방법으로 다시 짠 계획이 따르는 가이드다(계획과 함께 지워진다)
    """
CREATE TABLE IF NOT EXISTS solution (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  approach TEXT NOT NULL,
  steps_json TEXT NOT NULL DEFAULT '[]',
  code TEXT NOT NULL,
  verified INTEGER NOT NULL DEFAULT 0,
  clues_json TEXT NOT NULL DEFAULT '[]'
);
ALTER TABLE tutor_session ADD COLUMN solution_json TEXT;
""",
    # 6: 제출에 언어와 결과 종류(학습 보고서가 약점을 가른다), 문제별 학습 기록(AI 없이 본 힌트와 해설)
    """
ALTER TABLE submission ADD COLUMN language TEXT NOT NULL DEFAULT 'python';
ALTER TABLE submission ADD COLUMN status TEXT NOT NULL DEFAULT '';
ALTER TABLE submission ADD COLUMN detail_json TEXT NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS study (
  problem_id TEXT PRIMARY KEY REFERENCES problem(id) ON DELETE CASCADE,
  hints_seen INTEGER NOT NULL DEFAULT 0,
  solution_at TEXT,
  solution_before_pass INTEGER NOT NULL DEFAULT 0
);
""",
    # 7: 블록이 이름 바꾸기 표에 더한 짝(블록 코드 확인이 사용자의 다른 블록 코드와 이어 돌 때 계획 코드의 이름을 바꾼다)
    "ALTER TABLE block_state ADD COLUMN renames_json TEXT NOT NULL DEFAULT '[]';",
    # 8: 판정 '?'(확인 전) — 앞 블록이 바뀌어 통과를 물린 블록, 다시 확인이 실패한 블록, 이어 돌려 통과하지 못한 채운 블록.
    # SQLite는 CHECK를 바꾸지 못해 표를 새로 만들어 옮긴다
    """
CREATE TABLE block_state_v8 (
  problem_id TEXT NOT NULL REFERENCES problem(id) ON DELETE CASCADE,
  block_id TEXT NOT NULL,
  code TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('Y', 'N', '?')),
  miss INTEGER,
  tries INTEGER NOT NULL DEFAULT 1,
  at TEXT NOT NULL,
  renames_json TEXT NOT NULL DEFAULT '[]',
  PRIMARY KEY (problem_id, block_id)
);
INSERT INTO block_state_v8(problem_id, block_id, code, code_hash, verdict, miss, tries, at, renames_json)
  SELECT problem_id, block_id, code, code_hash, verdict, miss, tries, at, renames_json FROM block_state;
DROP TABLE block_state;
ALTER TABLE block_state_v8 RENAME TO block_state;
""",
    # 9: 문항 뼈대에 분석이 붙인 단계(1~5, 모르면 0)와 태그(온톨로지 기법 id). 등록한 문제의 목록에 보인다
    "ALTER TABLE problem_fact ADD COLUMN level INTEGER NOT NULL DEFAULT 0; ALTER TABLE problem_fact ADD COLUMN tags_json TEXT NOT NULL DEFAULT '[]';",
    # 10: 도움(튜터 기능·힌트·해설)을 처음 쓴 시각, 마지막 '처음부터' 뒤에 처음 쓴 시각, 그 '처음부터'의 시각과 그때까지 본 힌트 수(학습 보고서가 도움 없이 푼 문제를 가린다).
    #     옛 행은 남은 기록으로 채운다: 대화가 있는 문항은 행을 만들고, 가장 이른 대화·해설 시각을 넣는다. 본 힌트는 시각이 없어 가장 이른 시각으로 둔다(통과 전에 본 것으로 친다)
    """
ALTER TABLE study ADD COLUMN help_first_at TEXT;
ALTER TABLE study ADD COLUMN help_after_reset_at TEXT;
ALTER TABLE study ADD COLUMN reset_at TEXT;
ALTER TABLE study ADD COLUMN hints_at_reset INTEGER NOT NULL DEFAULT 0;
INSERT OR IGNORE INTO study(problem_id) SELECT DISTINCT problem_id FROM message;
UPDATE study SET help_first_at = CASE
  WHEN hints_seen > 0 THEN '0001-01-01T00:00:00+00:00'
  WHEN solution_at IS NULL THEN (SELECT MIN(at) FROM message WHERE message.problem_id = study.problem_id)
  ELSE MIN(solution_at, COALESCE((SELECT MIN(at) FROM message WHERE message.problem_id = study.problem_id), solution_at)) END;
UPDATE study SET help_after_reset_at = help_first_at;
""",
    # 11: 디버그 진단이 고른 언어 함정(피드백이 이어 받는다)
    "ALTER TABLE debug_state ADD COLUMN trap TEXT NOT NULL DEFAULT '';",
]


def migrate(conn: sqlite3.Connection) -> None:
    """남은 버전을 한 트랜잭션으로 옮긴다. 쓰기 잠금을 먼저 잡으므로 두 연결이 새 파일을 동시에 열어도 한쪽만 옮기고,
    다른 쪽은 기다렸다가 이미 끝난 버전을 본다(잠금 없이는 둘 다 버전 0을 보고 같은 ALTER를 두 번 돌려 파일이 영영 안 열렸다)."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
            for statement in script.split(";"):  # executescript는 트랜잭션을 끊으므로 문장을 하나씩 돌린다(문장 안에 ;가 없다)
                if statement.strip():
                    conn.execute(statement)
            conn.execute(f"PRAGMA user_version={number}")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
