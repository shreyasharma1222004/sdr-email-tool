from models.schemas import ProspectInput, ResearchData
from utils.logger import get_logger

logger = get_logger(__name__)

TONE_INSTRUCTIONS = {
    "friendly": (
        "Write in a warm, approachable, conversational tone. "
        "Sound like a helpful colleague, not a salesperson. "
        "Use contractions naturally. Be genuinely human."
    ),
    "formal": (
        "Write in a professional, polished, formal tone. "
        "Avoid contractions. Use complete sentences. "
        "Sound like a respected business professional."
    ),
    "direct": (
        "Write in a concise, confident, no-fluff tone. "
        "Get to the point immediately. Respect their time. "
        "Every sentence must earn its place."
    ),
    "consultative": (
        "Write in an empathetic, problem-aware, expert tone. "
        "Show you understand their challenges before offering solutions. "
        "Sound like a trusted advisor, not a vendor."
    ),
    "executive": (
        "Write in a high-level, strategic, peer-to-peer tone. "
        "Focus on business outcomes and ROI, not features. "
        "Sound like you're addressing a C-suite leader as an equal."
    )
}


def build_prompt(prospect: ProspectInput, research: ResearchData):
    tone_instruction = TONE_INSTRUCTIONS.get(
        prospect.tone, TONE_INSTRUCTIONS["friendly"]
    )

    system_prompt = f"""You are an elite Sales Development Representative (SDR) with 10+ years of experience writing cold emails that get replies.

TONE: {tone_instruction}

STRICT OUTPUT RULES:
1. Your response MUST follow this exact format:
   SUBJECT: [your subject line]
   BODY: [your email body]
   CTA: [your call-to-action sentence]

2. Email body must be 80-150 words. No exceptions.
3. Subject line must be under 60 characters. No all-caps.
4. Never use these words: guaranteed, free, urgent, act now, limited time.
5. Never start with "I hope this email finds you well".
6. Only use information provided. Do not invent facts.
7. The email must feel personally researched, not templated.
8. Include exactly one clear call-to-action.
9. Sign off naturally without a name."""

    prospect_context = _build_prospect_context(prospect)
    research_context = _build_research_context(research)

    user_prompt = f"""Generate a personalized cold email for the following prospect.

PROSPECT INFORMATION:
{prospect_context}

{research_context}

Generate the email now following all formatting rules exactly."""

    logger.info(
        f"Prompt built for {prospect.prospect_name} | "
        f"Tone: {prospect.tone} | "
        f"Research available: {research.research_successful}"
    )

    return system_prompt, user_prompt


def _build_prospect_context(prospect: ProspectInput) -> str:
    lines = [
        f"- Name: {prospect.prospect_name}",
        f"- Role: {prospect.prospect_role}",
        f"- Company: {prospect.company_name}",
    ]

    if prospect.company_website:
        lines.append(f"- Company Website: {prospect.company_website}")

    if prospect.linkedin_summary:
        lines.append(f"- LinkedIn Summary: {prospect.linkedin_summary}")

    if prospect.additional_notes:
        lines.append(f"- Additional Context: {prospect.additional_notes}")

    return "\n".join(lines)


def _build_research_context(research: ResearchData) -> str:
    if not research.research_successful:
        return ""

    lines = ["COMPANY INTELLIGENCE (from website research):"]

    if research.description:
        lines.append(f"- Company Description: {research.description}")

    if research.raw_text:
        lines.append(f"- Website Content Summary: {research.raw_text[:500]}...")

    return "\n".join(lines)