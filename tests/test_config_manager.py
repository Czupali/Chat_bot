import unittest
from unittest.mock import patch
import os
from config.config_manager import ConfigManager
from src.logger_setup import LoggerSetup


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Mockoljuk a környezeti változókat
        os.environ["SESSION_LOG_PATH"] = "logs/test_session.log"
        os.environ["RASA_URL"] = "http://localhost:5005/webhooks/rest/webhook"
        self.logger_setup = LoggerSetup("logs/test_session.log")

    @patch('dotenv.load_dotenv')
    def test_init_success(self, mock_load_dotenv):
        """Teszteli a ConfigManager sikeres inicializálását."""
        mock_load_dotenv.return_value = None
        config_manager = ConfigManager()
        self.assertEqual(config_manager.config["session_log_path"], "logs/test_session.log")
        self.assertEqual(config_manager.config["rasa_url"],
                         "http://localhost:5005/webhooks/rest/webhook")

    @patch('dotenv.load_dotenv')
    def test_init_missing_session_log_path(self, mock_load_dotenv):
        """Teszteli, ha a SESSION_LOG_PATH hiányzik."""
        mock_load_dotenv.return_value = None
        os.environ.pop("SESSION_LOG_PATH", None)
        with patch('os.getenv', return_value=None):  # Mockoljuk az os.getenv hívást
            with self.assertRaises(ValueError) as context:
                ConfigManager()
        self.assertEqual(str(context.exception), "SESSION_LOG_PATH is required")

    @patch('dotenv.load_dotenv')
    def test_init_missing_rasa_url(self, mock_load_dotenv):
        """Teszteli, ha a RASA_URL hiányzik, és az alapértelmezett érték beállítódik."""
        mock_load_dotenv.return_value = None
        os.environ.pop("RASA_URL", None)
        with patch('os.getenv') as mock_getenv:
            # Mockoljuk, hogy a RASA_URL üres, de a SESSION_LOG_PATH megmarad
            mock_getenv.side_effect = (lambda key, default=None: "logs/test_session.log"
                                       if key == "SESSION_LOG_PATH" else default)
            config_manager = ConfigManager()
            self.assertEqual(config_manager.config["rasa_url"],
                             "http://localhost:5005/webhooks/rest/webhook")

    @patch('dotenv.load_dotenv')
    def test_validate_config_missing_rasa_url(self, mock_load_dotenv):
        """Teszteli a _validate_config metódust üres RASA_URL esetén."""
        mock_load_dotenv.return_value = None
        config_manager = ConfigManager()
        # Kézzel állítjuk be a config szótárat üres rasa_url értékkel
        config_manager.config["rasa_url"] = None
        with patch.object(self.logger_setup.get_logger("Config"), 'warning') as mock_warning:
            config_manager._validate_config()
            mock_warning.assert_called_once_with(
                "RASA_URL not set, using default: %s",
                None
            )

    @patch('dotenv.load_dotenv')
    def test_init_invalid_env_file(self, mock_load_dotenv):
        """Teszteli, ha az .env fájl nem létezik."""
        mock_load_dotenv.return_value = False
        with patch.object(self.logger_setup.get_logger("Config"), 'info') as mock_info:
            config_manager = ConfigManager(env_file="non_existent.env")
            self.assertEqual(config_manager.config["session_log_path"], "logs/test_session.log")
            self.assertEqual(config_manager.config["rasa_url"],
                             "http://localhost:5005/webhooks/rest/webhook")
            mock_info.assert_called_once_with("ConfigManager initialized with env file: %s",
                                              "non_existent.env")

    @patch('dotenv.load_dotenv')
    def test_get_existing_key(self, mock_load_dotenv):
        """Teszteli a meglévő kulcs lekérdezését."""
        mock_load_dotenv.return_value = None
        config_manager = ConfigManager()
        result = config_manager.get("rasa_url")
        self.assertEqual(result, "http://localhost:5005/webhooks/rest/webhook")

    @patch('dotenv.load_dotenv')
    def test_get_non_existing_key(self, mock_load_dotenv):
        """Teszteli a nem létező kulcs lekérdezését."""
        mock_load_dotenv.return_value = None
        config_manager = ConfigManager()
        with patch.object(config_manager.logger, 'warning') as mock_warning:
            result = config_manager.get("invalid_key")
            self.assertIsNone(result)
            mock_warning.assert_called_once_with("Configuration key not found: %s", "invalid_key")


if __name__ == '__main__':
    unittest.main()
