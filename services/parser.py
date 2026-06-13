import re
from models.schemas import GeneratedEmail
from utils.logger import get_logger

logger = get_logger(__name__)


def parse_email_response(raw_response: str, prospect_id: str = None) -> GeneratedEmail:
    logger.info("Parsing AI response")

    try:
        subject = _extract_section(raw_response, "SUBJECT")
        body = _extract_section(raw_response, "BODY")
        cta = _extract_section(raw_response, "CTA")

        if not subject:
            subject = _extract_subject_fallback(raw_response)
            logger.warning("Used subject fallback extraction")

        if not body:
            body = _extract_body_fallback(raw_response)
            logger.warning("Used body fallback extraction")

        subject = _clean_text(subject)
        body = _clean_text(body)
        cta = _clean_text(cta)

        email = GeneratedEmail(
            subject_line=subject or "Let's connect",
            email_body=body or raw_response.strip(),
            call_to_action=cta,
            prospect_id=prospect_id,
        )

        logger.info(f"Parse successful | Word count: {email.word_count}")
        return email

    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        return GeneratedEmail(
            subject_line="(Could not parse subject)",
            email_body=raw_response.strip(),
            call_to_action="",
            prospect_id=prospect_id,
        )


def _extract_section(text: str, label: str) -> str:
    pattern = rf'{label}:\s*(.*?)(?=\n(?:SUBJECT|BODY|CTA):|$)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()
    return ""


def _extract_subject_fallback(text: str) -> str:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        for line in lines[:3]:
            if len(line) < 100:
                return line
    return ""


def _extract_body_fallback(text: str) -> str:
    return text.strip()


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()