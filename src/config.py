"""
Configuration du projet Gogol
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INDEXED_DATA_DIR = DATA_DIR / "indexed"
LOGS_DIR = BASE_DIR / "logs"

# Configuration du crawler
CRAWLER_CONFIG = {
    "max_pages": int(os.getenv("CRAWLER_MAX_PAGES", 100)),
    "delay_between_requests": float(os.getenv("CRAWLER_DELAY", 1.0)),
    "timeout": int(os.getenv("CRAWLER_TIMEOUT", 10)),
    "user_agent": os.getenv("CRAWLER_USER_AGENT", "Gogol Bot 1.0"),
}

# Configuration de l'indexeur
INDEXER_CONFIG = {
    "database_path": INDEXED_DATA_DIR / "gogol_index.db",
    "min_word_length": int(os.getenv("MIN_WORD_LENGTH", 3)),
    "max_word_length": int(os.getenv("MAX_WORD_LENGTH", 50)),
}

# Configuration du moteur de recherche
SEARCH_CONFIG = {
    "results_per_page": int(os.getenv("RESULTS_PER_PAGE", 10)),
    "max_results": int(os.getenv("MAX_RESULTS", 100)),
}

# Configuration de l'interface web
WEB_CONFIG = {
    "host": os.getenv("WEB_HOST", "127.0.0.1"),
    "port": int(os.getenv("WEB_PORT", 8000)),
    "debug": os.getenv("DEBUG", "True").lower() == "true",
}

# Logging
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "file": LOGS_DIR / "gogol.log",
}
