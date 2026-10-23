"""Extraction et nettoyage du corpus juridique sénégalais (Personne 1).

Lit data/manifest.csv, extrait le texte des originaux de data/raw/ et le nettoie
sans perdre les titres, la numérotation des articles ni les numéros de page.

  - PDF textuel : PyMuPDF, lecture bloc par bloc en respectant les colonnes
    (le Code de la famille est mis en page sur 3 colonnes) ; repli pypdf.
  - PDF scanné : OCR tesseract (fra) page par page, mis en cache dans data/processed/ocr/
    pour que l'équipe puisse relancer sans tesseract. Les fichiers du cache
    peuvent être corrigés à la main : ils sont alors prioritaires.
  - HTML : BeautifulSoup ; TXT : lecture directe.

Sorties dans data/processed/ :
  <doc_id>.txt          texte nettoyé avec marqueurs de page  [[page N]]
  <doc_id>.json         métadonnées + qualité + pages + articles détectés
  articles.jsonl        une ligne par article : format d'échange pour la personne 2
  quality_report.csv    contrôle de lisibilité par document
  traceability_report.csv  contrôle de traçabilité : chaque unité est-elle retrouvée
                        dans sa page source ? (comparaison sur texte normalisé)
  ocr/<pdf>/pNNN.txt    cache OCR (une page = un fichier, corrigeable à la main)

Colonnes du manifeste utilisées : id, titre, titre_court, organisme, type_document,
url, format, fichier_local, pages_debut, pages_fin, filtre, options,
date_consultation, version_texte, ingerer.
  filtre  : "livre=LIVRE II" | "livre=LIVRE VII&titre=TITRE III" | "articles=338-351" (vide = tout)
  options : "ocr=oui" (OCR des pages scannées) | "ocr=force" (OCR de toutes les pages)
            "intitules=oui" (intitulés d'articles en gras sous « Article N »)
            "pages=oui" (document explicatif découpé par page, pas par article)
            "ocr_relu=oui" (le cache OCR a été relu et corrigé contre l'image)

Usage :
  python src/ingest.py                    # tout le manifeste (ingerer=oui) puis contrôle de traçabilité
  python src/ingest.py --only constitution   # un seul document (n'écrase pas articles.jsonl)
  python src/ingest.py --ocr              # OCR en lot des pages scannées absentes du cache, puis ingestion
  python src/ingest.py --controle --sample 3   # contrôle de traçabilité seul (+ 3 passages au hasard)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
OCR_CACHE = PROCESSED / "ocr"  # cache OCR, corrigeable à la main
MANIFEST = DATA / "manifest.csv"

BOLD = "⟦B⟧"  # marqueur interne d'une ligne en gras (retiré à la sortie)

# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------


def _column_starts(blocks) -> list[float]:
    """Abscisses de début de colonne, ou [0] si la page est sur une seule colonne.

    Les x0 des blocs sont regroupés (écart > 60 pt = nouvelle colonne) ; la mise en
    colonnes n'est retenue que si ~90 % des blocs tiennent entièrement dans une bande.
    """
    xs = sorted(b["bbox"][0] for b in blocks)
    if not xs:
        return [0.0]
    starts = [xs[0]]
    for a, b in zip(xs, xs[1:]):
        if b - a > 60:
            starts.append(b)
    if len(starts) == 1:
        return [0.0]
    bounds = starts[1:] + [float("inf")]

    def band(x):
        return max(i for i, s0 in enumerate(starts) if x + 10 >= s0) if x + 10 >= starts[0] else 0

    fits = sum(1 for b in blocks if band(b["bbox"][0]) == band(b["bbox"][2] - 15)
               or b["bbox"][2] <= bounds[band(b["bbox"][0])] + 15)
    return starts if fits / len(blocks) >= 0.9 else [0.0]


def _page_text_pdf(page) -> str:
    """Texte d'une page PDF dans l'ordre de lecture (colonne par colonne)."""
    blocks = [b for b in page.get_text("dict")["blocks"] if b["type"] == 0]
    starts = _column_starts(blocks)

    height = page.rect.height

    def key(b):
        x0, y0, _, y1 = b["bbox"]
        if y1 < 0.11 * height:      # en-tête de page : avant toutes les colonnes
            return (-1, round(y0))
        if y0 > 0.9 * height:       # pied de page : après toutes les colonnes
            return (len(starts), round(y0))
        col = max((i for i, s0 in enumerate(starts) if x0 + 10 >= s0), default=0)
        return (col, round(y0))

    out = []
    for b in sorted(blocks, key=key):
        for line in b["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in line["spans"])
            if all(s["flags"] & 16 or "Bold" in s["font"] for s in spans):
                text = BOLD + text.strip()
            out.append(text)
        out.append("")
    return "\n".join(out)


def _ocr_page(page, cache_file: Path) -> str:
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    if not shutil.which("tesseract"):
        raise RuntimeError(f"page scannée sans cache OCR ({cache_file.name}) et tesseract absent")
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "p.png"
        page.get_pixmap(dpi=300).save(img)
        text = subprocess.run(["tesseract", str(img), "-", "-l", "fra", "--psm", "3"],
                              capture_output=True, text=True, encoding="utf-8", check=True,
                              env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text, encoding="utf-8")
    return text


def _unreadable(text: str) -> bool:
    """Page sans texte, ou couche texte illisible (polices mal encodées : « 3< 5 /:$"*/3FF+0<5 »)."""
    t = text.replace(BOLD, "")
    chars = [c for c in t if not c.isspace()]
    if len(chars) < 30:
        return True
    return sum(c.isalpha() for c in chars) / len(chars) < 0.6


def extract_pdf(path: Path, page_from=None, page_to=None, ocr=False) -> list[tuple[int, str, str]]:
    """Retourne [(numéro de page PDF, texte, méthode)] ; pages numérotées à partir de 1.

    ocr=True : OCR des pages sans texte ; ocr="force" : OCR de toutes les pages
    (couche texte présente mais inexploitable, ex. accents perdus).
    """
    try:
        import pymupdf
    except ImportError:  # anciennes versions de PyMuPDF
        try:
            import fitz as pymupdf
        except ImportError:
            pymupdf = None

    if pymupdf is None:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [(i + 1, p.extract_text() or "", "pypdf") for i, p in enumerate(reader.pages)]
        return pages[(page_from or 1) - 1:page_to or len(pages)]

    out = []
    with pymupdf.open(path) as doc:
        lo, hi = (page_from or 1), (page_to or doc.page_count)
        for n in range(lo, hi + 1):
            page = doc[n - 1]
            text, method = _page_text_pdf(page), "texte"
            if ocr == "force" or (ocr and _unreadable(text)):
                text = _ocr_page(page, OCR_CACHE / path.stem / f"p{n:03d}.txt")
                method = "ocr"
            out.append((n, text, method))
    return out


def extract_html(path: Path) -> list[tuple[int, str, str]]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    return [(1, main.get_text("\n"), "html")]


def extract(path: Path, fmt: str, page_from=None, page_to=None, ocr=False):
    fmt = fmt.lower()
    if fmt == "pdf":
        return extract_pdf(path, page_from, page_to, ocr)
    if fmt in {"html", "htm"}:
        return extract_html(path)
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    # export texte d'un PDF : une ligne vide sépare deux pages
    return [(i + 1, t, "txt") for i, t in enumerate(text.split("\n\n"))]


# --------------------------------------------------------------------------
# Nettoyage
# --------------------------------------------------------------------------

CHAR_FIXES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
              "’": "'", "‘": "'", " ": " ", " ": " ", " ": " ",
              "–": "-", "—": "-", "­": "", "…": "..."}

PAGE_NUMBER_RE = re.compile(r"^\s*(?:-\s*)?(?:page\s*)?\d{1,4}(?:\s*/\s*\d{1,4})?(?:\s*-)?\s*$", re.I)
ROMAN = r"(?:[IVXLC]+|Il|IIl|Ill)"  # « Il » = « II » mal codé dans certains PDF
ORDINAL = r"(?i:PREMI[EÈ]RE?|DEUXI[EÈ]ME|TROISI[EÈ]ME|QUATRI[EÈ]ME|CINQUI[EÈ]ME|SIXI[EÈ]ME|SEPTI[EÈ]ME|HUITI[EÈ]ME|UNIQUE|PR[EÉ]LIMINAIRE)"
LEVELS = [  # mot-clé en majuscules ou avec capitale initiale (« livre VI » dans une phrase n'est pas un titre)
    ("partie", re.compile(rf"^(?:{ORDINAL}\s+PARTIE\b|PARTIE\s+(?:{ROMAN}|\d+|{ORDINAL})\b|PARTIE\s+(?:L[ÉE]GISLATIVE|R[ÉE]GLEMENTAIRE)\b)")),
    ("livre", re.compile(rf"^(?:(?:LIVRE|Livre)\s+(?:{ROMAN}|\d+|{ORDINAL})\b|DISPOSITIONS FINALES$)")),
    ("titre", re.compile(rf"^(?:TITRE|Titre)\s+(?:{ROMAN}|\d+|{ORDINAL})\b")),
    ("chapitre", re.compile(rf"^(?:CHAPITRE|Chapitre)\s+(?:{ROMAN}|\d+|{ORDINAL})\b")),
    ("section", re.compile(rf"^(?:SECTION|Section)\s+(?:{ROMAN}|\d+|{ORDINAL})\b")),
    ("paragraphe", re.compile(rf"^(?:Sous-section|SOUS-SECTION|Paragraphe|PARAGRAPHE)\s+(?:{ROMAN}|\d+|{ORDINAL})\b")),
]
LEVEL_NAMES = [n for n, _ in LEVELS]
ARTICLE_RE = re.compile(
    # variantes OCR tolérées : « Atticle », « Aïticle », « Articie », « ARTICÉE »
    r"^[«\"‘'.|_*]{0,3}\s*(?:Art\.|A[rRtïí][tTiIïíl1]{1,2}[cC][lLiIíÉE1][eE])\s*"
    r"(?P<num>(?:(?:LO|[LRD])\s?\.?\s?)?(?:(?i:premier|1er|unique)|\d+(?:\s?[-.]\s?\d+(?=\s*(?:\(|$|\.|[A-ZÉ])))*)"
    r"(?:\s?(?:bis|ter|tertio|quater|quinquies|sexies|nouveau))?)\b['’]?\.?"
    r"\s*(?P<rest>.*)$"
)
# note de consolidation (« Article 3 de la loi constitutionnelle n° 2016-10 ... ») : ce n'est pas un article
NOTE_RE = re.compile(r"^[«\"“]?\s*(?:Article|Art\.)\s+\S+(?:\s+(?:bis|ter))?\s+(?:de\s+la\s+loi|du\s+d[ée]cret|de\s+l'ordonnance)\b", re.I)
STRUCT_RE = re.compile(rf"^(?:{BOLD})?[«\"]?\s*(?:ARTICLE|Article|Art\.|LIVRE|TITRE|CHAPITRE|SECTION|Sous-section|Paragraphe)\b", re.I)
LIST_ITEM_RE = re.compile(r"^(?:[-•*]|\d+[°)]|\d+\.\s|[a-z]\)|[IVX]+\.\s)")
TOC_RE = re.compile(r"\.{6,}\s*\d*\s*$")
# en-tête courant du Journal officiel (« 13 janvier 2020 JOURNAL OFFICIEL DE LA REPUBLIQUE DU SENEGAL 31 »)
RUNNING_HEADER_RE = re.compile(r"^[\d\s\w©.]{0,25}JOURNAL\s?OFFICIEL\s+DE\s+LA\s+REPUBLIQUE\s+DU\s+SENEGAL[\s\d\w]{0,25}$", re.I)


def normalize_chars(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for k, v in CHAR_FIXES.items():
        text = text.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def _shape(line: str) -> str:
    line = re.sub(r"[ \t]+", " ", normalize_chars(line.replace(BOLD, ""))).strip()
    return re.sub(r"\d+", "#", line)


def repeated_lines(pages: list[str], min_ratio: float = 0.5) -> set[str]:
    """Lignes présentes sur au moins min_ratio des pages : en-têtes / pieds de page."""
    if len(pages) < 4:
        return set()
    counts: Counter[str] = Counter()
    for p in pages:
        counts.update({_shape(l) for l in p.splitlines() if l.strip()})
    threshold = max(3, int(len(pages) * min_ratio))
    return {l for l, c in counts.items() if c >= threshold and not STRUCT_RE.match(l)}


def _ends_sentence(line: str) -> bool:
    return bool(re.search(r"[.:;!?»]\s*$", line))


def clean_page(text: str, boilerplate: set[str]) -> str:
    """Nettoie une page ; conserve les marqueurs de gras pour la détection de structure."""
    text = normalize_chars(text)
    lines: list[str] = []
    for line in text.splitlines():
        bold = line.startswith(BOLD)
        s = re.sub(r"[ \t]+", " ", line.replace(BOLD, "")).strip()
        if not s:
            lines.append("")
            continue
        if (PAGE_NUMBER_RE.match(s) or _shape(s) in boilerplate or TOC_RE.search(s)
                or RUNNING_HEADER_RE.match(s)):
            continue
        lines.append(BOLD + s if bold else s)

    merged: list[str] = []
    for line in lines:
        prev = merged[-1] if merged else ""
        if not line or not prev:
            merged.append(line)
            continue
        line_bold, prev_bold = line.startswith(BOLD), prev.startswith(BOLD)
        prev_txt, line_txt = prev.replace(BOLD, ""), line.replace(BOLD, "")
        # deux lignes en gras consécutives (intitulé sur deux lignes) : on les recolle
        same_kind = line_bold == prev_bold
        joinable = (same_kind and not STRUCT_RE.match(line) and not STRUCT_RE.match(prev)
                    and not LIST_ITEM_RE.match(line_txt)
                    and (line_bold or not _ends_sentence(prev_txt)))
        if line_bold and prev_bold and (line_txt.isupper() != prev_txt.isupper()):
            joinable = False
        # ligne courte juste sous « Article N » suivie d'une majuscule : intitulé probable, on ne recolle pas
        before = merged[-2].replace(BOLD, "") if len(merged) >= 2 else ""
        if (joinable and ARTICLE_RE.match(before) and len(prev_txt) < 80
                and re.match(r"^[A-ZÀ-Ý]", line_txt)):
            joinable = False
        if joinable:
            if re.search(r"[a-zàâçéèêëîïôûùüÿœ]-$", prev_txt) and re.match(r"[a-zàâçéèêëîïôûùüÿœ]", line_txt):
                merged[-1] = prev[:-1] + line_txt  # césure : « patrony- / mique »
            else:
                merged[-1] = prev + " " + line_txt
        else:
            merged.append(line)
    text = "\n".join(merged)
    low = "a-zàâçéèêëîïôûùüÿœ"
    text = re.sub(rf"([{low}])-\n\n([{low}])", r"\1\2", text)  # césure à un changement de bloc
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def strip_markers(text: str) -> str:
    return text.replace(BOLD, "")


# --------------------------------------------------------------------------
# Structure : Livre / Titre / Chapitre / Section / Paragraphe / Article
# --------------------------------------------------------------------------

ORD_TO_ROMAN = {"PREMIER": "I", "PREMIERE": "I", "PREMIÈRE": "I", "DEUXIEME": "II", "DEUXIÈME": "II",
                "TROISIEME": "III", "TROISIÈME": "III", "QUATRIEME": "IV", "QUATRIÈME": "IV",
                "CINQUIEME": "V", "SIXIEME": "VI", "SEPTIEME": "VII", "HUITIEME": "VIII"}


def strip_quotes(s: str) -> str:
    return re.sub(r"[“”«»\"]", "", s).strip()


def normalize_heading(h: str) -> str:
    """« LIVRE PREMIER - DES PERSONNES » -> « LIVRE I - DES PERSONNES » ; « Il » -> « II »."""
    h = re.sub(r"[“”«»\"]", "", re.sub(r"\s+", " ", h)).strip(" -:")
    h = re.sub(r"\s*[-:]\s*[-:]\s*", " - ", h)  # « Paragraphe I - - Causes »
    h = re.sub(r"^(\S+\s+[^\s.]+)\.\s+(?=\S)", r"\1 - ", h)  # « Titre II. Des libertés »
    words = h.split(" ")
    if len(words) >= 2:
        w = words[1].upper().rstrip(".:")
        if w in ORD_TO_ROMAN:
            words[1] = ORD_TO_ROMAN[w]
        elif re.fullmatch(r"[IVXL]*[Il]+[IVXL]*", words[1]) and "l" in words[1]:
            words[1] = words[1].replace("l", "I")
    h = " ".join(words)
    h = re.sub(r"\s*[-:]\s*", " - ", h, count=1) if re.search(r"[-:]", h) else h
    return re.sub(r"(?:\s-\s*){2,}", " - ", h)  # « Chapitre I. - Littoral » -> « Chapitre I - Littoral »


@dataclass
class Article:
    article: str
    intitule: str
    text: str
    page_start: int
    page_end: int
    modification: str = ""
    hierarchy: dict = field(default_factory=dict)


def split_articles(pages: list[tuple[int, str]], intitules: bool | str = False) -> list[Article]:
    """Découpe en articles.

    intitules=True : l'intitulé est la (les) ligne(s) en gras sous « Article N » ;
    intitules="heuristique" (export texte sans gras) : 1re ligne courte sans ponctuation
    finale, prolongée par les lignes qui commencent par une minuscule.
    """
    hierarchy: dict[str, str] = {}
    articles: list[Article] = []
    current: Article | None = None
    preamble: list[str] = []          # texte avant le premier article (exposé des motifs, préambule)
    preamble_pages: list[int] = []
    in_quote = False                  # entre « et » : nouvelle rédaction citée par une loi modificative
    pending_level: str | None = None   # niveau dont on attend l'intitulé (ligne suivante)
    expecting_title = False             # intitulé attendu après « Article N »
    pending_note: str | None = None     # note de consolidation, rattachée à l'article suivant
    heuristic = intitules == "heuristique"
    quote_note = ""                     # note qui introduit un bloc « ... » de plusieurs articles
    last_level: str | None = None

    def close():
        nonlocal current
        if current:
            articles.append(current)
        current = None

    for page_no, text in pages:
        lines = text.split("\n")
        for li, raw in enumerate(lines):
            bold = raw.startswith(BOLD)
            line = raw.replace(BOLD, "").strip()
            if not line:
                if current and current.text:
                    current.text += "\n"
                continue
            level = next((name for name, rx in LEVELS if rx.match(line)), None)
            if level:
                close()
                hierarchy[level] = normalize_heading(line) + (" -" if re.search(r"[-:]\s*$", line) else "")
                for lower in LEVEL_NAMES[LEVEL_NAMES.index(level) + 1:] + ["rubrique"]:
                    hierarchy.pop(lower, None)
                # l'intitulé peut continuer sur les lignes suivantes (majuscules ou gras)
                pending_level = last_level = level
                expecting_title = False
                continue
            continues = (line.isupper() or bold or hierarchy.get(pending_level, "").endswith("-")
                         or re.match(r"^(?:[a-zàâçéèêëîïôûùüÿœ]|[ldLD]'[a-zé])", line))
            if pending_level and continues and len(line) < 150 and not ARTICLE_RE.match(line):
                sep = " " if " - " in hierarchy[pending_level] else " - "
                hierarchy[pending_level] = normalize_heading(f"{hierarchy[pending_level]}{sep}{line}")
                continue
            pending_level = None
            if NOTE_RE.match(line):
                # juste sous « Article N » (texte vide) : la note concerne cet article ;
                # sinon elle annonce les articles qui suivent (ex. ajout des art. 25-1 à 25-3)
                note_for_current = current is not None and not current.text.strip()
                if not note_for_current:
                    close()
                pending_note = line
                continue
            # la note continue jusqu'à la fin de sa phrase (« ... article remplaçant l'alinéa premier. »)
            if (pending_note is not None and not pending_note.rstrip().endswith(".")
                    and not ARTICLE_RE.match(line) and not line.startswith(("«", "“", '"'))):
                pending_note += " " + line
                # la note finit par « (JORS ...), article ... . » : la suite de la ligne est le texte
                cut = re.match(r"^(.*?\),\s*article\b.*?[^A-Z]\.)\s+([«“]?\s*[A-ZÉÀ«].*)$", pending_note)
                if not cut:
                    continue
                pending_note, line = cut.group(1), cut.group(2)
            # intitulé de titre donné par une note de consolidation : “« DES DROITS ET LIBERTES ... »”
            if (pending_note is not None and current is None and last_level
                    and line.startswith(("«", "“")) and strip_quotes(line).isupper()):
                hierarchy[last_level] = normalize_heading(f"{hierarchy[last_level]} - {strip_quotes(line)}")
                pending_note = None
                continue
            if pending_note is not None and current is not None and not current.text.strip():
                current.modification = re.sub(r"\s+", " ", pending_note)[:400]
                quote_note, pending_note = current.modification, None
            # rubrique en majuscules juste avant un article (« EDUCATION », « TRAVAIL »)
            nxt = next((l.replace(BOLD, "").strip() for l in lines[li + 1:] if l.strip()), "")
            if (line.isupper() and len(line) < 70 and not ARTICLE_RE.match(line)
                    and ARTICLE_RE.match(nxt) and current is not None):
                close()
                hierarchy["rubrique"] = line
                continue
            m = ARTICLE_RE.match(line)
            if m and (not intitules or not m.group("rest") or m.group("rest").startswith("(")
                      or re.match(r"^AU\s?/", m.group("rest"))):
                close()
                num = m.group("num").strip()
                num = re.sub(r"(?i)\b(?:premier|1er)\b", "1", re.sub(r"\s*-\s*", "-", num))
                num = re.sub(r"^(LO|[LRD])\s?\.?\s?(?=\d)", r"\1.", num)  # « L. 22 », « R premier » -> « L.22 », « R.1 »
                rest = m.group("rest").strip().lstrip(".-: ").strip()
                modification = ""
                # article d'un Acte uniforme OHADA reproduit dans un code national (« ARTICLE 69 AU/DCG »)
                au = re.match(r"^(AU\s?/\s?[A-Z]+(?:\s?/\s?[A-Z]+)*)\b\s*(.*)$", rest)
                if au:
                    num = f"{num} {re.sub(r'\s', '', au.group(1))}"
                    rest, modification = au.group(2), f"article de l'Acte uniforme OHADA {au.group(1)} reproduit"
                mod = re.match(r"^\(([^)]*)\)\s*(.*)$", rest)
                if mod:
                    modification, rest = mod.group(1).strip(), mod.group(2)
                if line.startswith("«"):
                    in_quote = True
                if pending_note:
                    modification = quote_note = re.sub(r"\s+", " ", pending_note)[:400]
                    pending_note = None
                elif in_quote and not modification:
                    modification = quote_note or "nouvelle rédaction citée par le texte modificatif"
                title = ""
                if rest.lstrip(": ").isupper() and len(rest) < 150:  # « ARTICLE 14 : TRANSACTIONS PERSONNELLES... »
                    title, rest = rest.lstrip(": ").strip(), ""
                current = Article(num, title, rest, page_no, page_no, modification, dict(hierarchy))
                expecting_title = intitules
                if "»" in rest:
                    in_quote, quote_note = False, ""
                continue
            if current is None:
                if not articles:
                    preamble.append(line)
                    preamble_pages.append(page_no)
                continue
            if current.intitule.isupper() and not current.text and line.isupper() and len(line) < 150:
                current.intitule += " " + line  # intitulé en majuscules sur plusieurs lignes
                continue
            if expecting_title and bold and not heuristic:
                current.intitule = (current.intitule + " " + line).strip()
                continue
            if expecting_title and heuristic and not current.text:
                starts_lower = re.match(r"^[a-zàâçéèêëîïôûùüÿœ]", line)
                if (not current.intitule and len(line) < 80 and not _ends_sentence(line)) or \
                        (current.intitule and starts_lower and not _ends_sentence(current.intitule)):
                    current.intitule = (current.intitule + " " + line).strip()
                    continue
            expecting_title = False
            if line.startswith("«") and current.text == "" :
                in_quote = True
            if "»" in line and line.rfind("»") > line.rfind("«"):
                in_quote, quote_note = False, ""
            sep = "\n" if (not current.text or current.text.endswith("\n")) else " "
            current.text = (current.text + sep + line).lstrip("\n")
            current.page_end = page_no
    close()
    low = "a-zàâçéèêëîïôûùüÿœ"
    for a in articles:
        t = re.sub(rf"([{low}])-\n+([{low}])", r"\1\2", a.text)    # césure à un saut de bloc/colonne
        t = re.sub(rf"([^.:;!?»\n])\n+([{low}])", r"\1 \2", t)     # phrase coupée par un saut de bloc
        a.text = re.sub(r"\n{2,}", "\n", t).strip()
        if a.intitule.startswith("(") and not a.text:  # « (Abrogé par la loi n° 89-01...) »
            a.modification, a.intitule = a.intitule.strip("() "), ""
            a.text = a.modification
    if articles and len(" ".join(preamble)) > 200:
        articles.insert(0, Article("preambule", "Texte précédant le premier article", " ".join(preamble),
                                   preamble_pages[0], preamble_pages[-1]))
    return articles


def article_number(num: str) -> int | None:
    m = re.search(r"\d+", num)
    return int(m.group()) if m else None


def apply_filter(articles: list[Article], filtre: str) -> list[Article]:
    """Garde les articles qui satisfont toutes les conditions « clé=valeur » séparées par « & »."""
    for cond in filter(None, (c.strip() for c in (filtre or "").split("&"))):
        key, _, value = cond.partition("=")
        key, value = key.strip(), value.strip()
        if key == "articles":
            lo, _, hi = value.partition("-")
            lo, hi = int(lo), int(hi or lo)
            articles = [a for a in articles
                        if (n := article_number(a.article)) is not None and lo <= n <= hi]
        else:
            target = normalize_heading(value).upper().rstrip(".")
            articles = [a for a in articles
                        if a.hierarchy.get(key, "").upper().split(" - ")[0].rstrip(".") == target]
    return articles


# --------------------------------------------------------------------------
# Contrôle qualité
# --------------------------------------------------------------------------


def quality(extracted, pages_clean: list[str], articles: list[Article]) -> dict:
    raw = [strip_markers(t) for _, t, _ in extracted]
    methods = Counter(m for _, _, m in extracted)
    empty = sum(1 for t in raw if len(t.strip()) < 30)
    joined = "".join(strip_markers(p) for p in pages_clean)
    letters = sum(ch.isalpha() for ch in joined)
    nonspace = sum(not ch.isspace() for ch in joined)
    weird = sum(1 for ch in joined if ch == "�")
    nums = [a.article for a in articles]
    dupes = [n for n, c in Counter(nums).items() if c > 1]
    ints = [n for n in (article_number(x) for x in nums if "AU" not in x) if n is not None]
    gaps = [f"{a}->{b}" for a, b in zip(ints, ints[1:]) if b - a > 1]
    ratio = letters / max(1, nonspace)
    if not raw or empty / len(raw) > 0.3:
        status = "scan_sans_texte"
    elif methods.get("ocr"):
        status = "ocr_a_verifier"
    elif ratio < 0.75 or weird > 20:
        status = "texte_degrade"
    else:
        status = "ok"
    return {
        "pages": len(raw),
        "pages_ocr": methods.get("ocr", 0),
        "pages_vides": empty,
        "caracteres": len(joined),
        "ratio_lettres": round(ratio, 3),
        "articles_detectes": len(articles),
        "premier_article": nums[0] if nums else "",
        "dernier_article": nums[-1] if nums else "",
        "numeros_dupliques": " ".join(dupes[:20]),
        "sauts_numerotation": " ".join(gaps[:20]),
        "statut": status,
    }


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(path: Path = MANIFEST) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_options(s: str) -> dict:
    opts = {}
    for part in filter(None, (p.strip() for p in (s or "").split(";"))):
        k, _, v = part.partition("=")
        v = v.strip().lower()
        opts[k.strip()] = v if v in {"force", "heuristique"} else v in {"oui", "1", "true", "yes"}
    return opts


def _int(v) -> int | None:
    return int(v) if v and str(v).strip().isdigit() else None


def _pages_label(a, b) -> str:
    return f"p. {a}" if a == b else f"p. {a}-{b}"


_CACHE: dict = {}


def _extract_cached(path: Path, fmt: str, ocr):
    """Plusieurs extraits d'un même fichier : on n'extrait le PDF qu'une fois."""
    key = (path, fmt, ocr)
    if key not in _CACHE:
        _CACHE[key] = extract(path, fmt, None, None, ocr)
    return _CACHE[key]


def process(row: dict) -> tuple[dict, list[dict]]:
    src = RAW / row["fichier_local"]
    if not src.exists():
        raise FileNotFoundError(src)
    opts = parse_options(row.get("options", ""))
    p_from, p_to = _int(row.get("pages_debut")), _int(row.get("pages_fin"))
    # La structure (Livre, Titre...) est lue sur tout le document pour qu'un extrait
    # commençant au milieu d'un livre connaisse son contexte ; on ne garde ensuite
    # que les pages [pages_debut, pages_fin].
    ocr = opts.get("ocr", False)
    if row.get("filtre"):
        full = _extract_cached(src, row["format"], ocr)
    else:
        full = extract(src, row["format"], p_from, p_to, ocr)
    in_range = lambda n: (p_from or 1) <= n <= (p_to or 10**6)
    extracted = [e for e in full if in_range(e[0])]
    boiler = repeated_lines([t for _, t, _ in full])  # en-têtes répétés, estimés sur tout le fichier
    full_clean = [(n, clean_page(t, boiler)) for n, t, _ in full]
    numbered = [(n, t) for n, t in full_clean if in_range(n)]
    pages_clean = [t for _, t in numbered]
    if opts.get("pages"):
        articles = []
    else:
        # les pages précédentes donnent le contexte (Livre, Titre...) ; rien après pages_fin
        context = [x for x in full_clean if x[0] <= (p_to or 10**6)] if row.get("filtre") else numbered
        articles = [a for a in split_articles(context, opts.get("intitules", False)) if in_range(a.page_start)]
        articles = apply_filter(articles, row.get("filtre", ""))

    meta = dict(row)
    meta["sha256_original"] = sha256(src)
    q = quality(extracted, pages_clean, articles)
    if opts.get("ocr_relu") and q["statut"] == "ocr_a_verifier":
        q["statut"] = "ocr_relu_a_la_main"
    short = row.get("titre_court") or row["titre"]

    txt = "\n\n".join(f"[[page {n}]]\n{strip_markers(t)}" for n, t in numbered)
    header = (f"# {row['titre']}\n# Source : {row['organisme']} - {row['url']}\n"
              f"# Version : {row['version_texte']} | Consulté le {row['date_consultation']}\n"
              f"# Pages PDF {row.get('pages_debut') or 1}-{row.get('pages_fin') or len(numbered)}"
              f"{' | filtre ' + row['filtre'] if row.get('filtre') else ''}\n\n")
    (PROCESSED / f"{row['id']}.txt").write_text(header + txt, encoding="utf-8")

    doc = {
        "doc_id": row["id"], "metadata": meta, "quality": q,
        "pages": [{"page": n, "methode": m, "text": strip_markers(t)}
                  for (n, _, m), t in zip(extracted, pages_clean)],
        "articles": [asdict(a) for a in articles],
    }
    (PROCESSED / f"{row['id']}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    common = {"doc_id": row["id"], "titre_document": row["titre"], "type_document": row.get("type_document", ""),
              "source_url": row["url"], "version_texte": row["version_texte"],
              "date_consultation": row["date_consultation"]}
    method = {n: m for n, _, m in extracted}
    ocr_label = "ocr relu à la main" if opts.get("ocr_relu") else "ocr à vérifier"
    def extraction(a, b):  # une unité est « OCR » si une de ses pages l'est
        return ocr_label if any(method.get(n) == "ocr" for n in range(a, b + 1)) else "texte natif"
    units = []
    for idx, a in enumerate(articles):
        h = a.hierarchy
        units.append({
            "unit_id": f"{row['id']}::art-{a.article.replace(' ', '')}" + (f"::{idx}" if a.article in q["numeros_dupliques"].split() else ""),
            **common,
            "article": a.article, "intitule": a.intitule, "modification": a.modification,
            "partie": h.get("partie", ""), "livre": h.get("livre", ""), "titre": h.get("titre", ""), "chapitre": h.get("chapitre", ""),
            "section": h.get("section", ""), "paragraphe": h.get("paragraphe", ""),
            "rubrique": h.get("rubrique", ""),
            "page_start": a.page_start, "page_end": a.page_end,
            "citation": f"{short}, art. {a.article} ({_pages_label(a.page_start, a.page_end)})",
            "text": a.text, "extraction": extraction(a.page_start, a.page_end),
        })
    if not units:  # document sans articles ou option pages=oui (guide explicatif) : une unité par page
        for n, t in numbered:
            t = strip_markers(t).strip()
            if len(t) >= 80:  # ignore les pages quasi vides (couverture, sommaire réduit à rien)
                units.append({"unit_id": f"{row['id']}::p{n}", **common,
                              "article": "", "intitule": "", "modification": "",
                              "partie": "", "livre": "", "titre": "", "chapitre": "", "section": "", "paragraphe": "", "rubrique": "",
                              "page_start": n, "page_end": n, "citation": f"{short}, p. {n}", "text": t,
                              "extraction": extraction(n, n)})
    return {"id": row["id"], "titre": row["titre"], **q}, units


def load_units(path: Path | None = None) -> list[dict]:
    """Charge les unités normalisées (une par article, ou par page pour les guides).

    Point d'entrée pour la personne 2 (chunking / indexation) :
        from ingest import load_units
        units = load_units()   # data/processed/articles.jsonl
    """
    path = path or PROCESSED / "articles.jsonl"
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mark_replaced(units: list[dict], rows: list[dict]) -> None:
    """Signale les articles réécrits par un texte plus récent du corpus.

    Colonne « remplace » du manifeste, sur la ligne du texte modificatif :
    "cp-atteintes-personnes-moeurs:319 bis,320,320 bis,321".
    """
    replaced = {}
    for row in rows:
        target, _, nums = (row.get("remplace") or "").partition(":")
        for n in filter(None, (x.strip() for x in nums.split(","))):
            replaced[(target.strip(), n)] = f"remplacé par {row.get('titre_court') or row['titre']} (doc {row['id']})"
    for u in units:
        u["statut_version"] = replaced.get((u["doc_id"], u["article"]), "texte tel que publié par la source")


# --------------------------------------------------------------------------
# OCR en lot (tesseract, plusieurs pages en parallèle)
# --------------------------------------------------------------------------

def _ocr_batch_page(pdf: str, n: int, dpi: int = 300) -> int:
    import pymupdf

    out = OCR_CACHE / Path(pdf).stem / f"p{n:03d}.txt"
    if out.exists():  # page déjà en cache (éventuellement corrigée à la main) : on n'y touche pas
        return -1
    with pymupdf.open(pdf) as doc, tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "p.png"
        doc[n - 1].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).save(img)
        text = subprocess.run(["tesseract", str(img), "-", "-l", "fra", "--psm", "3"],
                              capture_output=True, text=True, encoding="utf-8", check=True,
                              env={**os.environ, "OMP_THREAD_LIMIT": "1"}).stdout  # 1 thread/page : évite la surcharge CPU
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return len(text)


def ocr_batch(rows: list[dict], workers: int = 4) -> None:
    """OCR de toutes les pages des PDF marqués ocr=oui/force, sauf celles déjà en cache."""
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract introuvable : installez Tesseract OCR (langue fra) et ajoutez-le au PATH")
    import pymupdf

    pdfs = sorted({str(RAW / r["fichier_local"]) for r in rows
                   if r["format"] == "pdf" and parse_options(r.get("options", "")).get("ocr")})
    jobs = []
    for pdf in pdfs:
        with pymupdf.open(pdf) as doc:
            jobs += [(pdf, n) for n in range(1, doc.page_count + 1)
                     if not (OCR_CACHE / Path(pdf).stem / f"p{n:03d}.txt").exists()]
    print(f"OCR : {len(jobs)} page(s) à traiter")
    with ProcessPoolExecutor(workers) as pool:
        futures = [pool.submit(_ocr_batch_page, pdf, n) for pdf, n in jobs]
        for done, f in enumerate(as_completed(futures), 1):
            f.result()
            if done % 20 == 0 or done == len(jobs):
                print(f"  {done}/{len(jobs)} pages", flush=True)


# --------------------------------------------------------------------------
# Contrôle de traçabilité : chaque unité doit se retrouver dans sa page source
# --------------------------------------------------------------------------

def _norm_trace(text: str) -> str:
    """Minuscules, sans accents, ponctuation ni espaces : indépendant de la mise en page."""
    text = unicodedata.normalize("NFKD", normalize_chars(text).replace(BOLD, ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]", "", text)


def _page_reference(row: dict, cache: dict) -> dict[int, str]:
    """Texte brut de chaque page (avant découpage), sans en-têtes répétés ni numéros de page."""
    key = (row["fichier_local"], row.get("options", ""))
    if key not in cache:
        opts = parse_options(row.get("options", ""))
        pages = extract(RAW / row["fichier_local"], row["format"], None, None, opts.get("ocr", False))
        boiler = repeated_lines([t for _, t, _ in pages])
        keep = lambda l: not (_shape(l) in boiler or PAGE_NUMBER_RE.match(l.replace(BOLD, "")))
        cache[key] = {n: _norm_trace("\n".join(l for l in t.splitlines() if keep(l))) for n, t, _ in pages}
    return cache[key]


def _probes(text: str, size: int = 40) -> list[str]:
    """Trois fragments répartis dans le texte (début, milieu, fin)."""
    t = _norm_trace(text)
    if len(t) <= size:
        return [t] if t else []
    return [t[s:s + size] for s in sorted({0, (len(t) - size) // 2, len(t) - size})]


def check_traceability(sample: int = 0) -> int:
    manifest = {r["id"]: r for r in read_manifest()}
    units = load_units()
    cache: dict = {}
    rows, ok = [], 0
    for u in units:
        ref = _page_reference(manifest[u["doc_id"]], cache)
        # la page suivante est incluse : un article peut déborder sur la colonne/page d'après
        span = "".join(ref.get(n, "") for n in range(u["page_start"], u["page_end"] + 2))
        found = [p in span for p in _probes(u["text"])]
        status = "ok" if found and all(found) else ("partiel" if any(found) else "introuvable")
        ok += status == "ok"
        rows.append({"unit_id": u["unit_id"], "citation": u["citation"], "pages": f"{u['page_start']}-{u['page_end']}",
                     "caracteres": len(u["text"]), "fragments_retrouves": f"{sum(found)}/{len(found)}",
                     "statut": status})
    with (PROCESSED / "traceability_report.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"Traçabilité : {ok}/{len(rows)} unités retrouvées intégralement dans leur page source "
          f"({100 * ok / max(1, len(rows)):.1f} %)")
    for r in rows:
        if r["statut"] != "ok":
            print(f"  [{r['statut']}] {r['citation']}")
    if sample:
        random.seed(0)
        for u in random.sample(units, min(sample, len(units))):
            print(f"\n--- {u['citation']} | {u['source_url']}\n{u['text'][:600]}")
    return 0 if all(r["statut"] != "introuvable" for r in rows) else 1


REPORT_FIELDS = ["id", "titre", "pages", "pages_ocr", "pages_vides", "caracteres", "ratio_lettres",
                 "articles_detectes", "premier_article", "dernier_article", "numeros_dupliques",
                 "sauts_numerotation", "statut"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="identifiants du manifeste à traiter")
    ap.add_argument("--ocr", action="store_true", help="OCR en lot des pages scannées absentes du cache avant l'ingestion")
    ap.add_argument("--workers", type=int, default=4, help="processus tesseract en parallèle (avec --ocr)")
    ap.add_argument("--controle", action="store_true", help="contrôle de traçabilité seul, sans réingestion")
    ap.add_argument("--sans-controle", action="store_true", help="ne pas lancer le contrôle de traçabilité après l'ingestion")
    ap.add_argument("--sample", type=int, default=0, help="afficher N passages tirés au hasard après le contrôle")
    args = ap.parse_args(argv)
    if args.controle:
        return check_traceability(args.sample)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_manifest()
            if r.get("ingerer", "oui").strip().lower() != "non" and (not args.only or r["id"] in args.only)]
    if args.ocr:
        ocr_batch(rows, args.workers)
    report, all_units, errors = [], [], 0
    for row in rows:
        try:
            q, units = process(row)
        except Exception as e:  # on continue sur les autres documents
            errors += 1
            print(f"[ERREUR] {row['id']}: {e}", file=sys.stderr)
            report.append({"id": row["id"], "titre": row["titre"], "statut": f"erreur: {e}"})
            continue
        report.append(q)
        all_units.extend(units)
        print(f"[{q['statut']}] {row['id']:<28} pages={q['pages']:<4} articles={q['articles_detectes']:<4}"
              f" {q['premier_article']}..{q['dernier_article']}")

    mark_replaced(all_units, rows)
    if not args.only:  # un traitement partiel ne doit pas écraser les fichiers agrégés
        with (PROCESSED / "articles.jsonl").open("w", encoding="utf-8") as f:
            for u in all_units:
                f.write(json.dumps(u, ensure_ascii=False) + "\n")
        with (PROCESSED / "quality_report.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=REPORT_FIELDS, extrasaction="ignore")
            w.writeheader()
            w.writerows(report)
        print(f"{len(all_units)} unités écrites dans {PROCESSED / 'articles.jsonl'}")
        if not args.sans_controle:
            errors += check_traceability(args.sample)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
