# config.py
import os
import logging
import tempfile
import platform
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = tempfile.gettempdir()

# Server configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))
HOST = os.getenv('HOST', '0.0.0.0')
SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())

# API keys
OPENAI_API_KEY ="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"    #OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key")
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Storage limits
MAX_HISTORY_ITEMS = int(os.getenv('MAX_HISTORY_ITEMS', 1000))
MAX_RESULT_SIZE = int(os.getenv('MAX_RESULT_SIZE', 10 * 1024 * 1024))  # 10MB

# Agent configuration
DEFAULT_CHECK_INTERVAL = int(os.getenv('DEFAULT_CHECK_INTERVAL', 30))
DEFAULT_JITTER = int(os.getenv('DEFAULT_JITTER', 5))
MAX_EXECUTION_TIME = int(os.getenv('MAX_EXECUTION_TIME', 60))
AGENT_PREFIX = os.getenv('AGENT_PREFIX', 'AGENT')

# Stealth configuration
ENABLE_EVASION = os.getenv('ENABLE_EVASION', 'True').lower() == 'true'
ENABLE_PERSISTENCE = os.getenv('ENABLE_PERSISTENCE', 'False').lower() == 'true'

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', os.path.join(TEMP_DIR, 'shadow_nexus.log'))
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

# System information
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"
