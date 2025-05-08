import requests
from src.logger_setup import LoggerSetup
from config.config_manager import ConfigManager

# Konfiguráció betoltese
config = ConfigManager()
SESSION_LOG_PATH = config.get("session_log_path")

# logolas inicializálás
logger_setup = LoggerSetup(SESSION_LOG_PATH)


class Chatbot:
    def __init__(self, rasa_url: str):
        """Inicializálja a Chatbot osztályt a Rasa URL-lel és naplózóval."""
        self.rasa_url = rasa_url
        self.chat_history = []  # Csevegési előzmények tárolása
        self.logger = logger_setup.get_logger("Chatbot")
        self.logger.info("Chatbot initialized with Rasa URL: %s", rasa_url)

    def send_message(self, message: str, chatbot: list, state: list) -> tuple[list, list, str]:
        """Elküldi az üzenetet a Rasa szervernek és visszaadja az előzményeket és a választ."""
        if not message.strip():
            self.logger.warning("Empty message received.")
            return chatbot, state, "⚠️ Kérlek, írj üzenetet."

        self.logger.info("User message: %s", message)

        try:
            # HTTP kérés küldése a Rasa szervernek
            response = requests.post(
                self.rasa_url,
                json={"sender": "user", "message": message},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                self.logger.error("Empty response from Rasa server.")
                bot_reply = "⚠️ The chatbot didn't respond. Please try again."
            else:
                bot_reply = ""
                for item in data:
                    if "text" in item:
                        bot_reply += item["text"] + "\n"
                    if "image" in item:
                        bot_reply += f"![Image]({item['image']})\n"
                bot_reply = bot_reply.strip() or "⚠️ Nincs érvényes válasz a chatbottól."
                self.logger.info("Rasa response: %s", bot_reply)

        except requests.ConnectionError:
            self.logger.error("Connection error: Rasa server is not responding.")
            bot_reply = "⚠️ The chatbot server is not responding. Please check if it's running."
        except requests.Timeout:
            self.logger.error("Timeout error: Rasa server took too long to respond.")
            bot_reply = "⚠️ The chatbot took too long to respond. Try again later."
        except requests.HTTPError as e:
            self.logger.error("HTTP error: %s", e)
            bot_reply = f"⚠️ HTTP Error: {e}"
        except requests.RequestException as e:
            self.logger.error("Request error: %s", e)
            bot_reply = f"⚠️ Error: {e}"

        # Csevegési előzmények frissítése
        self.chat_history.append((message, bot_reply))
        # return self.chat_history, bot_reply

        # Frissítjük a Gradio csevegési előzményeket és az állapotot
        chatbot.append((message, bot_reply))
        state.append({"user": message, "bot": bot_reply})

        return chatbot, state, ""  # Üres string a textbox üresítéséhez
