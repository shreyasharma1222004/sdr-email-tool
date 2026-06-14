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

LANGUAGE_INSTRUCTIONS = {
    # International
    "English": {
        "name": "English",
        "instruction": "Write the entire email in English.",
        "flag": "🇬🇧"
    },
    "Spanish": {
        "name": "Spanish",
        "instruction": "Write the entire email in Spanish (Español). Use natural, professional Spanish.",
        "flag": "🇪🇸"
    },
    "French": {
        "name": "French",
        "instruction": "Write the entire email in French (Français). Use natural, professional French.",
        "flag": "🇫🇷"
    },
    "German": {
        "name": "German",
        "instruction": "Write the entire email in German (Deutsch). Use natural, professional German.",
        "flag": "🇩🇪"
    },
    "Arabic": {
        "name": "Arabic",
        "instruction": "Write the entire email in Arabic (العربية). Use formal, professional Arabic.",
        "flag": "🇸🇦"
    },
    "Chinese": {
        "name": "Chinese",
        "instruction": "Write the entire email in Simplified Chinese (简体中文). Use professional business Chinese.",
        "flag": "🇨🇳"
    },
    "Japanese": {
        "name": "Japanese",
        "instruction": "Write the entire email in Japanese (日本語). Use keigo (敬語) formal business Japanese.",
        "flag": "🇯🇵"
    },

    # Indian Languages
    "Hindi": {
        "name": "Hindi",
        "instruction": "Write the entire email in Hindi (हिन्दी). Use professional and formal Hindi.",
        "flag": "🇮🇳"
    },
    "Bengali": {
        "name": "Bengali",
        "instruction": "Write the entire email in Bengali (বাংলা). Use professional and formal Bengali.",
        "flag": "🇮🇳"
    },
    "Tamil": {
        "name": "Tamil",
        "instruction": "Write the entire email in Tamil (தமிழ்). Use professional and formal Tamil.",
        "flag": "🇮🇳"
    },
    "Telugu": {
        "name": "Telugu",
        "instruction": "Write the entire email in Telugu (తెలుగు). Use professional and formal Telugu.",
        "flag": "🇮🇳"
    },
    "Marathi": {
        "name": "Marathi",
        "instruction": "Write the entire email in Marathi (मराठी). Use professional and formal Marathi.",
        "flag": "🇮🇳"
    },
    "Gujarati": {
        "name": "Gujarati",
        "instruction": "Write the entire email in Gujarati (ગુજરાતી). Use professional and formal Gujarati.",
        "flag": "🇮🇳"
    },
    "Kannada": {
        "name": "Kannada",
        "instruction": "Write the entire email in Kannada (ಕನ್ನಡ). Use professional and formal Kannada.",
        "flag": "🇮🇳"
    },
    "Malayalam": {
        "name": "Malayalam",
        "instruction": "Write the entire email in Malayalam (മലയാളം). Use professional and formal Malayalam.",
        "flag": "🇮🇳"
    },
    "Punjabi": {
        "name": "Punjabi",
        "instruction": "Write the entire email in Punjabi (ਪੰਜਾਬੀ). Use professional and formal Punjabi.",
        "flag": "🇮🇳"
    },
    "Odia": {
        "name": "Odia",
        "instruction": "Write the entire email in Odia (ଓଡ଼ିଆ). Use professional and formal Odia.",
        "flag": "🇮🇳"
    },
    "Urdu": {
        "name": "Urdu",
        "instruction": "Write the entire email in Urdu (اردو). Use professional and formal Urdu.",
        "flag": "🇵🇰"
    },
}

# All available languages for the UI dropdown
ALL_LANGUAGES = list(LANGUAGE_INSTRUCTIONS.keys())

# Grouped for display
INTERNATIONAL_LANGUAGES = [
    "English", "Spanish", "French", "German",
    "Arabic", "Chinese", "Japanese"
]

INDIAN_LANGUAGES = [
    "Hindi", "Bengali", "Tamil", "Telugu", "Marathi",
    "Gujarati", "Kannada", "Malayalam", "Punjabi", "Odia", "Urdu"
]


def build_prompt(
    prospect: ProspectInput,
    research: ResearchData,
    language: str = "English"
) -> tuple[str, str]:
    """
    Builds system and user prompts with language support.
    """
    tone_instruction = TONE_INSTRUCTIONS.get(
        prospect.tone, TONE_INSTRUCTIONS["friendly"]
    )

    lang_data = LANGUAGE_INSTRUCTIONS.get(
        language, LANGUAGE_INSTRUCTIONS["English"]
    )
    lang_instruction = lang_data["instruction"]

    system_prompt = f"""You are an elite Sales Development Representative (SDR) with 10+ years of experience writing cold emails that get replies across global markets.

TONE: {tone_instruction}

LANGUAGE: {lang_instruction}
IMPORTANT: The ENTIRE email including subject line, body, and CTA must be written in {language}. Do not mix languages.

STRICT OUTPUT RULES:
1. Your response MUST follow this exact format:
   SUBJECT: [your subject line]
   BODY: [your email body]
   CTA: [your call-to-action sentence]

2. Email body must be 80-150 words. No exceptions.
3. Subject line must be under 60 characters. No all-caps.
4. Never use spam trigger words.
5. Never start with generic openers.
6. Only use information provided. Do not invent facts.
7. The email must feel personally researched, not templated.
8. Include exactly one clear call-to-action.
9. Sign off naturally without a name.
10. Maintain cultural appropriateness for the {language} language and its business culture."""

    prospect_context = _build_prospect_context(prospect)
    research_context = _build_research_context(research)

    user_prompt = f"""Generate a personalized cold email in {language} for the following prospect.

PROSPECT INFORMATION:
{prospect_context}

{research_context}

Remember: Write everything in {language} only. Follow all formatting rules exactly."""

    logger.info(
        f"Prompt built | Prospect: {prospect.prospect_name} | "
        f"Tone: {prospect.tone} | Language: {language} | "
        f"Research: {research.research_successful}"
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
        lines.append(f"- Website Content: {research.raw_text[:500]}...")
    return "\n".join(lines)