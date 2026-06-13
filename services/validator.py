import re
from typing import Tuple
from models.schemas import ProspectInput
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_TONES = ["friendly", "formal", "direct", "consultative", "executive"]

MAX_NAME_LENGTH = 100
MAX_COMPANY_LENGTH = 100
MAX_ROLE_LENGTH = 100
MAX_NOTES_LENGTH = 500
MAX_LINKEDIN_LENGTH = 1000


def validate_prospect_input(data: dict):
    errors = []

    prospect_name = _sanitize_text(data.get("prospect_name", ""), MAX_NAME_LENGTH)
    company_name = _sanitize_text(data.get("company_name", ""), MAX_COMPANY_LENGTH)
    prospect_role = _sanitize_text(data.get("prospect_role", ""), MAX_ROLE_LENGTH)
    tone = data.get("tone", "").lower().strip()

    if not prospect_name:
        errors.append("Prospect name is required.")
    if not company_name:
        errors.append("Company name is required.")
    if not prospect_role:
        errors.append("Prospect role is required.")
    if tone not in VALID_TONES:
        errors.append(f"Tone must be one of: {', '.join(VALID_TONES)}.")

    company_website = data.get("company_website", "").strip()
    if company_website and not _is_valid_url(company_website):
        errors.append("Company website must be a valid URL (e.g., https://example.com).")

    linkedin_summary = _sanitize_text(
        data.get("linkedin_summary", ""), MAX_LINKEDIN_LENGTH
    )
    additional_notes = _sanitize_text(
        data.get("additional_notes", ""), MAX_NOTES_LENGTH
    )

    if errors:
        logger.warning(f"Validation failed: {errors}")
        return False, " | ".join(errors), None

    prospect = ProspectInput(
        prospect_name=prospect_name,
        company_name=company_name,
        prospect_role=prospect_role,
        tone=tone,
        company_website=company_website or None,
        linkedin_summary=linkedin_summary or None,
        additional_notes=additional_notes or None,
    )

    logger.info(f"Validation passed for prospect: {prospect_name} at {company_name}")
    return True, "", prospect


def _sanitize_text(text: str, max_length: int) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return cleaned.strip()[:max_length]


def _is_valid_url(url: str) -> bool:
    pattern = re.compile(
        r'^https?://'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
        r'+[A-Z]{2,6}'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return bool(pattern.match(url))