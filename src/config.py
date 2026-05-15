import os
from zoneinfo import ZoneInfo

# Core Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Tavily (for crawling)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Verifier Config
VERIFIER_FROM_EMAIL = os.getenv("VERIFIER_FROM_EMAIL", "verify@echotray.ai")
VERIFIER_PASS_THRESHOLD = int(os.getenv("VERIFIER_PASS_THRESHOLD", "75"))

# App Context
UTM_CAMPAIGN = os.getenv("UTM_CAMPAIGN", "personalize_verify_app")
TZ_ET = ZoneInfo("America/New_York")

# Thresholds for Personalization
SIGNAL_MAX_AGE_DAYS = int(os.getenv("SIGNAL_MAX_AGE_DAYS", "45"))
ICP_FIT_THRESHOLD = float(os.getenv("ICP_FIT_THRESHOLD", "0.6"))
