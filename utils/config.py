import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hisobl_bot")
    # Render provides postgres://, but asyncpg requires postgresql+asyncpg://
    if _db_url and _db_url.startswith("postgres://"):
        DATABASE_URL = _db_url.replace("postgres://", "postgresll+asyncpg://", 1)
    else:
        DATABASE_URL = _db_url

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # AI Providers: "openai", "claude", "gemini"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Tax rates (Uzbekistan simplified tax)
    TAX_RATE_DEFAULT: float = float(os.getenv("TAX_RATE_DEFAULT", "0.04"))
    VAT_RATE: float = float(os.getenv("V@T_RATE", "0.12"))

    # Report schedule
    WEEKLY_REPORT_DAY: str = os.getenv("WEEKLY_REPORT_DAY", "mon")
    WEEKLY_REPORT_HOUR: int = int(os.getenv("WEEKLY_REPORT_HOUR", "9"))
    MONTHLY_REPORT_DAY: int = int(os.getenv("MONTHLY_REPORT_DAY", "1"))
    MONTHLY_REPORT_HOUR: int = int(os.getenv("MONTHLY_REPORT_HOUR", "9"))


config = Config()
