# import unittest
# from unittest.mock import patch, MagicMock
# import os
# from src.process_pdf import PDFProcessor
# from config.config_manager import ConfigManager
# from src.logger_setup import LoggerSetup

# class TestPDFProcessor(unittest.TestCase):
#     def setUp(self):
#         # Konfiguráció és naplózás inicializálása
#         self.config = ConfigManager()
#         self.session_log_path = self.config.get("session_log_path")
#         self.logger_setup = LoggerSetup(self.session_log_path)
#         self.output_dir = "test_output"
#         self.processor = PDFProcessor(output_dir=self.output_dir)

#     def tearDown(self):
#         # Tesztek utáni takarítás (kimeneti mappa törlése, ha létezik)
#         import shutil
#         if os.path.exists(self.output_dir):
#             shutil.rmtree(self.output_dir)

#     @patch("pdfplumber.open")
#     def test_extract_pdf_text_success(self, mock_pdf_open):
#         # Mockoljuk a pdfplumber viselkedését
#         mock_pdf = MagicMock()
#         mock_page = MagicMock()
#         mock_page.extract_text.return_value = "Ez egy teszt szöveg"
#         mock_pdf.pages = [mock_page]
#         mock_pdf_open.return_value.__enter__.return_value = mock_pdf

#         # Teszteljük a szöveg kinyerését
#         pdf_path = "dummy.pdf"
#         result = self.processor.extract_pdf_text(pdf_path)

#         # Ellenőrizzük, hogy a kimeneti fájl létrejött
#         self.assertTrue(os.path.exists(self.output_dir))
#         output_files = os.listdir(self.output_dir)
#         self.assertEqual(len(output_files), 1)
#         self.assertIn("Szoveg kinyerve es elmentve", result)

#     def test_extract_pdf_text_invalid_file(self):
#         # Teszteljük, mi történik, ha a fájl nem létezik
#         pdf_path = "non_existent.pdf"
#         result = self.processor.extract_pdf_text(pdf_path)

#         self.assertEqual(result, f"Hiba: A fájl nem található: {pdf_path}")

#     def test_extract_pdf_text_empty_file(self):
#         # Teszteljük, mi történik, ha a fájl üres
#         with patch("os.path.exists", return_value=True), \
#              patch("os.path.getsize", return_value=0):
#             pdf_path = "empty.pdf"
#             result = self.processor.extract_pdf_text(pdf_path)

#             self.assertEqual(result, f"Hiba: A fájl üres: {pdf_path}")

# if __name__ == '__main__':
#     unittest.main()