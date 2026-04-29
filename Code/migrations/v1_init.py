from loguru import logger

from database.connection import DatabaseConnection

V1_INIT_VERSION = 1

V1_INIT_SQL = """
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    keywords TEXT NOT NULL,
    topics TEXT DEFAULT '[]',
    language TEXT DEFAULT '',
    min_stars INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 5,
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    url TEXT NOT NULL,
    homepage TEXT DEFAULT '',
    stars INTEGER DEFAULT 0,
    stars_growth INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    language TEXT DEFAULT '',
    topics TEXT DEFAULT '[]',
    readme_summary TEXT DEFAULT '',
    eval_score REAL DEFAULT 0.0,
    eval_details TEXT DEFAULT '{}',
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS match_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    match_score REAL NOT NULL,
    matched_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS summary_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT NOT NULL,
    repo_count INTEGER DEFAULT 0,
    candidate_count INTEGER DEFAULT 0,
    matched_count INTEGER DEFAULT 0,
    generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summary_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    rank INTEGER DEFAULT 0,
    FOREIGN KEY (summary_id) REFERENCES summary_logs(id) ON DELETE CASCADE,
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE RESTRICT
);

-- 索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_rules_name ON rules(name);
CREATE INDEX IF NOT EXISTS idx_rules_enabled ON rules(enabled);
CREATE UNIQUE INDEX IF NOT EXISTS idx_repositories_full_name ON repositories(full_name);
CREATE INDEX IF NOT EXISTS idx_repositories_fetched_at ON repositories(fetched_at);
CREATE INDEX IF NOT EXISTS idx_repositories_stars_growth ON repositories(stars_growth);
CREATE INDEX IF NOT EXISTS idx_repositories_eval_score ON repositories(eval_score);
CREATE INDEX IF NOT EXISTS idx_match_records_rule_id ON match_records(rule_id);
CREATE INDEX IF NOT EXISTS idx_match_records_repo_id ON match_records(repo_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_match_records_rule_repo ON match_records(rule_id, repo_id);
CREATE INDEX IF NOT EXISTS idx_summary_repos_summary_id ON summary_repos(summary_id);
CREATE INDEX IF NOT EXISTS idx_summary_repos_repo_id ON summary_repos(repo_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_summary_repos_summary_repo ON summary_repos(summary_id, repo_id);
CREATE INDEX IF NOT EXISTS idx_summary_logs_generated_at ON summary_logs(generated_at);
"""


def migrate(db: DatabaseConnection) -> None:
    """执行v1初始迁移：创建所有表和索引。"""
    conn = db.get_connection()
    try:
        conn.executescript(V1_INIT_SQL)
        logger.info("v1初始迁移完成：5张表和所有索引已创建")
    except Exception as e:
        logger.error(f"v1初始迁移失败: {e}")
        raise
