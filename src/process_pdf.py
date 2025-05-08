import os
from datetime import datetime
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from src.logger_setup import LoggerSetup
from config.config_manager import ConfigManager


# Konfiguráció betöltése
config = ConfigManager()
SESSION_LOG_PATH = config.get("session_log_path")

# logolas
logger_setup = LoggerSetup(SESSION_LOG_PATH)


class PDFProcessor:
    """Handles PDF file processing and text extraction."""

    def __init__(self, output_dir: str = "C:/Chat_bot/docs/output/processed_txt"):
        """Inicializálja a PDFProcessor osztályt a kimeneti mappával."""
        self.output_dir = output_dir
        self.logger = logger_setup.get_logger("PDF")
        os.makedirs(output_dir, exist_ok=True)
        if not os.path.exists(self.output_dir):
            self.logger.error("Failed to create output directory: %s", output_dir)
        self.logger.info("PDFProcessor initialized with output directory: %s", output_dir)

    def extract_pdf_text(self, pdf_file: str) -> str:
        """Kinyeri a szoveget egy PDF-bol és elmenti egy .txt fajlba."""
        # Ellenőrizzük, hogy Gradio tempfile vagy normál fájl
        # if isinstance(pdf_file, tempfile._TemporaryFileWrapper):  # javítva pylint warning miatt
        pdf_path = self._get_pdf_path(pdf_file)
        if not pdf_path:
            return "Hiba: Érvénytelen PDF fájl vagy fájlútvonal."

        if not self._validate_file(pdf_path):
            return f"Hiba: A fájl nem található vagy üres: {pdf_path}"
        self.logger.info("The file is valid!")

        self.logger.info("Starting PDF processing for: %s", pdf_path)
        return self._process_pdf(pdf_path)

    def _get_pdf_path(self, pdf_file: str) -> str:
        """Ellenőrzi és visszaadja a PDF fájl elérési útját."""
        if hasattr(pdf_file, "name"):
            pdf_path = pdf_file.name
            self.logger.info("Processing Gradio tempfile: %s", pdf_path)
            try:
                with open(pdf_path, "rb") as f:
                    header = f.read(5)
                    if not header.startswith(b"%PDF-"):
                        self.logger.error("Not a valid PDF file: %s", pdf_path)
                        return f"Hiba: A fájl nem érvényes PDF: {pdf_path}"
            except OSError as e:  # Specifikus kivétel a fájl megnyitási hibákhoz
                self.logger.error("Nem sikerült megnyitni a fájlt: %s", e)
                return f"Hiba: Nem sikerült megnyitni a fájlt: {e}"
            except Exception as e:  # Általános kivétel elkapás. pylint: disable=broad-exception-caught
                self.logger.error("Nem sikerült megnyitni a fájlt: %s", e)
                return f"Hiba: Nem sikerült megnyitni a fájlt: {e}"
        else:
            pdf_path = pdf_file
            self.logger.info("Processing file: %s", pdf_path)

        return pdf_path

    def _validate_file(self, pdf_path: str) -> bool:
        """Ellenőrzi, hogy a fájl létezik-e és nem üres-e."""
        # Fajl letezik-e
        if not os.path.exists(pdf_path):
            self.logger.error("File does not exist: %s", pdf_path)
            return False

        # Fajl meret check
        file_size = os.path.getsize(pdf_path)
        self.logger.info("File size: %d bytes", file_size)
        if file_size == 0:
            self.logger.error("File is empty: %s", pdf_path)
            return False

        return True

    def _process_pdf(self, pdf_path: str) -> str:
        """Feldolgozza a PDF-et és menti a szöveget."""
        try:
            # kimeneti mappa letezik-e
            os.makedirs(self.output_dir, exist_ok=True)

            # Generalunk egy egyedi fajlnevet az idobelyeg alapjan
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = os.path.join(self.output_dir, f"pdf_text_{timestamp}.txt")

            # Szoveg kinyerese
            self.logger.debug("Extracting text from PDF: %s", pdf_path)

            with pdfplumber.open(pdf_path) as pdf:
                text = "".join(page.extract_text() + "\n"
                               for page in pdf.pages if page.extract_text())

            # Szoveg mentese
            self.logger.debug("Saving extracted text to: %s", output_file)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            self.logger.info("PDF text extracted and saved to: %s", output_file)
            return f"Szoveg kinyerve es elmentve: {output_file}"

        except FileNotFoundError:
            self.logger.error("PDF file not found: %s", pdf_path)
            return f"Hiba: A PDF fájl nem található: {pdf_path}"
        except PDFSyntaxError:
            self.logger.error("Invalid PDF format: %s", pdf_path)
            return f"Hiba: Érvénytelen PDF formátum: {pdf_path}"
        except (Exception, OSError) as e:
            self.logger.error("Error processing PDF %s: %s", pdf_path, str(e))
            return f"Hiba a PDF feldolgozása közben: {str(e)}"

    # Azóta ignore-ba tettem
    # # Mivel a pylint szerint egy osztálynak minimum 2 public metódosa kell legyen, igí...
    # def get_extracted_files(self) -> list:
    #     """Visszaadja a kinyert szövegfájlok listáját."""
    #     return [f for f in os.listdir(self.output_dir) if f.endswith(".txt")]

# def extract_pdf_text(pdf_file, output_dir="processed_txt"):
#     """Kinyeri a szoveget egy PDF-bol és elmenti egy .txt fajlba."""
#     if isinstance(pdf_file, tempfile._TemporaryFileWrapper):
#         pdf_path = pdf_file.name
#         logger.info("Processing Gradio tempfile: %s", pdf_path)
#         try:
#             with open(pdf_path, "rb") as f:
#                 header = f.read(5)
#                 if not header.startswith(b"%PDF-"):
#                     logger.error("Not a valid PDF file: %s", pdf_path)
#                     return f"Hiba: A fájl nem érvényes PDF: {pdf_path}"
#         except Exception as e:
#             logger.error("Nem sikerült megnyitni a fájlt: %s", e)
#             return f"Hiba: Nem sikerült megnyitni a fájlt: {e}"
#     else:
#         pdf_path = pdf_file
#         logger.info("Processing file: %s", pdf_path)

#     logger.info("Starting PDF processing for: %s", pdf_path)

#     if not os.path.exists(pdf_path):
#         logger.error("File does not exist: %s", pdf_path)
#         return f"Hiba: A fájl nem található: {pdf_path}"

#     file_size = os.path.getsize(pdf_path)
#     logger.info("File size: %d bytes", file_size)
#     if file_size == 0:
#         logger.error("File is empty: %s", pdf_path)
#         return f"Hiba: A fájl üres: {pdf_path}"

#     try:
#         # kimeneti mappa letezik-e
#         os.makedirs(output_dir, exist_ok=True)

#         # Generalunk egy egyedi fajlnevet az idobelyeg alapjan
#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         output_file = os.path.join(output_dir, f"pdf_text_{timestamp}.txt")

#         # Szoveg kinyerese
#         logger.debug("Extracting text from PDF: %s", pdf_path)

#         with pdfplumber.open(pdf_path) as pdf:
#             text = ""
#             for page in pdf.pages:
#                 page_text = page.extract_text()
#                 text += page_text + "\n" if page_text else ""

#         # Szoveg mentese
#         logger.debug("Saving extracted text to: %s", output_file)
#         with open(output_file, "w", encoding="utf-8") as f:
#             f.write(text)

#         logger.info("PDF text extracted and saved to: %s", output_file)
#         return f"Szoveg kinyerve es elmentve: {output_file}"

#     except FileNotFoundError:
#         logger.error("PDF file not found: %s", pdf_path)
#         return f"Hiba: A PDF fájl nem található: {pdf_path}"
#     except PDFSyntaxError:
#         logger.error("Invalid PDF format: %s", pdf_path)
#         return f"Hiba: Érvénytelen PDF formátum: {pdf_path}"
#     except Exception as e:
#         logger.error("Error processing PDF %s: %s", pdf_path, str(e))
#         return f"Hiba a PDF feldolgozása közben: {str(e)}"
