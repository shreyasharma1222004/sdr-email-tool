import time
from groq import Groq
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_client = Groq(api_key=settings.OPENAI_API_KEY)


def generate_email(system_prompt: str, user_prompt: str) -> str:
    last_exception = None

    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            logger.info(f"Groq request attempt {attempt}/{settings.MAX_RETRIES}")

            start_time = time.time()

            response = _client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content

            logger.info(
                f"Groq success | "
                f"Tokens used: {response.usage.total_tokens} | "
                f"Time: {elapsed_ms}ms"
            )

            return content

        except Exception as e:
            wait_time = settings.RETRY_DELAY * attempt
            logger.warning(f"Attempt {attempt} failed: {e}. Waiting {wait_time}s.")
            last_exception = e
            time.sleep(wait_time)

    logger.error(f"All {settings.MAX_RETRIES} attempts failed.")
    raise last_exception