"""
Configuracoes centralizadas - todas as env vars do projeto.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# === Riot API ===
RIOT_API_KEY = os.getenv("RIOT_API_KEY", "")

# === AI ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# === Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# === Backend ===
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
APP_TOKEN = os.getenv("APP_TOKEN", "")
INTERNAL_BEARER_TOKEN = os.getenv("INTERNAL_BEARER_TOKEN", "")
LOCAL_APP_TOKEN = os.getenv("LOCAL_APP_TOKEN", "").strip()
PUBLIC_READ_ONLY = _env_bool("PUBLIC_READ_ONLY", default=ENVIRONMENT == "production")
RENDER_BACKEND_URL = os.getenv("RENDER_BACKEND_URL", "https://lol-coach-backend-z4b7.onrender.com")
CORS_ORIGINS = _env_csv(
    "CORS_ORIGINS",
    "https://mvpgg.vercel.app,https://lol-coach-frontend.vercel.app,http://localhost:5173",
)
REQUIRE_HTTPS = _env_bool("REQUIRE_HTTPS", default=ENVIRONMENT == "production")
TRUST_X_FORWARDED_PROTO = _env_bool("TRUST_X_FORWARDED_PROTO", default=True)
REQUIRE_RIOT_ID_FOR_COACHING = _env_bool("REQUIRE_RIOT_ID_FOR_COACHING", default=True)
PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("PUBLIC_READ_RATE_LIMIT_WINDOW_SECONDS", "60"))
PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("PUBLIC_READ_RATE_LIMIT_MAX_REQUESTS", "60"))
REFRESH_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("REFRESH_RATE_LIMIT_WINDOW_SECONDS", "120"))
REFRESH_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("REFRESH_RATE_LIMIT_MAX_REQUESTS", "6"))
REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_RATE_LIMIT_PREFIX = os.getenv("REDIS_RATE_LIMIT_PREFIX", "projectb:rl").strip() or "projectb:rl"
EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("EDGE_CLIENT_RATE_LIMIT_WINDOW_SECONDS", "60"))
EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS = int(os.getenv("EDGE_CLIENT_RATE_LIMIT_MAX_REQUESTS", "120"))
EDGE_CLIENT_ID_HEADERS = _env_csv("EDGE_CLIENT_ID_HEADERS", "X-API-Key,X-Client-ID")
MAX_IDS_PER_STATUS_QUERY = int(os.getenv("MAX_IDS_PER_STATUS_QUERY", "50"))
MAX_MATCH_ID_LENGTH = int(os.getenv("MAX_MATCH_ID_LENGTH", "80"))
MAX_RIOT_ID_LENGTH = int(os.getenv("MAX_RIOT_ID_LENGTH", "64"))
MAX_EVENTS_PER_UPLOAD = int(os.getenv("MAX_EVENTS_PER_UPLOAD", "120"))
MAX_MINIMAP_BASE64_LENGTH = int(os.getenv("MAX_MINIMAP_BASE64_LENGTH", "4000000"))

# === Webhooks ===
MAKE_FEEDBACK_WEBHOOK_URL = os.getenv("MAKE_FEEDBACK_WEBHOOK_URL", "")
DOWNLOAD_APP_URL = os.getenv("DOWNLOAD_APP_URL", "").strip()

# === Limites ===
DAILY_LIMIT = 20
