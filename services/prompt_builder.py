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
# ── OUTREACH SUITE PROMPTS ──────────────────────────────────

def build_whatsapp_prompt(prospect: ProspectInput, language: str = "English") -> tuple[str, str]:
    """Builds prompt for WhatsApp outreach message."""
    lang_data = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    system_prompt = f"""You are an expert sales professional writing WhatsApp outreach messages.

LANGUAGE: {lang_data["instruction"]}

RULES:
1. Format must be exactly:
   MESSAGE: [your whatsapp message]

2. Message must be 50-80 words maximum
3. Must sound casual and conversational — this is WhatsApp not email
4. Use simple language — no corporate jargon
5. Include one clear question or CTA at the end
6. Never use bullet points or formal structure
7. Sound like a real person texting, not a bot
8. No subject line needed — just the message"""

    user_prompt = f"""Write a WhatsApp outreach message for:
- Name: {prospect.prospect_name}
- Role: {prospect.prospect_role}
- Company: {prospect.company_name}

Write in {language}. Keep it casual, short, and human."""

    return system_prompt, user_prompt


def build_linkedin_prompt(
    prospect: ProspectInput,
    message_type: str = "connection",
    language: str = "English"
) -> tuple[str, str]:
    """
    Builds prompt for LinkedIn messages.
    message_type: 'connection' or 'dm'
    """
    lang_data = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    if message_type == "connection":
        rules = """
2. Must be under 300 characters — LinkedIn connection request limit
3. Sound genuine and specific — not copy-paste
4. Mention something specific about their role or company
5. Do not pitch anything — just a warm connection request
6. End with a simple reason to connect"""
        word_limit = "under 50 words"
    else:
        rules = """
2. Must be 100-150 words
3. Reference that you are already connected
4. Lead with value — what's in it for them
5. One clear CTA at the end
6. Sound like a peer not a vendor"""
        word_limit = "100-150 words"

    system_prompt = f"""You are an expert at LinkedIn outreach writing {word_limit} messages.

LANGUAGE: {lang_data["instruction"]}

RULES:
1. Format must be exactly:
   MESSAGE: [your linkedin message]
{rules}"""

    user_prompt = f"""Write a LinkedIn {message_type} request message for:
- Name: {prospect.prospect_name}
- Role: {prospect.prospect_role}
- Company: {prospect.company_name}

Write in {language}."""

    return system_prompt, user_prompt


def build_cold_call_prompt(prospect: ProspectInput, language: str = "English") -> tuple[str, str]:
    """Builds prompt for cold call script."""
    lang_data = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    system_prompt = f"""You are an expert sales trainer writing cold call scripts.

LANGUAGE: {lang_data["instruction"]}

RULES:
1. Format must be exactly:
   OPENER: [first 10 seconds — introduce yourself]
   HOOK: [the reason for calling — pain point or opportunity]
   PITCH: [15 second value proposition]
   QUESTION: [one open-ended discovery question]
   CTA: [ask for the meeting]
   OBJECTION: [handle the most likely objection]

2. Total script should take 60-90 seconds to read aloud
3. Sound natural and conversational
4. Use the prospect's name and company name
5. Never sound like you're reading from a script"""

    user_prompt = f"""Write a cold call script for:
- Prospect: {prospect.prospect_name}
- Role: {prospect.prospect_role}
- Company: {prospect.company_name}

Write in {language}."""

    return system_prompt, user_prompt


def build_followup_prompt(
    prospect: ProspectInput,
    original_email: str,
    followup_number: int = 1,
    language: str = "English"
) -> tuple[str, str]:
    """Builds follow-up email prompts with different angles."""
    lang_data = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["English"])

    angles = {
        1: "Add new value — share a relevant insight, stat, or case study they haven't heard",
        2: "Create urgency — reference timing, a trend, or a recent development in their industry",
        3: "Break-up email — acknowledge they're busy, make it easy to say no or yes, keep it 3 sentences max"
    }

    angle = angles.get(followup_number, angles[1])

    system_prompt = f"""You are an elite SDR writing follow-up emails.

LANGUAGE: {lang_data["instruction"]}

FOLLOW-UP #{followup_number} ANGLE: {angle}

RULES:
1. Format must be exactly:
   SUBJECT: [subject line — reference original or use pattern interrupt]
   BODY: [follow-up email body]
   CTA: [call to action]

2. Must be 50-80 words — shorter than original
3. Never repeat what was said in the original email
4. Must feel fresh and add new value
5. Reference that this is a follow-up naturally"""

    user_prompt = f"""Write follow-up #{followup_number} for:
- Prospect: {prospect.prospect_name}
- Role: {prospect.prospect_role}
- Company: {prospect.company_name}

Original email sent:
{original_email[:500]}

Write in {language}. Use the angle specified."""

    return system_prompt, user_prompt