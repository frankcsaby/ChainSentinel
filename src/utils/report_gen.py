import pandas as pd
from fpdf import FPDF
from datetime import datetime
from loguru import logger
from config.settings import settings
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{settings.APP_NAME} Report', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

class ReportGenerator:
    @staticmethod
    def create_pdf(data: dict, token_name: str):
        """
        Létrehoz egy PDF jelentést az AI elemzés alapján.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{token_name}_{timestamp}.pdf"
            filepath = settings.REPORT_DIR / filename
            
            pdf = PDFReport()
            pdf.add_page()
            
            # Cím
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"AUDIT REPORT: {token_name.upper()}", 0, 1, "C")
            pdf.ln(5)

            # Verdikt
            verdict = data.get('verdict', 'UNKNOWN')
            score = data.get('score', 0)
            
            pdf.set_font("Arial", "B", 14)
            if verdict == 'Safe':
                pdf.set_text_color(0, 150, 0)
            elif verdict == 'Scam':
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(255, 140, 0)
                
            pdf.cell(0, 10, f"VERDICT: {verdict} (Score: {score}/100)", 0, 1, "C")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)

            # Tartalom (Summary, Pros, Cons)
            sections = {
                "Executive Summary": data.get('summary', 'No summary provided.'),
                "Pros (Strengths)": "\n".join([f"+ {p}" for p in data.get('pros', [])]),
                "Cons (Risks)": "\n".join([f"- {c}" for c in data.get('cons', [])])
            }

            for title, content in sections.items():
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, title, 0, 1)
                pdf.set_font("Arial", "", 11)
                
                # Unicode karakterek kezelése (latin-1 fallback)
                safe_content = str(content).encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, safe_content)
                pdf.ln(5)

            pdf.output(str(filepath))
            logger.info(f"PDF elmentve: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Hiba a PDF generáláskor: {e}")
            return None

    @staticmethod
    def export_to_excel(data: list, filename: str = "portfolio_export"):
        """
        Adatok exportálása Excelbe.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            filepath = settings.REPORT_DIR / f"{filename}_{timestamp}.xlsx"
            
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
            logger.info(f"Excel elmentve: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Hiba az Excel exportnál: {e}")
            return None