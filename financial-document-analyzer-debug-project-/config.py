"""Application configuration from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM: use OPENAI_API_KEY + model, or GOOGLE_API_KEY for Gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # or gemini/gemini-pro

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_analyzer.db")

# Redis / Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)

# App
DATA_DIR = os.getenv("DATA_DIR", "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
