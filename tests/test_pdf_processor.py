import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
from src.process_pdf import PDFProcessor
from src.logger_setup import LoggerSetup
from config.config_manager import ConfigManager
from pdfminer.pdfparser import PDFSyntaxError
import pdfplumber


class TestPDFProcessor(unittest.TestCase):
    def setUp(self):
        # Mockoljuk a környezeti változókat
        os.environ["SESSION_LOG_PATH"] = "logs/test_session.log"

        # Konfiguráció és naplózás inicializálása
        self.config = ConfigManager()
        self.logger_setup = LoggerSetup(self.config.get("session_log_path"))
        self.output_dir = os.path.join(os.path.expanduser("~"), "test_output")
        self.processor = PDFProcessor(output_dir=self.output_dir)

    def tearDown(self):
        # Tesztek utáni takarítás: kimeneti mappa törlése
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_init_failed_directory_creation(self, mock_makedirs, mock_exists):
        """Teszteli, ha a kimeneti mappa létrehozása sikertelen."""
        # Mockoljuk, hogy a mappa nem létezik
        mock_exists.return_value = False
        # Mockoljuk, hogy os.makedirs nem dob kivételt, mert exist_ok=True
        mock_makedirs.return_value = None

        with patch.object(self.logger_setup.get_logger("PDF"), 'error') as mock_error:
            processor = PDFProcessor(output_dir="invalid_dir")
            mock_error.assert_called_once_with("Failed to create output directory: %s", "invalid_dir")
            self.assertEqual(processor.output_dir, "invalid_dir")
            mock_makedirs.assert_called_once_with("invalid_dir", exist_ok=True)

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    def test_extract_pdf_text_success(self, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli a sikeres szövegkinyerést és mentést."""
        # Mockoljuk a fájl létezését és méretét
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # Nem üres fájl

        # Mockoljuk a pdfplumber viselkedését
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Ez egy teszt szöveg"
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        pdf_path = "test.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        # Ellenőrizzük a kimeneti fájlt és az eredményt
        self.assertTrue(os.path.exists(self.output_dir))
        output_files = os.listdir(self.output_dir)
        self.assertEqual(len(output_files), 1)
        with open(os.path.join(self.output_dir, output_files[0]), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "Ez egy teszt szöveg\n")
        self.assertIn("Szoveg kinyerve es elmentve:", result)

    @patch("os.path.exists")
    def test_extract_pdf_text_file_not_found(self, mock_exists):
        """Teszteli, ha a PDF fájl nem létezik."""
        mock_exists.return_value = False
        pdf_path = "non_existent.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        self.assertEqual(result, f"Hiba: A fájl nem található vagy üres: {pdf_path}")
        self.assertEqual(len(os.listdir(self.output_dir)), 0)  # Nincs fájl a mappában

    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_extract_pdf_text_empty_file(self, mock_getsize, mock_exists):
        """Teszteli, ha a PDF fájl üres."""
        mock_exists.return_value = True
        mock_getsize.return_value = 0
        pdf_path = "empty.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        self.assertEqual(result, f"Hiba: A fájl nem található vagy üres: {pdf_path}")
        self.assertTrue(os.path.exists(self.output_dir))  # A mappa letrejon az __init__-ben
        self.assertEqual(len(os.listdir(self.output_dir)), 0)  # De nincs benne fajl

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    def test_extract_pdf_text_no_text(self, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli, ha a PDF nem tartalmaz szöveget."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # ures szoveg, kesobb tesztelheto ''-re is talan
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        pdf_path = "no_text.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        self.assertTrue(os.path.exists(self.output_dir))
        output_files = os.listdir(self.output_dir)
        self.assertEqual(len(output_files), 1)
        with open(os.path.join(self.output_dir, output_files[0]), 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "")
        self.assertIn("Szoveg kinyerve es elmentve:", result)

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    def test_extract_pdf_text_invalid_pdf(self, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli, ha a PDF fájl érvénytelen."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_pdf_open.side_effect = PDFSyntaxError("Invalid PDF structure")
        pdf_path = "invalid.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        self.assertEqual(result, f"Hiba: Érvénytelen PDF formátum: {pdf_path}")
        self.assertTrue(os.path.exists(self.output_dir))  # A mappa létrejön az __init__-ben
        self.assertEqual(len(os.listdir(self.output_dir)), 0)  # De nincs benne fájl

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    def test_extract_pdf_text_general_exception(self, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli, ha a PDF feldolgozása közben általános kivétel történik."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_pdf_open.side_effect = Exception("PDF processing error")
        pdf_path = "error.pdf"
        result = self.processor.extract_pdf_text(pdf_path)

        self.assertEqual(result, "Hiba a PDF feldolgozása közben: PDF processing error")
        self.assertTrue(os.path.exists(self.output_dir))  # A mappa letrejon az __init__-ben
        self.assertEqual(len(os.listdir(self.output_dir)), 0)  # De nincs benne fajl

    @patch("os.path.exists")
    def test_extract_pdf_text_invalid_path(self, mock_exists):
        """Teszteli, ha érvénytelen fájlútvonalat adnak meg."""
        mock_exists.return_value = True
        result = self.processor.extract_pdf_text(None)

        self.assertEqual(result, "Hiba: Érvénytelen PDF fájl vagy fájlútvonal.")
        self.assertTrue(os.path.exists(self.output_dir))  # A mappa letrejon az __init__-ben
        self.assertEqual(len(os.listdir(self.output_dir)), 0)  # De nincs benne fajl

    @patch("builtins.open")
    def test_get_pdf_path_tempfile_valid_pdf(self, mock_open):
        """Teszteli a Gradio tempfile esetet érvényes PDF fájllal."""
        tempfile_mock = MagicMock()
        tempfile_mock.name = "temp.pdf"
        mock_file = MagicMock()
        mock_file.read.return_value = b"%PDF-1.4"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.processor._get_pdf_path(tempfile_mock)
        self.assertEqual(result, "temp.pdf")
        mock_open.assert_called_once_with("temp.pdf", "rb")

    @patch("builtins.open")
    def test_get_pdf_path_tempfile_invalid_pdf(self, mock_open):
        """Teszteli a Gradio tempfile esetet érvénytelen PDF fájllal."""
        tempfile_mock = MagicMock()
        tempfile_mock.name = "temp.pdf"
        mock_file = MagicMock()
        mock_file.read.return_value = b"NOT_A_PDF"
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.processor._get_pdf_path(tempfile_mock)
        self.assertEqual(result, "Hiba: A fájl nem érvényes PDF: temp.pdf")
        mock_open.assert_called_once_with("temp.pdf", "rb")

    @patch("builtins.open")
    def test_get_pdf_path_tempfile_oserror(self, mock_open):
        """Teszteli a Gradio tempfile esetet OSError kivétellel."""
        tempfile_mock = MagicMock()
        tempfile_mock.name = "temp.pdf"
        mock_open.side_effect = OSError("Permission denied")

        result = self.processor._get_pdf_path(tempfile_mock)
        self.assertEqual(result, "Hiba: Nem sikerült megnyitni a fájlt: Permission denied")
        mock_open.assert_called_once_with("temp.pdf", "rb")

    @patch("builtins.open")
    def test_get_pdf_path_tempfile_general_exception(self, mock_open):
        """Teszteli a Gradio tempfile esetet általános kivétellel."""
        tempfile_mock = MagicMock()
        tempfile_mock.name = "temp.pdf"
        mock_open.side_effect = Exception("Unexpected error")

        result = self.processor._get_pdf_path(tempfile_mock)
        self.assertEqual(result, "Hiba: Nem sikerült megnyitni a fájlt: Unexpected error")
        mock_open.assert_called_once_with("temp.pdf", "rb")

    def test_get_pdf_path_regular_file(self):
        """Teszteli a normál fájl esetet."""
        pdf_path = "regular.pdf"
        result = self.processor._get_pdf_path(pdf_path)
        self.assertEqual(result, "regular.pdf")

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    @patch("builtins.open")
    def test_process_pdf_oserror(self, mock_open, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli az OSError kivételt a _process_pdf metódusban."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Ez egy teszt szöveg"
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Mockoljuk az írási hibát
        mock_open.side_effect = OSError("Permission denied")

        pdf_path = "test.pdf"
        result = self.processor._process_pdf(pdf_path)

        self.assertEqual(result, "Hiba a PDF feldolgozása közben: Permission denied")
        self.assertTrue(os.path.exists(self.output_dir))
        self.assertEqual(len(os.listdir(self.output_dir)), 0)

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("pdfplumber.open")
    def test_process_pdf_file_not_found(self, mock_pdf_open, mock_getsize, mock_exists):
        """Teszteli a FileNotFoundError kivételt a _process_pdf metódusban."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_pdf_open.side_effect = FileNotFoundError("File not found")
        pdf_path = "test.pdf"
        result = self.processor._process_pdf(pdf_path)
        self.assertEqual(result, f"Hiba: A PDF fájl nem található: {pdf_path}")
        self.assertTrue(os.path.exists(self.output_dir))
        self.assertEqual(len(os.listdir(self.output_dir)), 0)


if __name__ == '__main__':
    unittest.main()
