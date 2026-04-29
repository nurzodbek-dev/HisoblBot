import io
import logging
import os
import tempfile
from datetime import datetime

from fpdf import FPDF

logger = logging.getLogger(__name__)


class ReportPDF(FPDF):
    def __init__(self, title: str = "Hisobot"):
        super().__init__()
        self._report_title = title

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, self._report_title, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(
            0, 5,
            f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            new_x="LMARGIN", new_y="NEXT", align="C",
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"HisoblBot - Sahifa {self.page_no()}/{{nb}}", align="C")


def generate_report_pdf(
    summary: dict,
    transactions: list,
    period_label: str = "Haftalik",
    business_name: str | None = None,
) -> str:
    """Generate a PDF report and return the file path."""

    title = f"{business_name or 'HisoblBot'} - {period_label} hisobot"
    pdf = ReportPDF(title=title)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Summary section
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Moliyaviy xulosa", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    income = summary.get("total_income", 0)
    expense = summary.get("total_expense", 0)
    profit = summary.get("net_profit", 0)
    tx_count = summary.get("transaction_count", 0)

    rows = [
        ("Jami daromad:", f"{income:,.0f} UZS"),
        ("Jami xarajat:", f"{expense:,.0f} UZS"),
        ("Sof foyda:", f"{profit:,.0f} UZS"),
        ("Tranzaksiyalar soni:", str(tx_count)),
    ]
    for label, value in rows:
        pdf.cell(80, 7, label)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Expense by category
    expense_cats = summary.get("expense_by_category", [])
    if expense_cats:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Xarajatlar bo'yicha:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

        # Table header
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(70, 7, "Kategoriya", border=1, fill=True)
        pdf.cell(50, 7, "Summa (UZS)", border=1, fill=True)
        pdf.cell(30, 7, "Soni", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        for cat in expense_cats:
            pdf.cell(70, 7, cat["category"], border=1)
            pdf.cell(50, 7, f"{cat['total']:,.0f}", border=1)
            pdf.cell(30, 7, str(cat["count"]), border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Income by category
    income_cats = summary.get("income_by_category", [])
    if income_cats:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Daromadlar bo'yicha:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

        pdf.set_fill_color(220, 220, 220)
        pdf.cell(70, 7, "Kategoriya", border=1, fill=True)
        pdf.cell(50, 7, "Summa (UZS)", border=1, fill=True)
        pdf.cell(30, 7, "Soni", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        for cat in income_cats:
            pdf.cell(70, 7, cat["category"], border=1)
            pdf.cell(50, 7, f"{cat['total']:,.0f}", border=1)
            pdf.cell(30, 7, str(cat["count"]), border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Transaction list
    if transactions:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Tranzaksiyalar ro'yxati:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)

        # Table header
        pdf.set_fill_color(220, 220, 220)
        col_widths = [30, 20, 40, 45, 55]
        headers = ["Sana", "Turi", "Summa", "Kategoriya", "Tavsif"]
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 6, h, border=1, fill=True)
        pdf.ln()

        for tx in transactions[:100]:  # Limit to 100 rows
            created = tx.created_at.strftime("%m-%d %H:%M") if hasattr(tx, "created_at") else ""
            tx_type = "Kirim" if (hasattr(tx, "type") and tx.type.value == "income") else "Chiqim"
            amount_str = f"{tx.amount:,.0f}" if hasattr(tx, "amount") else ""
            category = (tx.category or "")[:20] if hasattr(tx, "category") else ""
            item = (tx.item or "")[:25] if hasattr(tx, "item") else ""

            # Check if we need a new page
            if pdf.get_y() > 270:
                pdf.add_page()
                pdf.set_font("Helvetica", "", 9)

            pdf.cell(col_widths[0], 6, created, border=1)
            pdf.cell(col_widths[1], 6, tx_type, border=1)
            pdf.cell(col_widths[2], 6, amount_str, border=1)
            pdf.cell(col_widths[3], 6, category, border=1)
            pdf.cell(col_widths[4], 6, item, border=1)
            pdf.ln()

    # Tax estimate
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Soliq taxmini:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    tax_simplified = income * 0.04
    pdf.cell(80, 7, "Yagona soliq (4%):")
    pdf.cell(0, 7, f"{tax_simplified:,.0f} UZS", new_x="LMARGIN", new_y="NEXT")

    if income > 1_000_000_000:
        vat = income * 0.12
        pdf.cell(80, 7, "QQS (12%):")
        pdf.cell(0, 7, f"{vat:,.0f} UZS", new_x="LMARGIN", new_y="NEXT")

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".pdf", prefix=f"hisobot_{period_label}_"
    )
    pdf.output(tmp.name)
    tmp.close()
    return tmp.name
