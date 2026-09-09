"""PDF report, built from the same report structure the page renders."""

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from assessment.scoring.disc import STYLE_NAMES

_MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}


def _date_fr(dt: datetime) -> str:
    """French date without relying on the server having a fr_FR locale installed."""
    return f"Généré le {dt.day:02d} {_MOIS_FR[dt.month]} {dt.year}"
from assessment.scoring.motivators import DRIVER_BLURBS
from assessment.scoring.stress import MODE_BLURBS, MODE_LABELS

from . import components as ui
from . import plots

INK = colors.HexColor(ui.INK)
SLATE = colors.HexColor(ui.SLATE)
RULE = colors.HexColor(ui.RULE)
SIGNAL = colors.HexColor(ui.SIGNAL)


class _Numbered(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for page in self._saved:
            self.__dict__.update(page)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(SLATE)
            self.drawRightString(A4[0] - 18 * mm, 12 * mm, f"{self._pageNumber} / {total}")
            self.drawString(18 * mm, 12 * mm, "Profil DISC")
            super().showPage()
        super().save()


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                             fontSize=19, textColor=INK, spaceAfter=4, leading=22),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=12.5, textColor=INK, spaceBefore=13, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold",
                             fontSize=10.5, textColor=INK, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                               fontSize=9.4, leading=14, textColor=INK, alignment=TA_LEFT,
                               spaceAfter=5),
        "muted": ParagraphStyle("muted", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=8.4, leading=12, textColor=SLATE, spaceAfter=4),
        "chan": ParagraphStyle("chan", parent=base["BodyText"], fontName="Courier",
                               fontSize=7.4, leading=10, textColor=SLATE, spaceAfter=2),
    }


def _clean(text: str) -> str:
    """Keep the inline tags reportlab understands, drop the rest."""
    text = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", text)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"<(?!/?(b|i|br)\b)[^>]*>", "", text)


def build_pdf(report: dict, results: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
        title="Profil DISC",
    )
    s = _styles()
    flow: list = []

    flow.append(Paragraph("PROFIL DISC", s["chan"]))
    flow.append(Paragraph("Mesuré, avec sa marge d'incertitude", s["h1"]))
    flow.append(Paragraph(_date_fr(datetime.now()), s["muted"]))
    flow.append(HRFlowable(width="100%", color=RULE, spaceBefore=6, spaceAfter=10))

    for module_id, verdict in report.get("confidence", {}).items():
        if verdict["level"] == "Low":
            flow.append(Paragraph(
                f"<b>Confiance faible — {module_id.replace('_', ' ')}.</b> "
                + " ".join(_clean(r) for r in verdict["reasons"]), s["muted"]))

    if "disc" in report:
        disc = report["disc"]
        summary = results["disc_natural"].summary
        flow.append(Paragraph(_clean(disc["title"]), s["h2"]))
        flow.append(Paragraph(_clean(disc["headline"]), s["muted"]))

        image = BytesIO()
        figure = plots.circumplex(summary["normalized"],
                                  report.get("adaptive", {}).get("normalized"))
        figure.savefig(image, format="png", dpi=170, bbox_inches="tight",
                       facecolor=figure.get_facecolor())
        image.seek(0)

        rows = [["Dimension", "Score", "± erreur"]]
        for style in "DISC":
            rows.append([STYLE_NAMES[style],
                         f"{summary['normalized'][style]:.0f}",
                         f"{summary['standard_error'][style]:.0f}"])
        table = Table(rows, colWidths=[46 * mm, 18 * mm, 18 * mm])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.6),
            ("TEXTCOLOR", (0, 0), (-1, -1), INK),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        flow.append(Table([[Image(image, width=76 * mm, height=76 * mm), table]],
                          colWidths=[80 * mm, 84 * mm],
                          style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")])))
        flow.append(Paragraph(
            "Comment lire ce point. Sa direction indique le mélange de vos deux dimensions les "
            "plus fortes. Sa distance au centre indique l'intensité du profil : proche du centre, "
            "il est plus situationnel ; loin du centre, il est marqué. Les anneaux (situationnelle "
            "/ modérée / marquée) reprennent les seuils utilisés dans le texte du rapport.",
            s["muted"]))
        flow.append(Spacer(1, 6))
        flow.append(Paragraph(_clean(disc["order_claim"]), s["body"]))
        flow.append(Paragraph(_clean(disc["confidence_caveat"]), s["muted"]))
        for claim in disc["claims"]:
            flow.append(Paragraph(_clean(claim["title"]), s["h3"]))
            flow.append(Paragraph(_clean(claim["text"]), s["body"]))
        flow.append(Paragraph("Rythme et attention", s["h3"]))
        flow.append(Paragraph(_clean(disc["tempo"]), s["body"]))
        if disc.get("time_relationship"):
            flow.append(Paragraph("Votre rapport au temps", s["h3"]))
            flow.append(Paragraph(_clean(disc["time_relationship"]), s["body"]))
        flow.append(Paragraph("Avec qui il vous est le plus difficile de travailler", s["h3"]))
        for who, text in disc["friction"]:
            flow.append(Paragraph(f"<b>Pour un collègue {_clean(who)}.</b> {_clean(text)}", s["body"]))

        flow.append(Paragraph("Détail du style", s["h3"]))
        for label, key in [
            ("Forces naturelles", "strengths"),
            ("Axes de progrès", "challenges"),
            ("Comment communiquer avec vous", "communication"),
            ("Ce qui vous motive", "motivators"),
            ("Ce qui déclenche du stress", "stress_triggers"),
            ("Sous pression", "under_pressure"),
        ]:
            if disc.get(key):
                flow.append(Paragraph(f"<b>{label}.</b> {_clean(disc[key])}", s["body"]))

    if "strain" in report:
        strain = report["strain"]
        flow.append(Paragraph("Naturel vs. au travail", s["h2"]))
        flow.append(Paragraph(
            f"Indice d'écart <b>{strain['index']:.0f}</b> — charge d'adaptation {strain['band']}, "
            f"la plus marquée sur {STYLE_NAMES[strain['largest']]}.", s["body"]))
        for style in "DISC":
            shift = strain["shifts"][style]
            marker = "significatif" if shift["significant"] else "dans le bruit de mesure"
            flow.append(Paragraph(
                f"<b>{STYLE_NAMES[style]}</b> {shift['natural']:.0f} &rarr; {shift['adaptive']:.0f} "
                f"({shift['delta']:+.0f}) — {marker}", s["body"]))

    if "strengths" in report:
        flow.append(PageBreak())
        strengths = report["strengths"]
        flow.append(Paragraph("Forces caractéristiques", s["h2"]))
        flow.append(Paragraph(_clean(strengths["tie_note"]), s["muted"]))
        for rank, theme in enumerate(strengths["top"], start=1):
            flow.append(Paragraph(f"#{rank} {_clean(theme['name'])} — {_clean(theme['domain'])}", s["h3"]))
            flow.append(Paragraph(_clean(theme["description"]), s["body"]))
            flow.append(Paragraph(f"<b>À utiliser.</b> {_clean(theme['action'])}", s["body"]))
            flow.append(Paragraph(
                f"<b>Comment c'est perçu.</b> {_clean(theme['shadow'])}<br/>"
                f"<b>Quand ça vous coûte.</b> {_clean(theme['overuse'])}", s["muted"]))
        flow.append(Paragraph("Ce que vous mettez de côté", s["h3"]))
        flow.append(Paragraph(_clean(strengths["bottom_note"]), s["body"]))
        flow.append(Paragraph(
            ", ".join(f"{_clean(t['name'])} ({t['win_rate']:.0%})" for t in strengths["bottom"]),
            s["muted"]))

    if "stress" in report:
        stress = report["stress"]
        flow.append(Paragraph("Sous pression", s["h2"]))
        dominant = stress["dominant"]
        flow.append(Paragraph(f"<b>{MODE_LABELS[dominant]}.</b> {_clean(MODE_BLURBS[dominant])}", s["body"]))
        flow.append(Paragraph(
            " · ".join(f"{MODE_LABELS[m]} {stress['scores'][m]:.0f}" for m in stress["ranking"]),
            s["muted"]))

    if "motivators" in report:
        motivators = report["motivators"]
        flow.append(Paragraph("Ce qui vous motive", s["h2"]))
        top = motivators["top"][0]
        flow.append(Paragraph(f"<b>{top}.</b> {_clean(DRIVER_BLURBS[top])}", s["body"]))
        flow.append(Paragraph(
            " · ".join(f"{d} {motivators['win_rates'][d]:.0%}" for d in motivators["ranking"]),
            s["muted"]))

    if report.get("integrations"):
        flow.append(Paragraph("Là où les regards se croisent", s["h2"]))
        for section in report["integrations"]:
            flow.append(Paragraph(_clean(section["title"]), s["h3"]))
            for line in section["lines"]:
                flow.append(Paragraph(_clean(line), s["body"]))

    if report.get("plan"):
        flow.append(Paragraph("Trois choses à essayer cette semaine", s["h2"]))
        for experiment in report["plan"]:
            flow.append(Paragraph(_clean(experiment["why"]), s["chan"]))
            flow.append(Paragraph(_clean(experiment["title"]), s["h3"]))
            flow.append(Paragraph(_clean(experiment["body"]), s["body"]))

    flow.append(Spacer(1, 8))
    flow.append(HRFlowable(width="100%", color=RULE, spaceAfter=6))
    flow.append(Paragraph(
        "Les scores sont des estimations issues d'un test court et sont présentés avec leur erreur-type. "
        "Un écart plus petit que cette erreur ne constitue pas une conclusion fiable.", s["muted"]))

    doc.build(flow, canvasmaker=_Numbered)
    buffer.seek(0)
    return buffer
