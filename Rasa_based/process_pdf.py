import pdfplumber
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from pdfminer.pdfparser import PDFSyntaxError
import tempfile

# kornyezeti valtozok beload
load_dotenv()

# SESSION_LOG_PATH beload
SESSION_LOG_PATH = os.getenv("SESSION_LOG_PATH")
if not SESSION_LOG_PATH:
    print("Error: SESSION_LOG_PATH not set in .env. Please ensure the action server initializes it.")

# logolas
logger = logging.getLogger("PDFLogger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(SESSION_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [PDF] %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

logger.info("Successfully loaded .env file")
logger.info(f"PDF Processing started – session log: {SESSION_LOG_PATH}")


def extract_pdf_text(pdf_file, output_dir="processed_txt"):
    """Kinyeri a szoveget egy PDF-bol és elmenti egy .txt fajlba."""

    if isinstance(pdf_file, tempfile._TemporaryFileWrapper):
        pdf_path = pdf_file.name
        logger.info(f"Processing Gradio tempfile: {pdf_path}")
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    logger.error(f"Not a valid PDF file: {pdf_path}")
                    return f"Hiba: A fájl nem érvényes PDF: {pdf_path}"
        except Exception as e:
            logger.error(f"Nem sikerült megnyitni a fájlt: {e}")
            return f"Hiba: Nem sikerült megnyitni a fájlt: {e}"
    else:
        pdf_path = pdf_file
        logger.info(f"Processing file: {pdf_path}")

    logger.info(f"Starting PDF processing for: {pdf_path}")

    if not os.path.exists(pdf_path):
        logger.error(f"File does not exist: {pdf_path}")
        return f"Hiba: A fájl nem található: {pdf_path}"

    file_size = os.path.getsize(pdf_path)
    logger.info(f"File size: {file_size} bytes")
    if file_size == 0:
        logger.error(f"File is empty: {pdf_path}")
        return f"Hiba: A fájl üres: {pdf_path}"

    try:
        # kimeneti mappa letezik-e
        os.makedirs(output_dir, exist_ok=True)

        # Generalunk egy egyedi fajlnevet az idobelyeg alapjan
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = os.path.join(output_dir, f"pdf_text_{timestamp}.txt")

        # Szoveg kinyerese
        logger.debug(f"Extracting text from PDF: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                text += page_text + "\n" if page_text else ""

        # Szoveg mentese
        logger.debug(f"Saving extracted text to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"PDF text extracted and saved to: {output_file}")
        return f"Szoveg kinyerve es elmentve: {output_file}"

    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        return f"Hiba: A PDF fájl nem található: {pdf_path}"
    except PDFSyntaxError:
        logger.error(f"Invalid PDF format: {pdf_path}")
        return f"Hiba: Érvénytelen PDF formátum: {pdf_path}"
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return f"Hiba a PDF feldolgozása közben: {str(e)}"
