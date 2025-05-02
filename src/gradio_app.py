import gradio as gr
import requests
from src.process_pdf import PDFProcessor
from src.chatbot import Chatbot
from src.logger_setup import LoggerSetup
from config.config_manager import ConfigManager
# import logging
# import os
# import datetime
# from process_pdf import extract_pdf_text
# from dotenv import load_dotenv

config = ConfigManager()
RASA_URL = config.get("rasa_url")
SESSION_LOG_PATH = config.get("session_log_path")

# os.makedirs(os.path.dirname(SESSION_LOG_PATH), exist_ok=True)
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - [Gradio] %(message)s",
#     handlers=[
#         logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8"),
#         logging.StreamHandler()  # kimenetre is
#     ]
# )

# logolas init
logger_setup = LoggerSetup(SESSION_LOG_PATH)
logger = logger_setup.get_logger("Gradio")

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


# Chatbot és PDFProcessor példányok létrehozása
chatbot_instance = Chatbot(RASA_URL)
pdf_processor = PDFProcessor()

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

    # msg.submit(chat_with_rasa, [msg, chatbot, state], [chatbot, state, msg])

    # chatbot osztály használata
    msg.submit(chatbot_instance.send_message, [msg, chatbot, state], [chatbot, state, msg])
    clear_btn.click(lambda: ([], []), None, [chatbot, state])  # Delete gomb
    # PDF feldolgozo gomb
    process_pdf_btn.click(pdf_processor.extract_pdf_text, pdf_upload, pdf_output)

if __name__ == "__main__":
    if not check_rasa_server():
        logger.warning("Rasa server is not reachable. "
                       "Start it with 'rasa run --enable-api --cors \"*\" --debug'.")
    demo.launch()
