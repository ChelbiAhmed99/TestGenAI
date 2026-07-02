from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import io


class ReportService:
    def generate_pdf_report(self, execution_results: list, project_name: str = "Smart Test Accelerator") -> bytes:
        """
        Generates a professional PDF executive report of test results.
        """
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # ── Header bar ──
        p.setFillColor(colors.HexColor("#ED1C24"))
        p.rect(0, height - 60, width, 60, fill=True, stroke=False)

        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 22)
        p.drawString(40, height - 42, "Devoteam · Smart Test Accelerator")

        # ── Sub-header ──
        p.setFillColor(colors.HexColor("#0F172A"))
        p.setFont("Helvetica-Bold", 16)
        p.drawString(40, height - 90, "Executive Test Report")

        p.setFont("Helvetica", 11)
        p.setFillColor(colors.HexColor("#64748B"))
        p.drawString(40, height - 110, f"Project: {project_name}")
        p.drawString(40, height - 126, f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}")

        # ── Separator ──
        p.setStrokeColor(colors.HexColor("#E2E8F0"))
        p.line(40, height - 140, width - 40, height - 140)

        # ── KPI Summary ──
        total = len(execution_results)
        passed = sum(1 for r in execution_results if (r.get("status", "") or "").lower() == "passed")
        failed = sum(1 for r in execution_results if (r.get("status", "") or "").lower() == "failed")
        total_duration = sum(r.get("duration", 0) for r in execution_results)
        pass_rate = round((passed / total) * 100, 1) if total > 0 else 0
        avg_coverage = 0
        coverages = [r.get("kpis", {}).get("coverage", 0) for r in execution_results if r.get("kpis")]
        if coverages:
            avg_coverage = round(sum(coverages) / len(coverages), 1)

        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.HexColor("#0F172A"))
        p.drawString(40, height - 170, "Key Performance Indicators")

        y = height - 200
        kpis = [
            ("Total Test Runs", str(total)),
            ("Passed", f"{passed} ({pass_rate}%)"),
            ("Failed", str(failed)),
            ("Total Duration", f"{total_duration}s"),
            ("Avg Coverage", f"{avg_coverage}%"),
        ]

        p.setFont("Helvetica", 11)
        for label, value in kpis:
            p.setFillColor(colors.HexColor("#64748B"))
            p.drawString(60, y, f"• {label}:")
            p.setFillColor(colors.HexColor("#0F172A"))
            p.setFont("Helvetica-Bold", 11)
            p.drawString(220, y, value)
            p.setFont("Helvetica", 11)
            y -= 22

        # ── Separator ──
        y -= 10
        p.setStrokeColor(colors.HexColor("#E2E8F0"))
        p.line(40, y, width - 40, y)
        y -= 30

        # ── Execution Details Table ──
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(colors.HexColor("#0F172A"))
        p.drawString(40, y, "Execution Details")
        y -= 30

        # Table header
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.HexColor("#64748B"))
        p.drawString(60, y, "Test Name")
        p.drawString(280, y, "Status")
        p.drawString(370, y, "Duration")
        p.drawString(450, y, "Coverage")
        y -= 6
        p.setStrokeColor(colors.HexColor("#CBD5E1"))
        p.line(40, y, width - 40, y)
        y -= 18

        p.setFont("Helvetica", 10)
        for result in execution_results:
            if y < 80:
                p.showPage()
                y = height - 60

            name = result.get("name", f"Test #{result.get('id', '?')}")
            status = result.get("status", "unknown")
            duration = result.get("duration", 0)
            coverage = result.get("kpis", {}).get("coverage", "—") if result.get("kpis") else "—"

            p.setFillColor(colors.HexColor("#0F172A"))
            p.drawString(60, y, str(name)[:35])

            # Color-coded status
            status_lower = str(status).lower()
            if status_lower == "passed":
                p.setFillColor(colors.HexColor("#10B981"))
            elif status_lower == "failed":
                p.setFillColor(colors.HexColor("#EF4444"))
            else:
                p.setFillColor(colors.HexColor("#F59E0B"))
            p.setFont("Helvetica-Bold", 10)
            p.drawString(280, y, str(status).upper())

            p.setFont("Helvetica", 10)
            p.setFillColor(colors.HexColor("#0F172A"))
            p.drawString(370, y, f"{duration}s")
            p.drawString(450, y, f"{coverage}%" if coverage != "—" else "—")
            y -= 20

        # ── Footer ──
        p.setFont("Helvetica", 8)
        p.setFillColor(colors.HexColor("#94A3B8"))
        p.drawString(40, 30, f"Devoteam Smart Test Accelerator — Confidential — {datetime.now().strftime('%Y')}")
        p.drawRightString(width - 40, 30, "Powered by Gemini AI")

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        return pdf


report_service = ReportService()
