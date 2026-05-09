"""
Project settings and configuration.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'google/gemma-4-31b-it:free')

# Comma-separated list of fallback models tried in order when the primary is unavailable
_fallback_raw = os.getenv('OPENROUTER_FALLBACK_MODELS', '')
OPENROUTER_FALLBACK_MODELS: list[str] = [m.strip() for m in _fallback_raw.split(',') if m.strip()]

if not OPENROUTER_API_KEY:
    print("AVISO: OPENROUTER_API_KEY não está definida. As funcionalidades de IA estarão indisponíveis.")


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_hex(32)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = UPLOAD_FOLDER
