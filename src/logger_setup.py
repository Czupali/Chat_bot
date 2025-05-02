import os
import logging
from typing import Dict


class LoggerSetup:
    """Több modul központosított naplózási konfigurációját kezeli."""
    _loggers: Dict[str, logging.Logger] = {}  # Tárolja a létrehozott logger-eket

    def __init__(self, log_file: str, log_level: int = logging.INFO):
        """Inicializálja a LoggerSetup osztályt a naplófájllal és szinttel."""
        self.log_file = log_file
        self.log_level = log_level
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def get_logger(self, module_name: str) -> logging.Logger:
        """Létrehoz vagy visszaad egy logger-t a megadott modulhoz."""
        if module_name not in self._loggers:
            logger = logging.getLogger(module_name)
            logger.setLevel(self.log_level)
            logger.handlers.clear()  # Elkerüli a duplikált handlerek hozzáadását

            # Fájl handler
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
            ))
            logger.addHandler(file_handler)

            # Konzol handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(levelname)s - [%(name)s] %(message)s"
            ))
            logger.addHandler(console_handler)

            self._loggers[module_name] = logger
            logger.info("Logger initialized for module: %s", module_name)

        return self._loggers[module_name]
