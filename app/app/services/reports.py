from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stats import dashboard, revenue_by_engineer


async def monthly_report(session: AsyncSession) -> tuple[str, bytes]:
    text = await dashboard(session)
    revenue = await revenue_by_engineer(session)
    full_text = f"{text}\n\n{revenue}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Monthly studio report")
    y = 800
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, f"Monthly studio report {datetime.now():%Y-%m}")
    y -= 30
    pdf.setFont("Helvetica", 10)
    for raw_line in full_text.replace("<b>", "").replace("</b>", "").splitlines():
        if y < 50:
            pdf.showPage()
            y = 800
            pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, raw_line[:110])
        y -= 16
    pdf.save()
    return full_text, buffer.getvalue()

