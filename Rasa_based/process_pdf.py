import os
import logging
import datetime
import tempfile
import pdfplumber
from dotenv import load_dotenv, set_key
from pdfminer.pdfparser import PDFSyntaxError

# kornyezeti valtozok beload
load_dotenv()

# SESSION_LOG_PATH beload
SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
if not SESSION_LOG_PATH:
    print("Error: SESSION_LOG_PATH not set in .env."
          " Please ensure the action server initializes it.")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    SESSION_LOG_PATH = f"C:/Chat_bot/Rasa_based/logs/session_{timestamp}.log"
try:
    set_key(".env", "SESSION_LOG_PATH", SESSION_LOG_PATH)
except Exception as e:
    print(f"Failed to update .env with SESSION_LOG_PATH: {e}")

# logolas
logger = logging.getLogger("PDFLogger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [PDF] %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

logger.info("Successfully loaded .env file")
logger.info("PDF Processing started – session log: %s", SESSION_LOG_PATH)


def extract_pdf_text(pdf_path: str, timestamp_pdf: str) -> tuple[str, int]:
    """
    Kinyeri a PDF tartalmát szövegként, és elmenti egy fájlba a timestamp_pdf alapján.
    Visszaadja a fájl elérési útját és a kinyert oldalak számát.
    """
    if isinstance(pdf_path, tempfile._TemporaryFileWrapper):
        pdf_path = pdf_path.name
        logger.info("Processing Gradio tempfile: %s", pdf_path)
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    logger.error("Not a valid PDF file: %s", pdf_path)
                    return f"Hiba: A fájl nem érvényes PDF: {pdf_path}", 0
        except Exception as e:
            logger.error("Nem sikerült megnyitni a fájlt: %s", e)
            return f"Hiba: Nem sikerült megnyitni a fájlt: {e}", 0

    logger.info("Starting PDF processing for: %s", pdf_path)

    if not os.path.exists(pdf_path):
        logger.error("File does not exist: %s", pdf_path)
        return f"Hiba: A fájl nem található: {pdf_path}", 0

    file_size = os.path.getsize(pdf_path)
    logger.info("File size: %d bytes", file_size)
    if file_size == 0:
        logger.error("File is empty: %s", pdf_path)
        return f"Hiba: A fájl üres: {pdf_path}", 0

    try:
        logger.debug("Extracting text from PDF: %s", pdf_path)

        # PDF szöveg kinyerése
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                text += page_text + "\n" if page_text else ""

        # # Ideiglenes fájl létrehozása
        # with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
        #  suffix=f"_{conversation_id}.txt", delete=False) as temp_file:
        #     temp_file.write(text)
        #     output_file = temp_file.name

        # logger.info("PDF text saved to temporary file: %s", output_file)
        # return output_file, num_pages

        # Szöveg mentése fájlba a conversation_id alapján
        output_dir = "C:/Chat_bot/Rasa_based/processed_txt"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{timestamp_pdf}_pdf_text.txt")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info("PDF text saved to: %s", output_file)
        return output_file, num_pages

    except FileNotFoundError:
        logger.error("PDF file not found: %s", pdf_path)
        return f"Hiba: A PDF fájl nem található: {pdf_path}", None
    except PDFSyntaxError:
        logger.error("Invalid PDF format: %s", pdf_path)
        return f"Hiba: Érvénytelen PDF formátum: {pdf_path}", None
    except Exception as e:
        logger.error("Error processing PDF %s: %s", pdf_path, str(e))
        return f"Hiba a PDF feldolgozása közben: {str(e)}", None
