import unittest
from unittest.mock import patch, MagicMock
from src.chatbot import Chatbot
from src.logger_setup import LoggerSetup
from config.config_manager import ConfigManager
import requests


class TestChatbot(unittest.TestCase):
    def setUp(self):
        # Mockoljuk a környezeti változókat
        # os.environ["SESSION_LOG_PATH"] = "logs/test_session.log"
        # os.environ["RASA_URL"] = "http://localhost:5005/webhooks/rest/webhook"
        
        # Konfiguráció inicializálása
        self.config = ConfigManager()
        self.rasa_url = self.config.get("rasa_url")
        self.session_log_path = self.config.get("session_log_path")

        # Logger inicializálása
        self.logger_setup = LoggerSetup(self.session_log_path)
        self.chatbot = Chatbot(self.rasa_url)

    def test_init(self):
        """Teszteli a Chatbot inicializálását."""
        self.assertEqual(self.chatbot.rasa_url, self.rasa_url)
        self.assertEqual(self.chatbot.chat_history, [])
        self.assertIsNotNone(self.chatbot.logger)

    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """Teszteli a sikeres üzenetküldést."""
        # Mockoljuk a Rasa választ
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"text": "Hello!"},
            {"text": "How can I help you?"}
        ]
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        # Ellenőrizzük az eredményeket
        self.assertEqual(result_chatbot, [(message, "Hello!\nHow can I help you?")])
        self.assertEqual(result_state, [{"user": message, "bot": "Hello!\nHow can I help you?"}])
        self.assertEqual(result_text, "")
        mock_post.assert_called_once_with(
            self.rasa_url,
            json={"sender": "user", "message": message},
            timeout=5
        )

    def test_send_message_empty(self):
        """Teszteli az üres üzenet kezelését."""
        chatbot_state = []
        state = []
        message = ""

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [])
        self.assertEqual(result_state, [])
        self.assertEqual(result_text, "⚠️ Kérlek, írj üzenetet.")

    @patch('requests.post')
    def test_send_message_connection_error(self, mock_post):
        """Teszteli a kapcsolati hiba kezelését."""
        # mock_post = MagicMock()
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [(message, "⚠️ The chatbot server is not responding."
                                           " Please check if it's running.")])
        self.assertEqual(result_state, [{"user": message, "bot": "⚠️ The chatbot server is not responding."
                                         " Please check if it's running."}])
        self.assertEqual(result_text, "")

    @patch('requests.post')
    def test_send_message_timeout_error(self, mock_post):
        mock_post.side_effect = requests.Timeout("Request timed out")

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [(message, "⚠️ The chatbot took too long to respond."
                                           " Try again later.")])
        self.assertEqual(result_state, [{"user": message, "bot":
                                         "⚠️ The chatbot took too long to respond."
                                         " Try again later."}])
        self.assertEqual(result_text, "")

    @patch('requests.post')
    def test_send_message_empty_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [(message, "⚠️ The chatbot didn't respond."
                                           " Please try again.")])
        self.assertEqual(result_state, [{"user": message, "bot": "⚠️ The chatbot didn't respond."
                                         " Please try again."}])
        self.assertEqual(result_text, "")

    @patch('requests.post')
    def test_send_message_http_error(self, mock_post):
        """Teszteli az HTTP hiba kezelését."""
        error_message = "404 Client Error: Not Found"
        mock_post.side_effect = requests.HTTPError(error_message)

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [(message, f"⚠️ HTTP Error: {error_message}")])
        self.assertEqual(result_state, [{"user": message, "bot": f"⚠️ HTTP Error: {error_message}"}])
        self.assertEqual(result_text, "")

    @patch('requests.post')
    def test_send_message_request_exception(self, mock_post):
        """Teszteli az általános kérési kivétel kezelését."""
        error_message = "Invalid request"
        mock_post.side_effect = requests.RequestException(error_message)

        chatbot_state = []
        state = []
        message = "Hi!"

        result_chatbot, result_state, result_text = self.chatbot.send_message(
            message, chatbot_state, state
        )

        self.assertEqual(result_chatbot, [(message, f"⚠️ Error: {error_message}")])
        self.assertEqual(result_state, [{"user": message, "bot": f"⚠️ Error: {error_message}"}])
        self.assertEqual(result_text, "")


if __name__ == '__main__':
    unittest.main()
