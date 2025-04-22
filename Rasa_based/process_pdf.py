import pdfplumber
import os
import logging
from datetime import datetime

# Logolas beallitasa (ugyanaz, mint a gradio_app.py-ban)
logger = logging.getLogger(__name__)

def extract_pdf_text(pdf_path, output_dir="logs"):
    """Kinyeri a szoveget egy PDF-bol és elmenti egy .txt fajlba."""
    logger.info(f"Starting PDF processing for: {pdf_path}")
    
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
                text += page.extract_text() or ""
        
        # Szoveg mentese
        logger.debug(f"Saving extracted text to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"PDF text extracted and saved to: {output_file}")
        return f"Szoveg kinyerve es elmentve: {output_file}"
    
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        return f"Hiba: A PDF fájl nem található: {pdf_path}"
    except pdfplumber.PDFSyntaxError:
        logger.error(f"Invalid PDF format: {pdf_path}")
        return f"Hiba: Érvénytelen PDF formátum: {pdf_path}"
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return f"Hiba a PDF feldolgozása közben: {str(e)}"