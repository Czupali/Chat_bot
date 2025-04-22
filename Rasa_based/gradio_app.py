import gradio as gr
import requests
import logging
import os
import datetime
from dotenv import load_dotenv, set_key
from process_pdf import extract_pdf_text 

# Kornyezeti valtozok betoltes
load_dotenv()

# RASA_URL ellenorzes
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
if not os.getenv("RASA_URL"):
    print("Warning: RASA_URL not set in .env. Using default: http://localhost:5005/webhooks/rest/webhook")

# Idobelyeg kezeles
SESSION_TIMESTAMP = os.getenv("SESSION_LOG_TIMESTAMP")
# Ha nincs idobelyeg, generalj ujat
if not SESSION_TIMESTAMP:
    SESSION_TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        set_key(".env", "SESSION_LOG_TIMESTAMP", SESSION_TIMESTAMP)
    except Exception as e:
        print(f"Failed to update .env with SESSION_LOG_TIMESTAMP: {e}")  # Ideiglenes print, mert a logger még nem létezik

SESSION_LOG_PATH = f"logs/session_{SESSION_TIMESTAMP}.log"

# logolas
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [Gradio] %(message)s",
    handlers=[
        logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8"),
        logging.StreamHandler() # kimenetre is
    ]
)
logger = logging.getLogger(__name__)

print("*"*10 + "Mukodik a log" + "SESSION_LOG_PATH: " + SESSION_LOG_PATH)

logger.info("Successfully loaded .env file")
logger.info(f"Gradio app started – session log: {SESSION_LOG_PATH}")

# Kornyezeti valtozok ellenorzese
if os.getenv("RASA_URL"):
    logger.info("Successfully loaded .env file")
else:
    logger.error("Failed to load .env file")

logger.info("Gradio app started – new session log created.")

def check_rasa_server():
    """Ellenorzi, hogy a Rasa szerver elerheto-e."""
    try:
        response = requests.get("http://localhost:5005", timeout=2)
        logger.info("Rasa server is reachable.")
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Failed to connect to Rasa server: {e}")
        return False

def chat_with_rasa(message, history):
    """Kommunikacio a Rasa szerverrel."""
    if not message.strip():
        logger.warning("Empty message received.")
        return history, history, "⚠️ Please enter a message."

    logger.info(f"User message: {message}")

    payload = {"sender": "user", "message": message}
    try:
        response = requests.post(RASA_URL, json=payload, timeout=5)
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
            
            logger.info(f"Rasa response: {bot_reply}")

    except requests.ConnectionError:
        logger.error("Connection error: Rasa server is not responding.")
        bot_reply = "⚠️ The chatbot server is not responding. Please check if it's running."
    except requests.Timeout:
        logger.error("Timeout error: Rasa server took too long to respond.")
        bot_reply = "⚠️ The chatbot took too long to respond. Try again later."
    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        bot_reply = f"⚠️ HTTP Error: {e}"
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        bot_reply = f"⚠️ Error: {e}"

    history.append((message, bot_reply))
    state.append({"user": message, "bot": bot_reply})
    return history, history, ""  # Üzenetmező törlése


def process_pdf_upload(pdf_file):
    """PDF fajl feltoltese es szoveg kinyerese."""
    if pdf_file is None:
        logger.warning("No PDF file uploaded.")
        return "Kérlek, tölts fel egy PDF fájlt."
    result = extract_pdf_text(pdf_file)
    logging.info(f"PDF processing result: {result}")
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

    msg.submit(chat_with_rasa, [msg, state], [chatbot, state, msg])
    clear_btn.click(lambda: ([], []), None, [chatbot, state])
    process_pdf_btn.click(process_pdf_upload, pdf_upload, pdf_output)

if __name__ == "__main__":
    if not check_rasa_server():
        logger.warning("Rasa server is not reachable. Start it with 'rasa run --enable-api --cors \"*\" --debug'.")
    demo.launch()
