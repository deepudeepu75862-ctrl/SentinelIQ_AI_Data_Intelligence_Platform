"""PDF summary report generation."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_pdf_report(profile: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="SentinelIQ Analysis Report")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("SentinelIQ — Data Intelligence Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Automated profile and anomaly detection summary", styles["Normal"]),
        Spacer(1, 16),
    ]
    rows = [
        ["Metric", "Value"],
        ["Rows analyzed", str(profile.get("rows", 0))],
        ["Columns", str(profile.get("columns", 0))],
        ["Missing cells", str(profile.get("missing_cells", 0))],
        ["Duplicate rows", str(profile.get("duplicate_rows", 0))],
        ["Flagged anomalies", str(profile.get("flagged_rows", 0))],
        ["High alerts", str(profile.get("high_alerts", 0))],
        ["Mean demo risk score", str(profile.get("mean_risk_score", 0))],
        ["Numeric columns", ", ".join(profile.get("numeric_columns", []))],
    ]
    table = Table(rows, colWidths=[190, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    story.extend([
        Spacer(1, 18),
        Paragraph(
            "Disclaimer: anomaly flags and risk scores are heuristic indicators, not calibrated probabilities or professional advice. Review flagged records in context.",
            styles["BodyText"],
        ),
    ])
    doc.build(story)
    return buffer.getvalue()
