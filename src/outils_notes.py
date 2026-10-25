"""Deux outils pour l'évaluation.
  python src\\outils_notes.py verifier
      -> contrôle, dans data/processed/articles.jsonl, le numéro d'article attendu de chaque question
  python src\\outils_notes.py corriger ID exactitude fidelite completude citations refus inventee "note"
      -> corrige les notes d'UNE question déjà notée (refus : a/i/n ; inventee : o/n)
      exemple : python src\\outils_notes.py corriger F03 2 2 2 2 n n "Reponse juste, art. 152 cite"
"""
import csv, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "evaluation" / "questions.json"
RESULTS = ROOT / "reports" / "results_run1.csv"
CANDIDATES = [ROOT / "data" / "processed" / "articles.jsonl", ROOT / "data" / "processed" / "chunks.jsonl"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower().replace("\u2019", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def article_of(rec):
    for src in (rec, rec.get("metadata") or {}):
        a = src.get("article") if isinstance(src, dict) else None
        if a:
            return str(a)
    for s in strings(rec):
        m = re.search(r"art-(\d+\w*)", s)
        if m:
            return m.group(1)
    return "?"


def verifier():
    path = next((p for p in CANDIDATES if p.exists()), None)
    if not path:
        sys.exit("Fichier articles.jsonl introuvable dans data/processed/")
    recs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            txt = norm(" ".join(strings(r)))
            if "code de la famille" in txt or "cf-" in txt:
                recs.append((article_of(r), txt))
    print(f"{len(recs)} unités lues dans {path.name}\n")
    bad = 0
    for q in json.loads(QUESTIONS.read_text(encoding="utf-8")):
        if not q["answerable"]:
            continue
        for g in q["expected_evidence"]:
            exp = [re.sub(r"\D", "", a) for a in g if re.match(r"^Article \d+$", a)]
            phrases = [norm(a) for a in g if not re.match(r"^Article \d+$", a)]
            found = sorted({a for a, t in recs for p in phrases if p in t}, key=lambda x: (len(x), x))
            ok = bool(set(exp) & set(found))
            bad += (not ok)
            print(f"{q['id']:<4} attendu art. {','.join(exp):<4} | trouvé dans art. {','.join(found[:6]) or 'AUCUN':<14} -> {'OK' if ok else '*** A CORRIGER ***'}")
    print(f"\n{bad} référence(s) à corriger.")


def corriger(a):
    if len(a) < 7:
        sys.exit(__doc__)
    qid, ex, fi, co, ci, refus, inv = a[:7]
    note = a[7] if len(a) > 7 else ""
    for v in (ex, fi, co, ci):
        if v not in ("0", "1", "2"):
            sys.exit("Les 4 notes doivent valoir 0, 1 ou 2.")
    if refus not in ("a", "i", "n") or inv not in ("o", "n"):
        sys.exit("refus = a/i/n et inventee = o/n")
    rows = list(csv.DictReader(open(RESULTS, encoding="utf-8-sig", newline="")))
    fields = list(rows[0].keys())
    hit = [r for r in rows if r["id"].upper() == qid.upper()]
    if not hit:
        sys.exit(f"Question {qid} introuvable.")
    hit[0].update(exactitude=ex, fidelite=fi, completude=co, citations=ci,
                  abstention={"a": "appropriee", "i": "inutile", "n": "non"}[refus],
                  inventee="oui" if inv == "o" else "non", notes=note)
    with open(RESULTS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{qid.upper()} corrigée : {ex}/{fi}/{co}/{ci}, refus={refus}, inventé={inv}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("verifier", "corriger"):
        sys.exit(__doc__)
    verifier() if sys.argv[1] == "verifier" else corriger(sys.argv[2:])
