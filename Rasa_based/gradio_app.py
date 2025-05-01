import logging
import os
import gradio as gr
import requests
# import datetime
from dotenv import load_dotenv
from process_pdf import extract_pdf_text

# Kornyezeti valtozok betoltes
load_dotenv()

# RASA_URL ellenorzes
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
if not os.getenv("RASA_URL"):
    print("Warning: RASA_URL not set in .env. Using default: "
          "http://localhost:5005/webhooks/rest/webhook")

# SESSION_LOG_PATH beloadolas
SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
if not SESSION_LOG_PATH:
    print("Error: SESSION_LOG_PATH not set in .env. "
          "Please ensure the action server initializes it.")


# logolas
os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [Gradio] %(message)s",
    handlers=[
        logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()  # kimenetre is
    ]
)
logger = logging.getLogger(__name__)

print("*" * 10 + "Mukodik a log" + "SESSION_LOG_PATH: " + SESSION_LOG_PATH)

logger.info("Successfully loaded .env file")
logger.info("Gradio app started – session log: %s", SESSION_LOG_PATH)


def check_rasa_server():
    """Ellenorzi, hogy a Rasa szerver elerheto-e."""
    try:
        response = requests.get(RASA_URL.replace("/webhooks/rest/webhook", ""), timeout=2)
        logger.info("Rasa server is reachable.")
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error("Failed to connect to Rasa server: %s", e)
        return False


def chat_with_rasa(message, chatbot, state):
    """Kommunikacio a Rasa szerverrel."""
    if not message.strip():
        logger.warning("Empty message received.")
        return chatbot, state, "⚠️ Kérlek, írj üzenetet."

    logger.info("User message: %s", message)

    # payload = {"sender": "user", "message": message}
    try:
        response = requests.post(RASA_URL, json={"sender": "user", "message": message}, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not data:
            logger.error("Empty response from Rasa server.")
            bot_reply = "⚠️ The chatbot didn't respond. Please try again."
        else:
            bot_reply = ""
            for item in data:
                if "text" in item:
                    bot_reply += item["text"] + "\n"
                if "image" in item:
                    bot_reply += f"![Image]({item['image']})\n"
            bot_reply = bot_reply.strip() or "⚠️ Nincs érvényes válasz a chatbottól."

            logger.info("Rasa response: %s", bot_reply)

    except requests.ConnectionError:
        logger.error("Connection error: Rasa server is not responding.")
        bot_reply = "⚠️ The chatbot server is not responding. Please check if it's running."
    except requests.Timeout:
        logger.error("Timeout error: Rasa server took too long to respond.")
        bot_reply = "⚠️ The chatbot took too long to respond. Try again later."
    except requests.HTTPError as e:
        logger.error("HTTP error: %s", e)
        bot_reply = f"⚠️ HTTP Error: {e}"
    except requests.RequestException as e:
        logger.error("Request error: %s", e)
        bot_reply = f"⚠️ Error: {e}"

    chatbot.append((message, bot_reply))
    new_state = state + [{"user": message, "bot": bot_reply}]  # State módosítása
    return chatbot, new_state, ""  # Uzenetmezo torlese


def process_pdf_upload(pdf_file):
    """PDF fajl feltoltese es szoveg kinyerese."""
    if pdf_file is None:
        logger.warning("No PDF file uploaded.")
        return "Kérlek, tölts fel egy PDF fájlt."
    result = extract_pdf_text(pdf_file)
    logging.info("PDF processing result: %s", result)
    return result


with gr.Blocks(title="AI Chatbot") as demo:
    gr.Markdown("""
        ## 🤖 AI Chatbot (Rasa + Gradio)
        Ask me about AI, machine learning, or just chat!
        **Examples**: "What is AI?", "Tell me a joke!", "How are you?"
        """)
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Your message", placeholder="Type your message here...")
    clear_btn = gr.Button("Clear")
    pdf_upload = gr.File(label="Upload PDF", file_types=[".pdf"])  # PDF feltolto
    process_pdf_btn = gr.Button("Process PDF")  # Gomb
    pdf_output = gr.Textbox(label="PDF Processing Result")  # Kimenet

    state = gr.State([])

    msg.submit(chat_with_rasa, [msg, chatbot, state], [chatbot, state, msg])
    clear_btn.click(lambda: ([], []), None, [chatbot, state])
    process_pdf_btn.click(process_pdf_upload, pdf_upload, pdf_output)

if __name__ == "__main__":
    if not check_rasa_server():
        logger.warning("Rasa server is not reachable. "
                       "Start it with 'rasa run --enable-api --cors \"*\" --debug'.")
    demo.launch()
