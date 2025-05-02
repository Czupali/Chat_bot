# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Dict, List, Text

import wikipedia
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from config.config_manager import ConfigManager
from src.logger_setup import LoggerSetup

# from dotenv import load_dotenv, set_key
# import datetime
# import os
# import logging

# model_name = "mistralai/Mistral-7B-Instruct-v0.1"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

config = ConfigManager()
RASA_URL = config.get("rasa_url")
SESSION_LOG_PATH = config.get("session_log_path")

# logger = logging.getLogger("ActionLogger")
# logger.setLevel(logging.INFO)
# if not logger.handlers:  # Elkeruljuk a dupla handlerek hozzaadasat
#     os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)
#     handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
#     handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [Action] %(message)s"))
#     logger.addHandler(handler)
#     logger.addHandler(logging.StreamHandler())

# logolas init
logger_setup = LoggerSetup(SESSION_LOG_PATH)
logger = logger_setup.get_logger("Action")

print("*" * 10 + "Mukodik a log" + "SESSION_LOG_PATH: " + SESSION_LOG_PATH)

# Szerver inditasanak naplozasa
logger.info("Action server started – session log: %s", SESSION_LOG_PATH)

logger.info("Testing actions.py logging")


def call_llm(question: str) -> str:
    # # Kérdés tokenizálása
    # inputs = tokenizer(question, return_tensors="pt")

    # # Modell előrejelzés
    # with torch.no_grad():
    #     outputs = model.generate(**inputs, max_length=100,
    # num_return_sequences=1, temperature=0.7)

    # # Válasz dekódolása és visszaadása
    # answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # return answer.strip()
    return "🔮 (This is where an LLM would generate a smart answer...)"


class ActionTopicHandler(Action):
    def name(self) -> str:
        return "action_topic_handler"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Összes topic entitas lekeres
        topics = [e['value'] for e in tracker.latest_message['entities'] if e['entity'] == 'topic']
        user_message = tracker.latest_message.get("text")
        logger.info("User message: %s | Detected topics: %s", user_message, topics)

#
# Ha egy tema sincs
#
        if len(topics) == 0:
            # Az egesz uzenetet atadjuk az llm-nek, majd elmentjuk egy kulon fajlba
            # tanitas elotti ellenorzesre, topic kiválasztásra, akar utter letrehozasra
            dispatcher.utter_message(
                text=f"You're asking about '{user_message}'. "
                "Let me try to answer based on an external source...")
            try:
                response = call_llm(user_message)
                logger.info("LLM response: %s", response)
                if response and len(response.strip()) > 0:
                    dispatcher.utter_message(text=response)
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't generate a useful answer.")
                    logger.error("LLM returned empty response for user message: %s", user_message)
            except Exception as e:
                dispatcher.utter_message(text="An error occurred while using the AI model.")
                logger.error("LLM error for user message: %s | Error: %s", user_message, str(e))


#
# Ha csak egy tema van
#
        elif len(topics) == 1:
            # utter kereses, ha nincs wikipedia(, ha nincs llm)
            utter_key = "utter_" + topics[0].lower().replace(" ", "_")
            if utter_key in domain.get("responses", {}):
                # Ha letezik sablonos (utter) valasz
                dispatcher.utter_message(text=f"Let me tell you about {topics[0]}...")
                dispatcher.utter_message(response=utter_key)
                logger.info("Utter response used: %s", utter_key)

            else:
                try:
                    logger.info("Searching Wikipedia for topic: %s", topics[0])
                    summary = wikipedia.summary(topics[0], sentences=2)
                    dispatcher.utter_message(text=summary)
                    logger.info("Wikipedia summary returned for topic: %s", topics[0])
                except wikipedia.exceptions.DisambiguationError as e:
                    dispatcher.utter_message(text="That topic is ambiguous. "
                                             "Could you be more specific?")
                    logger.error("Wikipedia DisambiguationError for topic: %s |"
                                 " User message: %s | Error: %s", topics[0], user_message, str(e))
                except wikipedia.exceptions.PageError:
                    dispatcher.utter_message(text="I couldn't find "
                                             "a Wikipedia page for that topic.")
                    logger.error("Wikipedia PageError for topic: %s"
                                 " | User message: %s | "
                                 "Error: Page not found", topics[0], user_message)
                except Exception as e:
                    dispatcher.utter_message(text="An unexpected error "
                                             "occurred while searching Wikipedia.")
                    logger.error("Wikipedia error for topic: %s"
                                 " | User message: %s | Error: %s", topics[0], user_message, str(e))


#
#  Ha tobb tema van
#
        else:
            # Mivel kilottuk a 0 es 1 topic lehetoseget igy csak a tobb topic maradt.
            # Osszefuzzuk, megnezzuk van e utter, ha van kiiratas, ha nincs llm.
            utter_key = "utter_" + "_".join([t.lower().replace(" ", "_") for t in topics])
            joined = " and ".join(topics)

            if utter_key in domain.get("responses", {}):
                # Ha letezik sablonos (utter) valasz
                dispatcher.utter_message(response=utter_key)
                logger.info("Utter response used: %s", utter_key)
            else:
                dispatcher.utter_message(text=f"You're asking about {joined}. "
                                         "Let me try to answer based on an external source...")
                try:
                    response = call_llm(user_message)
                    logger.info("LLM response: %s", response)
                    if response and len(response.strip()) > 0:
                        dispatcher.utter_message(text=response)
                    else:
                        dispatcher.utter_message(text="Sorry, I couldn't generate a useful answer.")
                        logger.error("LLM returned empty response for user message:"
                                     " %s", user_message)
                except Exception as e:
                    dispatcher.utter_message(text="An error occurred while using the AI model.")
                    logger.error("LLM error for user message: %s | Error: %s", user_message, str(e))

        return []
