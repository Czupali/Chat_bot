import os
from dotenv import load_dotenv
from src.logger_setup import LoggerSetup
# import logging

# Betölti a .env fájlt a modul elején
load_dotenv()

# Konfiguráció betöltése előtt naplózás init
SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH", "logs/session.log")  # ideiglenes
logger_setup = LoggerSetup(SESSION_LOG_PATH)


class ConfigManager:
    """Manages configuration loading from .env file."""
    def __init__(self, env_file: str = "config/.env"):
        """Inicializálja a ConfigManager osztályt a megadott .env fájllal."""
        self.logger = logger_setup.get_logger("Config")
        load_dotenv(env_file)
        self.config = {
            "rasa_url": os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook"),
            "session_log_path": os.getenv("SESSION_LOG_PATH")
        }
        self._validate_config()
        self.logger.info("ConfigManager initialized with env file: %s", env_file)

    def _validate_config(self):
        """Validálja a szükséges konfigurációs értékeket."""
        if not self.config["session_log_path"]:
            self.logger.error("SESSION_LOG_PATH not set in .env")
            raise ValueError("SESSION_LOG_PATH is required")
        if not self.config["rasa_url"]:
            self.logger.warning("RASA_URL not set, using default: %s", self.config["rasa_url"])

    def get(self, key: str) -> str:
        """Visszaadja a megadott konfigurációs értéket."""
        value = self.config.get(key)
        if value is None:
            self.logger.warning("Configuration key not found: %s", key)
        return value
