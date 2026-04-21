import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

_CONFIG_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CONFIG_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent

load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_PROJECT_ROOT / ".env.example")


@dataclass(frozen=True)
class Settings:
	app_name: str = os.getenv("APP_NAME", "AI Memory Doctor")
	environment: str = os.getenv("ENVIRONMENT", "development")
	debug: bool = os.getenv("DEBUG", "false").lower() == "true"
	database_url: str = os.getenv("DATABASE_URL", "sqlite:///./memory.db")
	jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_ENV")
	jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
	access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
	backend_port: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
	workers: int = int(os.getenv("WORKERS", "1"))
	cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
	allowed_hosts: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,*.onrender.com")
	timezone: str = os.getenv("TIMEZONE", "Africa/Addis_Ababa")
	date_format: str = os.getenv("DATE_FORMAT", "ISO")
	language: str = os.getenv("LANGUAGE", "English")
	admin_emails: str = os.getenv("ADMIN_EMAILS", "")
	embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
	llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
	llm_api_key: str = os.getenv("LLM_API_KEY", "")
	llm_model: str = os.getenv("LLM_MODEL", "models/gemini-2.0-flash")


def parse_csv_env(value: str) -> list[str]:
	return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()
