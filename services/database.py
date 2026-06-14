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

            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                company TEXT,
                linkedin_url TEXT,
                twitter_url TEXT,
                website TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generated_emails (
                id TEXT PRIMARY KEY,
                prospect_id TEXT NOT NULL,
                contact_id TEXT,
                subject_line TEXT NOT NULL,
                email_body TEXT NOT NULL,
                call_to_action TEXT,
                language TEXT DEFAULT 'English',
                word_count INTEGER,
                generation_time_ms INTEGER,
                model_used TEXT,
                status TEXT DEFAULT 'draft',
                is_deleted INTEGER DEFAULT 0,
                deleted_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (prospect_id) REFERENCES prospects(id)
            );

            CREATE TABLE IF NOT EXISTS email_tracking (
                id TEXT PRIMARY KEY,
                email_id TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                tracked_at TEXT NOT NULL,
                FOREIGN KEY (email_id) REFERENCES generated_emails(id)
            );

            CREATE TABLE IF NOT EXISTS replies (
                id TEXT PRIMARY KEY,
                email_id TEXT NOT NULL,
                reply_text TEXT NOT NULL,
                replied_at TEXT NOT NULL,
                sentiment TEXT,
                FOREIGN KEY (email_id) REFERENCES generated_emails(id)
            );

            CREATE INDEX IF NOT EXISTS idx_emails_prospect_id
                ON generated_emails(prospect_id);
            CREATE INDEX IF NOT EXISTS idx_emails_created_at
                ON generated_emails(created_at);
            CREATE INDEX IF NOT EXISTS idx_emails_status
                ON generated_emails(status);
            CREATE INDEX IF NOT EXISTS idx_emails_deleted
                ON generated_emails(is_deleted);
            CREATE INDEX IF NOT EXISTS idx_tracking_email_id
                ON email_tracking(email_id);
            CREATE INDEX IF NOT EXISTS idx_replies_email_id
                ON replies(email_id);
            CREATE INDEX IF NOT EXISTS idx_contacts_company
                ON contacts(company);
        """)
    logger.info("Database initialized with all tables")


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
        return True
    except Exception as e:
        logger.error(f"Failed to save prospect: {e}", exc_info=True)
        return False


def save_email(email: GeneratedEmail, language: str = "English") -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO generated_emails
                   (id, prospect_id, subject_line, email_body, call_to_action,
                    language, word_count, generation_time_ms, model_used,
                    status, is_deleted, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    email.id,
                    email.prospect_id,
                    email.subject_line,
                    email.email_body,
                    email.call_to_action,
                    language,
                    email.word_count,
                    email.generation_time_ms,
                    email.model_used,
                    "draft",
                    0,
                    email.created_at.isoformat(),
                )
            )
        return True
    except Exception as e:
        logger.error(f"Failed to save email: {e}", exc_info=True)
        return False


def get_recent_emails(limit: int = 50, include_deleted: bool = False) -> list:
    try:
        with get_connection() as conn:
            query = """
                SELECT e.id, e.subject_line, e.email_body, e.created_at,
                       e.status, e.language, e.word_count, e.is_deleted,
                       p.prospect_name, p.company_name, p.prospect_role
                FROM generated_emails e
                JOIN prospects p ON e.prospect_id = p.id
                WHERE e.is_deleted = ?
                ORDER BY e.created_at DESC
                LIMIT ?
            """
            rows = conn.execute(query, (1 if include_deleted else 0, limit)).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch emails: {e}", exc_info=True)
        return []


def update_email_status(email_id: str, status: str, notes: str = "") -> bool:
    """
    Updates email pipeline status.
    Status options: draft, sent, opened, replied, bounced
    """
    try:
        from datetime import datetime
        import uuid
        with get_connection() as conn:
            conn.execute(
                "UPDATE generated_emails SET status = ? WHERE id = ?",
                (status, email_id)
            )
            conn.execute(
                """INSERT INTO email_tracking (id, email_id, status, notes, tracked_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), email_id, status, notes, datetime.utcnow().isoformat())
            )
        return True
    except Exception as e:
        logger.error(f"Failed to update status: {e}", exc_info=True)
        return False


def soft_delete_email(email_id: str) -> bool:
    """Moves email to recycle bin without permanently deleting."""
    try:
        from datetime import datetime
        with get_connection() as conn:
            conn.execute(
                "UPDATE generated_emails SET is_deleted = 1, deleted_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), email_id)
            )
        return True
    except Exception as e:
        logger.error(f"Failed to delete email: {e}", exc_info=True)
        return False


def restore_email(email_id: str) -> bool:
    """Restores email from recycle bin."""
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE generated_emails SET is_deleted = 0, deleted_at = NULL WHERE id = ?",
                (email_id,)
            )
        return True
    except Exception as e:
        logger.error(f"Failed to restore email: {e}", exc_info=True)
        return False


def permanent_delete_email(email_id: str) -> bool:
    """Permanently deletes email from recycle bin."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM email_tracking WHERE email_id = ?", (email_id,))
            conn.execute("DELETE FROM replies WHERE email_id = ?", (email_id,))
            conn.execute("DELETE FROM generated_emails WHERE id = ?", (email_id,))
        return True
    except Exception as e:
        logger.error(f"Failed to permanently delete: {e}", exc_info=True)
        return False


def save_reply(email_id: str, reply_text: str, sentiment: str = "") -> bool:
    """Saves a reply received for a specific email."""
    try:
        from datetime import datetime
        import uuid
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO replies (id, email_id, reply_text, replied_at, sentiment)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), email_id, reply_text,
                 datetime.utcnow().isoformat(), sentiment)
            )
            conn.execute(
                "UPDATE generated_emails SET status = 'replied' WHERE id = ?",
                (email_id,)
            )
        return True
    except Exception as e:
        logger.error(f"Failed to save reply: {e}", exc_info=True)
        return False


def get_replies(email_id: str) -> list:
    """Gets all replies for a specific email."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM replies WHERE email_id = ? ORDER BY replied_at DESC",
                (email_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch replies: {e}", exc_info=True)
        return []


def get_email_tracking(email_id: str) -> list:
    """Gets full tracking history for an email."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM email_tracking
                   WHERE email_id = ? ORDER BY tracked_at ASC""",
                (email_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch tracking: {e}", exc_info=True)
        return []


def save_contact(contact: dict) -> bool:
    """Saves a new contact to the contacts table."""
    try:
        from datetime import datetime
        import uuid
        now = datetime.utcnow().isoformat()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO contacts
                   (id, full_name, email, phone, company,
                    linkedin_url, twitter_url, website, notes,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    contact.get("full_name", ""),
                    contact.get("email", ""),
                    contact.get("phone", ""),
                    contact.get("company", ""),
                    contact.get("linkedin_url", ""),
                    contact.get("twitter_url", ""),
                    contact.get("website", ""),
                    contact.get("notes", ""),
                    now, now
                )
            )
        return True
    except Exception as e:
        logger.error(f"Failed to save contact: {e}", exc_info=True)
        return False


def get_all_contacts() -> list:
    """Returns all saved contacts."""
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM contacts ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch contacts: {e}", exc_info=True)
        return []


def delete_contact(contact_id: str) -> bool:
    """Permanently deletes a contact."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        return True
    except Exception as e:
        logger.error(f"Failed to delete contact: {e}", exc_info=True)
        return False


def get_analytics_data() -> dict:
    """Returns aggregated analytics for the dashboard."""
    try:
        with get_connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM generated_emails WHERE is_deleted = 0"
            ).fetchone()[0]

            by_status = conn.execute(
                """SELECT status, COUNT(*) as count
                   FROM generated_emails WHERE is_deleted = 0
                   GROUP BY status"""
            ).fetchall()

            by_language = conn.execute(
                """SELECT language, COUNT(*) as count
                   FROM generated_emails WHERE is_deleted = 0
                   GROUP BY language ORDER BY count DESC"""
            ).fetchall()

            total_replies = conn.execute(
                "SELECT COUNT(*) FROM replies"
            ).fetchone()[0]

            total_contacts = conn.execute(
                "SELECT COUNT(*) FROM contacts"
            ).fetchone()[0]

            return {
                "total_emails": total,
                "by_status": [dict(r) for r in by_status],
                "by_language": [dict(r) for r in by_language],
                "total_replies": total_replies,
                "total_contacts": total_contacts,
                "reply_rate": round((total_replies / total * 100), 1) if total > 0 else 0
            }
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}", exc_info=True)
        return {}