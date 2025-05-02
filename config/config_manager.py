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
    def __init__(self, env_file: str = ".env"):
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

# kornyezeti valtozok beload
# load_dotenv()

# # SESSION_LOG_PATH beload
# SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
# if not SESSION_LOG_PATH:
#     print("Error: SESSION_LOG_PATH not set in .env. "
#           "Please ensure the action server initializes it.")


# # Kornyezeti valtozok betoltes
# load_dotenv()

# # RASA_URL ellenorzes
# RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
# if not os.getenv("RASA_URL"):
#     print("Warning: RASA_URL not set in .env. Using default: "
#           "http://localhost:5005/webhooks/rest/webhook")

# # SESSION_LOG_PATH beloadolas
# SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
# if not SESSION_LOG_PATH:
#     print("Error: SESSION_LOG_PATH not set in .env. "
#           "Please ensure the action server initializes it.")


# # Kornyezeti valtozok betoltese
# load_dotenv()

# # SESSION_LOG_PATH inicial
# SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
# if not SESSION_LOG_PATH or "{timestamp}" in SESSION_LOG_PATH:
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     SESSION_LOG_PATH = f"C:/Chat_bot/Rasa_based/logs/session_{timestamp}.log"
#     try:
#         set_key(".env", "SESSION_LOG_PATH", SESSION_LOG_PATH)
#     except Exception as e:
#         print(f"Failed to update .env with SESSION_LOG_PATH: {e}")
