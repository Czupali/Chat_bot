# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
import os
import datetime
import logging
import re
import wikipedia
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from dotenv import load_dotenv, set_key
from process_pdf import extract_pdf_text


# Kornyezeti valtozok betoltese
load_dotenv()

# SESSION_LOG_PATH inicial
SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
if not SESSION_LOG_PATH or "{timestamp}" in SESSION_LOG_PATH:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    SESSION_LOG_PATH = f"C:/Chat_bot/Rasa_based/logs/session_{timestamp}.log"
    try:
        set_key(".env", "SESSION_LOG_PATH", SESSION_LOG_PATH)
    except Exception as e:
        print(f"Failed to update .env with SESSION_LOG_PATH: {e}")


# logolas
logger = logging.getLogger("ActionLogger")
logger.setLevel(logging.INFO)
if not logger.handlers:  # Elkeruljuk a dupla handlerek hozzaadasat
    os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)
    handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [Action] %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

print("*" * 10 + "Mukodik a log" + "SESSION_LOG_PATH: " + SESSION_LOG_PATH)

# Szerver inditasanak naplozasa
logger.info("Action server started – session log: %s", SESSION_LOG_PATH)

logger.info("Testing actions.py logging")


def call_llm(question: str) -> str:
    # # Kérdés tokenizálása
    # inputs = tokenizer(question, return_tensors="pt")
    # # Modell előrejelzés
    # with torch.no_grad():
    #     outputs = model.generate(**inputs, max_length=100, num_return_sequences=1, temperature=0.7)

    # # Válasz dekódolása és visszaadása
    # answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # return answer.strip()
    return "🔮 (This is where an LLM would generate a smart answer...)"


# class ActionSetPDFPath(Action):
#     def name(self) -> str:
#         return "action_set_pdf_path"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         # Entitások kinyerése
#         entities = tracker.latest_message.get("entities", [])
#         pdf_path = None
#         for entity in entities:
#             if entity["entity"] == "pdf_path":
#                 pdf_path = entity["value"]
#                 break

#         # Ha nincs pdf_path entitás, akkor no pdf-kent kezeljük
#         if not pdf_path:
#             dispatcher.utter_message(response="utter_no_pdf")
#             return []

#         # # Conversation ID használata a fájl azonosításához
#         # conversation_id = tracker.sender_id
#         # A conversation id csak "user" ami felülírást okoz
#         timestamp_pdf = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#         # PDF szöveg kinyerése és fájlba mentése
#         text_file_path, num_pages = extract_pdf_text(pdf_path, timestamp_pdf)
        
#         if not text_file_path or num_pages == 0:
#             dispatcher.utter_message(response="utter_no_pdf")
#             return []
        
#         logger.info("Slot pdf_text_path: %s, num_pages: %s", text_file_path, num_pages)
#         dispatcher.utter_message(text="HIIIII THIS IS A TEST")
#         dispatcher.utter_message(text=f"PDF processed with {num_pages} pages. You can now ask about its content.")
#         logger.info("ASD EZT MÁR BASZKI KIÍRNI")
#         # A slot-ban a szövegfájl elérési útját tároljuk
#         return [SlotSet("pdf_text_path", text_file_path)]


class ActionHandlePDFQuestion(Action):
    def name(self) -> str:
        return "action_handle_pdf_question"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Szövegfájl elérési útjának lekérése
        text_file_path = tracker.get_slot("pdf_text_path")
        logger.info("Slot pdf_text_path: %s", text_file_path)
        if not text_file_path or not os.path.exists(text_file_path):
            dispatcher.utter_message(response="utter_no_pdf")
            return []

        # Szöveg visszaolvasása a fájlból
        try:
            with open(text_file_path, "r", encoding="utf-8") as f:
                pdf_text = f.read()
            if not pdf_text:
                dispatcher.utter_message(text="Error: PDF text is empty.")
                return []
            logger.info("Extracted PDF text (first 200 chars): %s", pdf_text[:200])  # Naplózás

        except Exception as e:
            dispatcher.utter_message(text=f"Error generating answer: {str(e)}")
            logger.error("Error reading PDF text file %s: %s", text_file_path, str(e))
            return []

        # Felhasználó kérdése
        question = tracker.latest_message.get("text", "What is in the PDF?")
        logger.info("User question: %s", question)  # Naplózás

        # LLM hívása a válasz generálására
        # LLM hívása a kérdés és a szöveg átadásával
        try:
            response = call_llm(question + "\n\nPDF content:\n" + pdf_text)
            logger.info("LLM response: %s", response)  # Naplózás
            dispatcher.utter_message(text=response)
        except Exception as e:
            dispatcher.utter_message(text=f"Error generating answer: {str(e)}")
            logger.error("LLM error for question %s: %s", question, str(e))

        return []

        # # Kinyerjük a PDF tartalmát
        # try:
        #     pdf_text, _ = extract_pdf_text(pdf_path, conversation_id)
        #     # Egyszerű összefoglaló (pl. az első 200 karakter)
        #     summary = pdf_text[:200] + "..." if len(pdf_text) > 200 else pdf_text
        #     dispatcher.utter_message(response="utter_pdf_summary", pdf_summary=summary)

        #     # A felhasználó kérdése
        #     question = tracker.latest_message.get("text", "").lower()
        #     keywords = question.split()
        #     matches = []
        #     for keyword in keywords:
        #         pattern = r".{0,50}" + re.escape(keyword) + r".{0,50}"
        #         found = re.findall(pattern, pdf_text, re.IGNORECASE)
        #         matches.extend(found[:2])  # Maximum 2 találat kulcsszavonként
        #     if matches:
        #         answer = "\n".join(matches)
        #     else:
        #         answer = "No relevant information found in the PDF."
        #     dispatcher.utter_message(response="utter_pdf_answer", pdf_answer=answer)
        # except FileNotFoundError:
        #     dispatcher.utter_message(text="Error: PDF file not found.")
        # except SyntaxError:
        #     dispatcher.utter_message(text="Error: Invalid PDF format.")
        # except Exception as e:
        #     dispatcher.utter_message(text=f"Error processing PDF: {str(e)}")
        #     logger.error("PDF processing error: %s", str(e))

        # return [SlotSet("pdf_path", pdf_path)]


class ActionTopicHandler(Action):
    def name(self) -> str:
        return "action_topic_handler"

    def run(self, dispatcher: CollectingDispatcher,
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
                "Let me try to answer based on an external source..."
            )
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
                    dispatcher.utter_message(text="That topic is ambiguous. Could you be more specific?")
                    logger.error("Wikipedia DisambiguationError for topic: %s |"
                                 " User message: %s | Error: %s", topics[0], user_message, str(e))
                except wikipedia.exceptions.PageError:
                    dispatcher.utter_message(text="I couldn't find a Wikipedia page for that topic.")
                    logger.error("Wikipedia PageError for topic: %s"
                                 " | User message: %s | Error: Page not found", topics[0], user_message)
                except Exception as e:
                    dispatcher.utter_message(text="An unexpected error occurred while searching Wikipedia.")
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
                dispatcher.utter_message(text=f"You're asking about {joined}."
                                         " Let me try to answer based on an external source...")
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

        return []
