import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Groq Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "llama-3.3-70b-versatile"  # Free Groq model
    OPENAI_MAX_TOKENS: int = 500
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = 1.0

    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DB_PATH: str = os.getenv("DB_PATH", "data/emails.db")

    # Email Constraints
    MAX_EMAIL_WORDS: int = 150
    MIN_EMAIL_WORDS: int = 80

    # Research
    RESEARCH_TIMEOUT: int = 10
    MAX_RESEARCH_CHARS: int = 2000

    @classmethod
    def validate(cls) -> None:
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "API key not found. "
                "Add your Groq key to the .env file as OPENAI_API_KEY=your-key"
            )

    @classmethod
    def is_production(cls) -> bool:
        return cls.APP_ENV == "production"


settings = Settings()