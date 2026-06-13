import csv
import io
from models.schemas import GeneratedEmail, ProspectInput
from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_csv(prospect: ProspectInput, email: GeneratedEmail) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Prospect Name", "Company", "Role", "Tone",
        "Subject Line", "Email Body", "CTA",
        "Word Count", "Generated At"
    ])

    writer.writerow([
        prospect.prospect_name,
        prospect.company_name,
        prospect.prospect_role,
        prospect.tone,
        email.subject_line,
        email.email_body,
        email.call_to_action,
        email.word_count,
        email.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    ])

    return output.getvalue().encode("utf-8")


def export_to_txt(prospect: ProspectInput, email: GeneratedEmail) -> bytes:
    content = f"""SDR Email Generator — Export
Generated: {email.created_at.strftime("%Y-%m-%d %H:%M:%S")}
{'='*50}

PROSPECT: {prospect.prospect_name}
COMPANY:  {prospect.company_name}
ROLE:     {prospect.prospect_role}
TONE:     {prospect.tone.capitalize()}

{'='*50}
SUBJECT:
{email.subject_line}

BODY:
{email.email_body}

CALL TO ACTION:
{email.call_to_action}
{'='*50}
Word Count: {email.word_count}
"""
    return content.encode("utf-8")