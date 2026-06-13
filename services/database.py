import sqlite3
from pathlib import Path
from models.schemas import ProspectInput, GeneratedEmail
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def get_connection() -> sqlite3.Connection:
    db_path = Path(settings.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS prospects (
                id TEXT PRIMARY KEY,
                prospect_name TEXT NOT NULL,
                company_name TEXT NOT NULL,
                prospect_role TEXT NOT NULL,
                tone TEXT NOT NULL,
                company_website TEXT,
                linkedin_summary TEXT,
                additional_notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generated_emails (
                id TEXT PRIMARY KEY,
                prospect_id TEXT NOT NULL,
                subject_line TEXT NOT NULL,
                email_body TEXT NOT NULL,
                call_to_action TEXT,
                word_count INTEGER,
                generation_time_ms INTEGER,
                model_used TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (prospect_id) REFERENCES prospects(id)
            );

            CREATE INDEX IF NOT EXISTS idx_emails_prospect_id
                ON generated_emails(prospect_id);
            CREATE INDEX IF NOT EXISTS idx_emails_created_at
                ON generated_emails(created_at);
        """)
    logger.info("Database initialized")


def save_prospect(prospect: ProspectInput) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO prospects
                   (id, prospect_name, company_name, prospect_role, tone,
                    company_website, linkedin_summary, additional_notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    prospect.id,
                    prospect.prospect_name,
                    prospect.company_name,
                    prospect.prospect_role,
                    prospect.tone,
                    prospect.company_website,
                    prospect.linkedin_summary,
                    prospect.additional_notes,
                    prospect.created_at.isoformat(),
                )
            )
        logger.info(f"Saved prospect: {prospect.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save prospect: {e}", exc_info=True)
        return False


def save_email(email: GeneratedEmail) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO generated_emails
                   (id, prospect_id, subject_line, email_body, call_to_action,
                    word_count, generation_time_ms, model_used, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    email.id,
                    email.prospect_id,
                    email.subject_line,
                    email.email_body,
                    email.call_to_action,
                    email.word_count,
                    email.generation_time_ms,
                    email.model_used,
                    email.created_at.isoformat(),
                )
            )
        logger.info(f"Saved email: {email.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save email: {e}", exc_info=True)
        return False


def get_recent_emails(limit: int = 10) -> list:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT e.id, e.subject_line, e.email_body, e.created_at,
                          p.prospect_name, p.company_name
                   FROM generated_emails e
                   JOIN prospects p ON e.prospect_id = p.id
                   ORDER BY e.created_at DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch recent emails: {e}", exc_info=True)
        return []