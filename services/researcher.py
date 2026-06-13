import requests
from bs4 import BeautifulSoup
from models.schemas import ResearchData, ProspectInput
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def research_company(prospect: ProspectInput) -> ResearchData:
    research = ResearchData(company_name=prospect.company_name)

    if not prospect.company_website:
        logger.info(f"No website provided for {prospect.company_name}, skipping research.")
        return research

    try:
        logger.info(f"Researching {prospect.company_website}")

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SDR-Research-Bot/1.0)"
        }

        response = requests.get(
            prospect.company_website,
            headers=headers,
            timeout=settings.RESEARCH_TIMEOUT
        )
        response.raise_for_status()

        research.raw_text = _parse_website(response.text)
        research.description = _extract_description(response.text)
        research.research_successful = True

        logger.info(f"Research successful for {prospect.company_name}")

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout researching {prospect.company_website}")
        research.error_message = "Website took too long to respond"

    except requests.exceptions.ConnectionError:
        logger.warning(f"Cannot connect to {prospect.company_website}")
        research.error_message = "Could not connect to website"

    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error for {prospect.company_website}")
        research.error_message = "Website returned an error"

    except Exception as e:
        logger.error(f"Unexpected research error: {e}", exc_info=True)
        research.error_message = "Unexpected error during research"

    return research


def _parse_website(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header",
                      "aside", "form", "button"]):
        tag.decompose()

    content_tags = soup.find_all(
        ["p", "h1", "h2", "h3", "li", "span"],
        limit=50
    )

    text_parts = []
    for tag in content_tags:
        text = tag.get_text(separator=" ", strip=True)
        if len(text) > 30:
            text_parts.append(text)

    combined = " ".join(text_parts)
    return combined[:settings.MAX_RESEARCH_CHARS]


def _extract_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"][:300]

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"][:300]

    return ""