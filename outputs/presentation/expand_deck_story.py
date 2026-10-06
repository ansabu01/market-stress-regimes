"""Story-expansion pass for the seminar deck (2026-07-04, round 2).

Adds eight narrative slides in the existing visual language and a dark SPY
sparkline strip to the title slide. The Markov-chain section (divider 02 through
the two animation slides) is left completely untouched. All numbers are verbatim
from the report/pipeline; figures come from make_expansion_figures.py or the
official notebook outputs.

Run AFTER enhance_deck.py's output is the current final_presentation_draft.pptx:
    python make_expansion_figures.py && python expand_deck_story.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

HERE = Path(__file__).resolve().parent
DECK = HERE / "final_presentation_draft.pptx"
FIGS = HERE / "figures"
ROOT = HERE.parents[1]
LOGO = ROOT / "assets" / "tum_logo.png"

NAVY = RGBColor(0x22, 0x26, 0x2E)
CALM = RGBColor(0x4C, 0x78, 0xA8)
STRESS = RGBColor(0xB2, 0x22, 0x22)
GOLD = RGBColor(0xB8, 0x86, 0x0B)
EYEBROW = RGBColor(0x6B, 0x72, 0x80)
BODY = RGBColor(0x2B, 0x2B, 0x2B)
MUTED = RGBColor(0x66, 0x70, 0x85)
CARD_FILL = RGBColor(0xF7, 0xF8, 0xFB)
CARD_LINE = RGBColor(0xE3, 0xE7, 0xEE)

LOGO_W = Inches(0.62)
LOGO_H = Inches(0.62 / 1.919)
LOGO_LEFT = Inches(10.0) - LOGO_W - Inches(0.42)
LOGO_TOP = Inches(0.26)


# --- shape helpers (matching the existing deck exactly) -------------------------

def add_logo(slide):
    slide.shapes.add_picture(str(LOGO), LOGO_LEFT, LOGO_TOP, LOGO_W, LOGO_H)


def add_dots(slide):
    for i, col in enumerate((CALM, STRESS)):
        sq = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                    Inches(0.50 + i * 0.145), Inches(0.34),
                                    Inches(0.09), Inches(0.09))
        sq.fill.solid()
        sq.fill.fore_color.rgb = col
        sq.line.fill.background()
        sq.shadow.inherit = False


def txt(slide, l, t, w, h, text, *, font="Calibri", size=13, color=BODY, bold=False,
        italic=False, align=PP_ALIGN.LEFT, spacing=None):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    if spacing is not None:
        r._r.get_or_add_rPr().set("spc", str(int(spacing)))
    return box


def bullets(slide, l, t, w, h, items, *, size=13):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        p.line_spacing = 1.14
        r = p.add_run()
        r.text = "•  " + item
        r.font.name = "Calibri"
        r.font.size = Pt(size)
        r.font.color.rgb = BODY
    return box


def place_image(slide, path, l, t, max_w, max_h, *, center_in=None):
    """Place an image preserving aspect ratio inside (max_w, max_h)."""
    with Image.open(path) as im:
        aspect = im.width / im.height
    w, h = max_w, max_w / aspect
    if h > max_h:
        h, w = max_h, max_h * aspect
    if center_in is not None:
        l = l + (center_in - w) / 2
    return slide.shapes.add_picture(str(path), Inches(l), Inches(t), Inches(w), Inches(h))


import copy

_NOTES_DONOR_SP = None  # cached deep-copyable body placeholder <p:sp>


def set_notes(prs, slide, notes: str) -> None:
    """Set presenter notes, cloning a body placeholder if the notes master lacks one."""
    global _NOTES_DONOR_SP
    ns = slide.notes_slide
    if ns.notes_text_frame is not None:
        ns.notes_text_frame.text = notes
        return
    if _NOTES_DONOR_SP is None:
        for other in prs.slides:
            if other is slide or not other.has_notes_slide:
                continue
            donor = other.notes_slide
            if donor.notes_text_frame is not None:
                _NOTES_DONOR_SP = donor.notes_text_frame._txBody.getparent()
                break
    if _NOTES_DONOR_SP is None:
        print("  [warn] no donor notes placeholder found; skipping embedded notes")
        return
    sp = copy.deepcopy(_NOTES_DONOR_SP)
    ns.shapes._spTree.append(sp)
    if ns.notes_text_frame is not None:
        ns.notes_text_frame.text = notes


def light_slide(prs, eyebrow, title, *, title_size=24, notes=""):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    add_dots(slide)
    txt(slide, 0.82, 0.22, 8.0, 0.32, eyebrow.upper(), size=10.5, color=EYEBROW,
        bold=True, spacing=300)
    txt(slide, 0.50, 0.52, 9.00, 0.92, title, font="Cambria", size=title_size,
        color=NAVY, bold=True)
    add_logo(slide)
    if notes:
        set_notes(prs, slide, notes)
    return slide


def card(slide, l, t, w, h, head, head_color, body_text):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t),
                                 Inches(w), Inches(h))
    shp.adjustments[0] = 0.055
    shp.fill.solid()
    shp.fill.fore_color.rgb = CARD_FILL
    shp.line.color.rgb = CARD_LINE
    shp.line.width = Pt(1)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.16)
    tf.margin_top = Inches(0.12)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = head
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = head_color
    p2 = tf.add_paragraph()
    p2.space_before = Pt(4)
    p2.line_spacing = 1.12
    r2 = p2.add_run()
    r2.text = body_text
    r2.font.name = "Calibri"
    r2.font.size = Pt(11)
    r2.font.color.rgb = BODY


# --- build the eight new slides -------------------------------------------------

def build_slides(prs):
    new = []

    # S_A — The promise (free-lunch floor)
    s = light_slide(
        prs, "The promise",
        "One free lunch — with a floor set by average correlation",
        notes=("- Markowitz: portfolio risk depends on co-movement, not the number of assets.\n"
               "- Equal-weight formula (report appendix): idiosyncratic risk dies at 1/N, "
               "but sigma_p converges to sqrt(rho-bar) x sigma.\n"
               "- With the measured calm cross-asset rho-bar of 0.20 the floor is 0.44; at the "
               "stress international-equity rho-bar of 0.87 it is 0.93 — adding markets buys almost nothing.\n"
               "- So the entire question is whether rho-bar stays where the calm sample says it is."))
    bullets(s, 0.50, 1.62, 3.85, 3.6, [
        "Portfolio risk is driven by co-movement, not by the number of holdings (Markowitz, 1952)",
        "Adding assets removes idiosyncratic risk — the average correlation ρ̄ sets the floor:  σₚ → √ρ̄ · σ",
        "At the calm cross-asset ρ̄ = 0.20 the floor is 0.44 σ;  at the stress international-equity ρ̄ = 0.87 it is 0.93 σ",
        "The whole promise rests on ρ̄ staying put when stress arrives — that is this paper's question",
    ])
    place_image(s, FIGS / "fig_free_lunch.png", 4.50, 1.42, 5.05, 3.95)
    new.append(s)

    # S_B — The warning (2008 vs 2022)
    s = light_slide(
        prs, "The warning",
        "Two stress episodes, two different failure modes",
        notes=("- GFC window (Oct 2007 - Jun 2009): SPY -38% at window end, TLT +14%, GLD +23% — "
               "the textbook flight-to-quality hedge worked.\n"
               "- 2022-23 window: SPY recovered to -10%, but TLT finished -39% — deeper than equities; "
               "only gold held (+9%).\n"
               "- Same word 'stress', opposite hedge behaviour -> motivates regime-conditional, "
               "episode-aware analysis instead of one full-sample correlation."))
    place_image(s, FIGS / "fig_hedges_2008_2022.png", 0.50, 1.52, 9.0, 3.30, center_in=9.0)
    txt(s, 0.50, 4.98, 9.0, 0.55,
        "2008: Treasuries +14% and gold +23% cushioned a 38% equity fall.   2022–23: long Treasuries −39% — "
        "deeper than equities — and only gold held (+9%). Same “stress”, different anatomy.",
        size=11.5, color=MUTED)
    new.append(s)

    # S_C — The reshuffle (delta heatmap)
    s = light_slide(
        prs, "Result 1 — the reshuffle",
        "A flat average hides a rotation: risk-on tightens, hedges decouple",
        notes=("- Stress-minus-calm difference matrix for the cross-asset panel.\n"
               "- Warm block: SPY-VNQ +0.21, DBC/USO-VNQ ~ +0.23 — the risk-on complex converges.\n"
               "- Cool block: TLT-VNQ -0.37, TLT-AGG -0.23 — duration decouples further.\n"
               "- 61% of the 36 pairs FALL in stress; both moves load one risk-on/risk-off axis, "
               "so the average stays flat while the structure rotates."))
    place_image(s, ROOT / "outputs" / "03_correlation_raw" / "panel_a_cross_asset_stress_minus_calm_heatmap.png",
                0.42, 1.42, 4.45, 3.95)
    bullets(s, 5.10, 1.70, 4.40, 3.6, [
        "Warm block — the risk-on complex converges: SPY–VNQ +0.21, DBC–VNQ and USO–VNQ ≈ +0.23",
        "Cool block — the safe-haven sleeve decouples: TLT–VNQ −0.37, SHY–VNQ −0.31, TLT–AGG −0.23",
        "61% of cross-asset pairs see their correlation fall in stress — the opposite of the textbook story",
        "Both moves load the same risk-on/risk-off axis: the average barely moves while the structure rotates",
    ])
    new.append(s)

    # S_D — Honest inference (fisher vs bootstrap)
    s = light_slide(
        prs, "Result 1 — honest inference",
        "Respecting serial dependence deletes a third of the “discoveries”",
        notes=("- Fisher-z assumes i.i.d. Gaussian days: flags 73 of 91 combined pairs as significant.\n"
               "- The 21-day circular block bootstrap keeps volatility clustering: 50 survive FDR control.\n"
               "- Every bootstrap discovery is also a Fisher discovery — the extra 23 are what the "
               "i.i.d. assumption fabricates.\n"
               "- Concrete case: SPY-AGG delta +0.08 -> Fisher p = 0.008, bootstrap p = 0.27."))
    place_image(s, ROOT / "outputs" / "04_correlation_bootstrapping" / "bootstrap_vs_fisher.png",
                0.42, 1.42, 4.45, 3.95)
    bullets(s, 5.10, 1.70, 4.40, 3.6, [
        "The classical Fisher-z test treats 4,711 clustered days as independent: 73 of 91 pairs look significant",
        "The 21-day block bootstrap keeps volatility clustering and regime persistence: 50 survive FDR control",
        "All 50 are also Fisher discoveries — the other 23 exist only under the i.i.d. illusion",
        "Example: SPY–AGG Δρ = +0.08 → Fisher p = 0.008, but bootstrap p = 0.27",
    ])
    new.append(s)

    # S_E — PCA mechanics (spectrum)
    s = light_slide(
        prs, "Result 2 — mechanics",
        "Stress does not create risk directions — it feeds the second axis into the first",
        title_size=22,
        notes=("- Calm cross-asset panel: two comparable axes — risk (30.8%) and rates (29.0%).\n"
               "- Stress: the leading axis pulls away (37.4% vs 23.9%).\n"
               "- Top-3 cumulative share barely moves (~76%): variance is reallocated, not created.\n"
               "- Effective bets fall 4.52 -> 4.33: about one-fifth of an independent bet lost."))
    bullets(s, 0.50, 1.70, 3.85, 3.6, [
        "Calm: the panel genuinely runs two axes side by side — a risk axis (30.8%) and a rates axis (29.0%)",
        "Stress: the leading axis pulls away — 37.4% vs 23.9%",
        "Top-3 cumulative share is unchanged (≈ 76%): variance migrates between axes, it is not created",
        "Effective bets fall 4.52 → 4.33 — the portfolio quietly loses a fifth of an independent bet",
    ])
    place_image(s, FIGS / "fig_pca_spectrum.png", 4.50, 1.42, 5.05, 3.95)
    new.append(s)

    # S_F — FR mechanism
    s = light_slide(
        prs, "Result 3 — the mechanism",
        "Why higher volatility alone inflates measured correlation",
        notes=("- Forbes-Rigobon (2002): with an unchanged linear relationship, a more volatile common "
               "factor mechanically raises the measured correlation.\n"
               "- SPY's stress variance is x3.97 its calm variance (delta = 2.97).\n"
               "- At that shock a true rho of 0.50 is MEASURED as 0.75 with zero change in dependence.\n"
               "- Hence the adjustment: deflate each stress correlation by its variance shock before "
               "calling anything contagion."))
    bullets(s, 0.50, 1.70, 3.85, 3.6, [
        "Keep the relationship fixed and only raise the market factor's variance — the measured correlation rises anyway (Forbes–Rigobon, 2002)",
        "SPY's variance is × 3.97 higher in stress (δ = 2.97)",
        "At that shock, a true ρ = 0.50 is measured as ≈ 0.75 — with no change in dependence at all",
        "So every stress correlation is deflated by its variance shock before we call anything “contagion”",
    ])
    place_image(s, FIGS / "fig_fr_mechanism.png", 4.50, 1.42, 5.05, 3.95)
    new.append(s)

    # S_G — Where resilience lives (pair_max non-SPY)
    s = light_slide(
        prs, "Result 3 — where resilience lives",
        "Resilience is a cross-asset property, not a geographic one",
        notes=("- Conservative pair-max adjustment, non-SPY pairs only.\n"
               "- Cross-asset panel: 19 of 28 pairs are genuinely resilient (green) — their correlation "
               "FELL in stress; only 2 volatility-sensitive.\n"
               "- International equity: 0 of 10 resilient, 7 volatility-bias-sensitive.\n"
               "- Diversification that survives adjustment lives across asset classes, not across borders."))
    txt(s, 0.50, 1.42, 9.0, 0.35,
        "Conservative pair-max adjustment, non-SPY pairs · green = correlation fell in stress (resilient)",
        size=11.5, color=MUTED)
    place_image(s, ROOT / "outputs" / "06_adjusted_correlation" / "forbes_rigobon_pair_max_non_spy_raw_vs_adjusted.png",
                0.50, 1.80, 9.0, 3.30, center_in=9.0)
    txt(s, 0.50, 5.14, 9.0, 0.40,
        "Cross-asset: 19 of 28 pairs genuinely resilient — Treasuries and gold de-correlate in stress.   "
        "International equity: 0 of 10 resilient.",
        size=11.5, color=MUTED)
    new.append(s)

    # S_H — Scorecard
    s = light_slide(
        prs, "Synthesis",
        "A stress scorecard for the classic diversifiers",
        notes=("- TLT: resilient on average (stress rho vs SPY -0.36) but episode-dependent — +0.10 in 2022-23.\n"
               "- GLD: steady across every episode ([+0.01, +0.15]).\n"
               "- VNQ: equity in disguise — tightens with stocks, hedges decouple from it.\n"
               "- International equity: uniform tightening, PC1 89%, no resilient pair.\n"
               "- Takeaway: different risk drivers, not more assets or more countries."))
    card(s, 0.50, 1.50, 4.42, 1.68, "Long Treasuries (TLT) — conditional hedge", CALM,
         "Resilient on average: stress correlation with SPY of −0.36, decoupling further when equities fall. "
         "But episode-dependent — it flips to +0.10 in the 2022–23 inflation stress.")
    card(s, 5.08, 1.50, 4.42, 1.68, "Gold (GLD) — the steady one", GOLD,
         "Comparatively stable across stress types: SPY–GLD stays within [+0.01, +0.15] in every episode. "
         "No sign flips, no drama — episode-robust diversification.")
    card(s, 0.50, 3.34, 4.42, 1.68, "Listed real estate (VNQ) — equity in disguise", STRESS,
         "Behaves like the risk-on complex: tightens with equities in stress (SPY–VNQ +0.21) while the true "
         "hedges decouple from it (TLT–VNQ −0.37).")
    card(s, 5.08, 3.34, 4.42, 1.68, "International equity — no crisis diversifier", STRESS,
         "All 15 pairs tighten in stress; the common factor absorbs 89% of variance. Six markets deliver "
         "barely more than one effective bet exactly when breadth should pay.")
    txt(s, 0.50, 5.16, 9.0, 0.40,
        "Stress-robust diversification needs genuinely different risk drivers — not more assets, and not more countries.",
        font="Cambria", size=13.5, color=NAVY, italic=True)
    new.append(s)

    return new


# --- title-slide sparkline strip ------------------------------------------------

def add_title_strip(prs):
    title_slide = prs.slides[0]
    strip = FIGS / "fig_title_strip.png"
    title_slide.shapes.add_picture(str(strip), Inches(0), Inches(5.02),
                                   Inches(10.0), Inches(0.60))


# --- transitions (dark beats slow, everything else medium) ----------------------

def is_dark(slide) -> bool:
    try:
        fill = slide.background.fill
        return fill.type == 1 and fill.fore_color.rgb == NAVY
    except Exception:
        return False


def apply_transitions(prs):
    for slide in prs.slides:
        sld = slide._element
        for old in sld.findall(qn("p:transition")):
            sld.remove(old)
        trans = etree.SubElement(sld, qn("p:transition"))
        trans.set("spd", "slow" if is_dark(slide) else "med")
        etree.SubElement(trans, qn("p:fade"))
        sld.remove(trans)
        clr = sld.find(qn("p:clrMapOvr"))
        csld = sld.find(qn("p:cSld"))
        anchor = clr if clr is not None else csld
        anchor.addnext(trans)


def main():
    prs = Presentation(str(DECK))
    n_orig = len(prs.slides._sldIdLst)
    assert n_orig == 18, f"expected the current 18-slide deck, found {n_orig}"

    new = build_slides(prs)
    add_title_strip(prs)

    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    o = ids[:18]
    SA, SB, SC, SD, SE, SF, SG, SH = ids[18:26]
    # Current layout: 0 Title, 1 D1, 2 Motivation, 3 Data, 4 D2, 5 how, 6 chain,
    # 7 gif5, 8 gif6, 9 regime-dating, 10 D3, 11 Corr, 12 Episode, 13 Bootstrap,
    # 14 PCA, 15 FR, 16 Dashboard, 17 Conclusion.
    # The Markov block (4-9) stays contiguous and untouched.
    new_order = [
        o[0], o[1], SA, SB, o[2], o[3],
        o[4], o[5], o[6], o[7], o[8], o[9],
        o[10], o[11], SC, o[12], o[13], SD, o[14], SE, SF, o[15], SG,
        o[16], SH, o[17],
    ]
    assert len(new_order) == 26
    for el in ids:
        sldIdLst.remove(el)
    for el in new_order:
        sldIdLst.append(el)

    apply_transitions(prs)
    prs.save(str(DECK))
    print(f"saved {DECK.name}: {len(prs.slides._sldIdLst)} slides")


if __name__ == "__main__":
    main()
