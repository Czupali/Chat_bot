import unittest
from unittest.mock import patch, MagicMock
import os
import logging
from src.logger_setup import LoggerSetup


class TestLoggerSetup(unittest.TestCase):
    def setUp(self):
        self.log_file = "logs/test_session.log"
        # Tisztitjuk a _loggers dict-t minden teszt elott
        LoggerSetup._loggers.clear()

    @patch('os.makedirs')
    def test_init(self, mock_makedirs):
        """Teszteli a LoggerSetup inicializálását."""
        logger_setup = LoggerSetup(self.log_file, log_level=logging.INFO)
        self.assertEqual(logger_setup.log_file, self.log_file)
        self.assertEqual(logger_setup.log_level, logging.INFO)
        mock_makedirs.assert_called_once_with(os.path.dirname(self.log_file), exist_ok=True)
        self.assertEqual(logger_setup._loggers, {})

    @patch('logging.getLogger')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    def test_get_logger_new(self, mock_stream_handler, mock_file_handler, mock_get_logger):
        """Teszteli az új logger létrehozását."""
        module_name = "TestModule"
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_file_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_file_handler_instance
        mock_stream_handler_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        logger_setup = LoggerSetup(self.log_file)
        logger = logger_setup.get_logger(module_name)

        self.assertEqual(logger, mock_logger)
        self.assertEqual(logger_setup._loggers[module_name], mock_logger)
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        mock_get_logger.assert_called_once_with(module_name)
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        mock_logger.handlers.clear.assert_called_once()
        mock_file_handler.assert_called_once_with(self.log_file, encoding="utf-8")
        mock_stream_handler.assert_called_once()
        self.assertEqual(mock_logger.addHandler.call_count, 2)  # FileHandler es StreamHandler
        mock_logger.info.assert_called_once_with("Logger initialized for module: %s", module_name)

    @patch('logging.getLogger')
    def test_get_logger_existing(self, mock_get_logger):
        """Teszteli a meglévő logger visszaadását."""
        module_name = "TestModule"
        mock_logger = MagicMock()
        logger_setup = LoggerSetup(self.log_file)
        logger_setup._loggers[module_name] = mock_logger

        logger = logger_setup.get_logger(module_name)

        self.assertEqual(logger, mock_logger)
        mock_get_logger.assert_not_called()

    @patch('logging.getLogger')
    @patch('logging.FileHandler')
    @patch('logging.StreamHandler')
    def test_logger_logging(self, mock_stream_handler, mock_file_handler, mock_get_logger):
        """Teszteli a naplózási üzenetek helyes naplózását."""
        module_name = "TestModule"
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_file_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_file_handler_instance
        mock_stream_handler_instance = MagicMock()
        mock_stream_handler.return_value = mock_stream_handler_instance

        logger_setup = LoggerSetup(self.log_file)
        logger = logger_setup.get_logger(module_name)
        logger.info("Test message")

        mock_logger.info.assert_called_with("Test message")


if __name__ == '__main__':
    unittest.main()