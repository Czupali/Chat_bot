# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# This is a simple example for a custom action which utters "Hello World!"
# from typing import Any, Text, Dict, List
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
# class ActionHelloWorld(Action):
#     def name(self) -> Text:
#         return "action_hello_world"
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         dispatcher.utter_message(text="Hello World!")
#         return []

import wikipedia
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import os
import datetime

def log_error_to_file(user_message, message: str):
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/{datetime.datetime.now()}errors.log", "a", encoding="utf-8") as f:
        f.write(f"user message: {user_message}\n message: {message}\n")

def call_llm(prompt: str) -> str:
    # Itt később jöhet OpenAI, HuggingFace, Mistral, stb.
    return "🔮 (This is where an LLM would generate a smart answer...)"

class ActionTopicHandler(Action):
    def name(self) -> str:
        return "action_topic_handler"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Összes topic entitas lekeres
        topics = [e['value'] for e in tracker.latest_message['entities'] if e['entity'] == 'topic']

        user_message = tracker.latest_message.get("text")

######### Ha egy tema sincs #########
        if len(topics) == 0:
            '''
            Az egesz uzenetet atadjuk az llm-nek, majd elmentjuk egy kulon fajlba
            tanitas elotti ellenorzesre, topic kiválasztásra, akar utter letrehozasra
            '''
            dispatcher.utter_message(text=f"You're asking about '{user_message}'. Let me try to answer based on an external source...")
            try:
                response = call_llm(user_message)
                if response and len(response.strip()) > 0:
                    dispatcher.utter_message(text=response)
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't generate a useful answer.")
                    log_error_to_file(user_message, "LLM returned empty response.")
            except Exception as e:
                dispatcher.utter_message(text="An error occurred while using the AI model.")
                log_error_to_file(user_message, str(e))



######### Ha csak egy tema van #########
        elif len(topics) == 1:
            '''
            utter kereses, ha nincs wikipedia(, ha nincs llm)
            '''
            utter_key = "utter_" + topics[0].lower().replace(" ", "_")
            if utter_key in domain.get("responses", {}):
                # Ha letezik sablonos (utter) valasz
                dispatcher.utter_message(text=f"Let me tell you about {topics[0]}...")
                dispatcher.utter_message(response=utter_key)
    
            else:
                try:
                    summary = wikipedia.summary(topics[0], sentences=2)
                    dispatcher.utter_message(text=summary)
                except wikipedia.exceptions.DisambiguationError as e:
                    dispatcher.utter_message(text="That topic is ambiguous. Could you be more specific?")
                    log_error_to_file(user_message, str(e))
                except wikipedia.exceptions.PageError:
                    dispatcher.utter_message(text="I couldn't find a Wikipedia page for that topic.")
                    log_error_to_file(user_message, "Page not found")
                except Exception as e:
                    dispatcher.utter_message(text="An unexpected error occurred while searching Wikipedia.")
                    log_error_to_file(user_message, str(e))


        else:
            '''
            Mivel kilottuk a 0 es 1 topic lehetoseget igy csak a tobb topic maradt.
            Osszefuzzuk, megnezzuk van e utter, ha van kiiratas, ha nincs llm.
            '''
            utter_key = "utter_" + "_".join([t.lower().replace(" ", "_") for t in topics])
            joined = " and ".join(topics)

            if utter_key in domain.get("responses", {}):
                # Ha letezik sablonos (utter) valasz
                dispatcher.utter_message(response=utter_key)
            else:
                dispatcher.utter_message(text=f"You're asking about {joined}. Let me try to answer based on an external source...")
                try:
                    response = call_llm(user_message)
                    if response and len(response.strip()) > 0:
                        dispatcher.utter_message(text=response)
                    else:
                        dispatcher.utter_message(text="Sorry, I couldn't generate a useful answer.")
                        log_error_to_file(user_message, "LLM returned empty response.")
                except Exception as e:
                    dispatcher.utter_message(text="An error occurred while using the AI model.")
                    log_error_to_file(user_message, str(e))

        return []

