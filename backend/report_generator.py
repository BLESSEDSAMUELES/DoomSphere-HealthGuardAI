"""
PDF Report Generator Module
Creates professional medical scan analysis reports in PDF format.
"""

import os
import datetime
from fpdf import FPDF


class MedicalReportPDF(FPDF):
    """Custom PDF class for medical reports."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        # Brand bar
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 18, 'F')

        self.set_font("Helvetica", "B", 11)
        self.set_text_color(56, 189, 248)
        self.set_y(4)
        self.cell(0, 10, "HEALTHGUARD AI", ln=False, align="L")

        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "Medical Scan Analysis Report", ln=True, align="R")

        self.ln(8)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(51, 65, 85)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="L", ln=False)
        self.cell(0, 8,
                  "DISCLAIMER: AI-assisted analysis. Not a substitute for professional medical diagnosis.",
                  align="R", ln=True)

    def add_section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(56, 189, 248)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(56, 189, 248)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def add_key_value(self, key, value, severity=None):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(148, 163, 184)
        self.cell(55, 7, key + ":", ln=False)

        self.set_font("Helvetica", "", 9)
        if severity == "high":
            self.set_text_color(239, 68, 68)
        elif severity == "medium":
            self.set_text_color(251, 191, 36)
        elif severity == "low":
            self.set_text_color(52, 211, 153)
        else:
            self.set_text_color(226, 232, 240)

        self.cell(0, 7, str(value), ln=True)

    def add_finding_card(self, finding: dict, index: int):
        # Card background
        y_start = self.get_y()
        self.set_fill_color(30, 41, 59)
        self.rect(10, y_start, 190, 28, 'F')

        # Severity indicator
        severity = finding.get("severity", "medium")
        if severity == "high":
            self.set_fill_color(239, 68, 68)
        elif severity == "medium":
            self.set_fill_color(251, 191, 36)
        else:
            self.set_fill_color(52, 211, 153)
        self.rect(10, y_start, 3, 28, 'F')

        # Finding name
        self.set_xy(16, y_start + 2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(226, 232, 240)
        self.cell(120, 6, f"{index}. {finding['finding']}", ln=False)

        # Confidence badge
        self.set_font("Helvetica", "B", 9)
        conf = finding["confidence"]
        self.cell(0, 6, f"{conf}% confidence", ln=True, align="R")

        # Description
        self.set_x(16)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(148, 163, 184)
        desc = finding.get("description", "")
        if len(desc) > 150:
            desc = desc[:147] + "..."
        self.multi_cell(180, 4, desc)

        self.ln(4)


def generate_report(
    scan_type_result: dict,
    analysis_result: dict,
    original_filename: str,
    output_dir: str,
    images_dir: str,
) -> str:
    """
    Generate a comprehensive PDF report.
    Returns the filename of the generated PDF.
    """
    pdf = MedicalReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Report Title ---
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(226, 232, 240)
    pdf.cell(0, 12, "Scan Analysis Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    now = datetime.datetime.now()
    pdf.cell(0, 6, f"Generated on {now.strftime('%B %d, %Y at %I:%M %p')}", ln=True, align="C")
    pdf.ln(8)

    # --- Patient / File Info ---
    pdf.add_section_title("Scan Information")
    pdf.add_key_value("File Name", original_filename)
    pdf.add_key_value("Scan Type", scan_type_result.get("scan_type", "Unknown"))
    pdf.add_key_value("Type Confidence", f"{scan_type_result.get('confidence', 0)}%")
    pdf.add_key_value("Resolution", scan_type_result.get("features", {}).get("resolution", "N/A"))
    pdf.add_key_value("Analysis Date", now.strftime("%Y-%m-%d %H:%M:%S"))
    pdf.add_key_value("Model", analysis_result.get("model_info", {}).get("name", "HealthGuard AI"))
    pdf.ln(4)

    # --- Scan Type Description ---
    desc = scan_type_result.get("description", "")
    if desc:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(4)

    # --- Overall Assessment ---
    pdf.add_section_title("Overall Assessment")
    severity = analysis_result.get("overall_severity", "medium")
    pdf.add_key_value("Overall Severity", severity.upper(), severity=severity)
    pdf.add_key_value("Primary Finding", analysis_result.get("primary_finding", "N/A"),
                      severity=severity)
    pdf.ln(6)

    # --- Findings ---
    pdf.add_section_title("Detailed Findings")
    findings = analysis_result.get("findings", [])
    for i, finding in enumerate(findings, 1):
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.add_finding_card(finding, i)

    # --- Images ---
    pdf.add_page()
    pdf.add_section_title("Visual Analysis")

    # Original scan
    # Heatmap
    heatmap_file = analysis_result.get("heatmap_path", "")
    heatmap_full = os.path.join(images_dir, heatmap_file)
    if heatmap_file and os.path.exists(heatmap_full):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(226, 232, 240)
        pdf.cell(0, 8, "GradCAM Heatmap Analysis", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 5, "Warmer colors indicate regions most relevant to the AI prediction.", ln=True)
        pdf.ln(2)
        try:
            pdf.image(heatmap_full, x=30, w=150)
        except Exception:
            pdf.cell(0, 8, "[Heatmap image could not be loaded]", ln=True)
        pdf.ln(6)

    # Annotated
    annotated_file = analysis_result.get("annotated_path", "")
    annotated_full = os.path.join(images_dir, annotated_file)
    if annotated_file and os.path.exists(annotated_full):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(226, 232, 240)
        pdf.cell(0, 8, "Annotated Regions of Interest", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(0, 5,
                 "Green boxes and yellow contours highlight AI-identified regions of interest.",
                 ln=True)
        pdf.ln(2)
        try:
            pdf.image(annotated_full, x=30, w=150)
        except Exception:
            pdf.cell(0, 8, "[Annotated image could not be loaded]", ln=True)
        pdf.ln(6)

    # --- Disclaimer ---
    pdf.add_page()
    pdf.add_section_title("Important Disclaimer")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(148, 163, 184)
    disclaimer = (
        "This report has been generated by HealthGuard AI, an artificial intelligence-based "
        "medical scan analysis system. The findings and predictions presented in this report "
        "are AI-generated and should NOT be used as a sole basis for medical diagnosis or "
        "treatment decisions.\n\n"
        "This tool is designed to assist healthcare professionals by providing preliminary "
        "analysis and highlighting potential areas of interest. All findings should be reviewed "
        "and validated by qualified medical professionals.\n\n"
        "The AI model uses deep learning techniques including DenseNet-121 architecture with "
        "GradCAM visualization. While the model has been trained on medical imaging data, "
        "it may produce false positives or miss findings. Always consult with a licensed "
        "healthcare provider for proper diagnosis and treatment.\n\n"
        "HealthGuard AI and its developers are not liable for any medical decisions made "
        "based on the outputs of this system."
    )
    pdf.multi_cell(0, 5, disclaimer)

    # Save PDF
    report_filename = f"HealthGuard_Report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    report_path = os.path.join(output_dir, report_filename)
    pdf.output(report_path)

    return report_filename
