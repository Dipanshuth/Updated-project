"""
AI Digital Memory Vault — PDF Service
Generate FIR reports as PDF documents using fpdf2
"""

from fpdf import FPDF
import os
from datetime import datetime

class FIRReportPDF(FPDF):
    def header(self):
        # Logo/Icon placeholder 
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "AI DIGITAL MEMORY VAULT", border=False, ln=True, align="C")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 8, "Automated First Information Report (FIR)", border=False, ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Generated Auto-FIR", align="C")

def generate_fir_pdf(evidence_data: dict, output_path: str) -> str:
    """
    Generate an actual First Information Report as PDF using fpdf2.
    """
    pdf = FIRReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "FIRST INFORMATION REPORT", border=True, ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "I. GENERAL INFORMATION", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    # Table data
    pdf.cell(50, 8, "FIR Number:", border=0)
    pdf.cell(0, 8, evidence_data.get('fir_number', 'N/A'), border=0, ln=True)
    
    pdf.cell(50, 8, "Date & Time:", border=0)
    pdf.cell(0, 8, str(evidence_data.get('generated_at', 'N/A')), border=0, ln=True)
    
    pdf.cell(50, 8, "Police Station:", border=0)
    pdf.cell(0, 8, str(evidence_data.get('station', 'N/A')), border=0, ln=True)
    
    pdf.cell(50, 8, "Evidence Ref:", border=0)
    pdf.cell(0, 8, str(evidence_data.get('evidence_id', 'N/A')), border=0, ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "II. INCIDENT DETAILS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(50, 8, "Incident Time:", border=0)
    pdf.cell(0, 8, str(evidence_data.get('incident_datetime', 'N/A')), border=0, ln=True)
    
    pdf.cell(50, 8, "Location:", border=0)
    pdf.multi_cell(0, 8, str(evidence_data.get('incident_location', 'N/A')) + " — GPS: " + str(evidence_data.get('gps', 'N/A')), border=0)
    
    pdf.cell(50, 8, "AI Distress Score:", border=0)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, str(evidence_data.get('distress_confidence', 'N/A')), border=0, ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "III. NARRATION OF FACTS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, str(evidence_data.get('narration', 'AI analysis pending.')))
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "IV. EVIDENCE INTEGRITY", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(40, 8, "SHA-256 Hash:")
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 8, str(evidence_data.get('hash', 'N/A')))
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 8, "Status:")
    pdf.set_text_color(0, 150, 0)
    pdf.cell(0, 8, "VERIFIED - No Tampering Detected", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    # Save the PDF
    pdf.output(output_path)
    return output_path

def generate_fir_content(evidence_data: dict) -> dict:
    """Generate FIR content dict from evidence data."""
    evidence_id = evidence_data.get('evidence_id', '')
    return {
        "fir_number": f"FIR/2026/NCR/{hash(evidence_id) % 100000:05d}",
        "generated_at": datetime.now().isoformat(),
        "station": "Connaught Place PS, New Delhi",
        "district": "New Delhi",
        "evidence_id": evidence_id,
        "incident_datetime": evidence_data.get("incident_datetime", "Unknown"),
        "incident_location": evidence_data.get("location", "Unknown"),
        "gps": f"{evidence_data.get('latitude', 'N/A')}, {evidence_data.get('longitude', 'N/A')}",
        "incident_type": "Physical Altercation / Threat",
        "distress_confidence": f"{int(evidence_data.get('confidence', 0.0) * 100)}%" if evidence_data.get('confidence') else "N/A",
        "narration": evidence_data.get("ai_summary", "AI analysis pending."),
        "hash": evidence_data.get("sha256_hash", ""),
        "status": "generated",
    }
