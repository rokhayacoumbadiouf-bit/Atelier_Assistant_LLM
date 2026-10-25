"""Évaluation du RAG juridique.

  python -m src.evaluate run       [--top-k 5] [--questions ...] [--out reports/results.csv]
  python -m src.evaluate noter     [--results reports/results.csv]   (mode guidé : notes 0-2)
  python -m src.evaluate summarize [--results reports/results.csv]

Étape 1 (run)       : pose les questions au système, calcule Recall@5 et détecte les abstentions
                      automatiquement, laisse les colonnes de notation manuelle vides.
Étape 2 (à la main) : ouvrir results.csv, remplir exactitude / fidelite / completude / citations (0-2),
                      abstention (appropriee/inutile/non), inventee (oui/non), notes.
Étape 3 (summarize) : moyennes, taux, tableau par type -> reports/summary.md
"""
import argparse, csv, json, os, re, statistics, time, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "data" / "evaluation" / "questions.json"
RESULTS = ROOT / "reports" / "results.csv"
SUMMARY = ROOT / "reports" / "summary.md"

CURRENT_MODEL = ""
MANUAL_COLS = ["exactitude", "fidelite", "completude", "citations", "abstention", "inventee", "notes"]
ABSTAIN_MARKERS = ["pas disponible", "ne trouve pas", "aucune information", "pas d'information",
                   "n'est pas mentionne", "ne figure pas", "ne contiennent pas", "pas dans les documents",
                   "ne peux pas repondre", "information absente", "pas precise",
                   "n'ai pas trouve", "pas suffisamment pertinent", "corpus ne permet pas", "ne permet pas de repondre"]


# --------------------------------------------------------------------------- ADAPTATEUR
def run_system(question, top_k=5):
    """ADAPTATEUR vers le code du groupe (src/retrieval.py et src/rag.py).
    retrieval.search(question, top_k) -> liste de passages (dict)
    rag.generate_answer(question, passages) -> texte de la réponse
    Si leurs noms changent, c'est le SEUL endroit à modifier."""
    import sys
    for d in (str(ROOT), str(ROOT / "src")):  # supporte 'from retrieval import' ET 'from src.retrieval import'
        if d not in sys.path:
            sys.path.insert(0, d)
    try:
        import retrieval, rag
    except ImportError:
        from src import retrieval, rag
    # Modèle Ollama : par défaut qwen2.5:3b (PC 8 Go) ; modifiable via la variable OLLAMA_MODEL.
    # On remplace la constante de rag.py EN MÉMOIRE, sans modifier leur fichier.
    global CURRENT_MODEL
    CURRENT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    rag.OLLAMA_MODEL = CURRENT_MODEL
    passages = retrieval.search(question, top_k=top_k)
    answer = rag.generate_answer(question, passages)
    return answer or "", passages or []


# --------------------------------------------------------------------------- OUTILS
def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower().replace("’", "'"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


ARTICLE_ONLY = re.compile(r"^(?:art(?:icle|\.)?\s*)?(\d+)(?:\s*(bis|ter))?$")


def evidence_found(evidence, haystack):
    """haystack déjà normalisé. Un numéro d'article ('111', 'Art. 111 bis') est cherché comme
    'article 111' / 'art. 111' avec limite de mot ; sinon recherche de la phrase telle quelle."""
    e = norm(evidence).strip()
    m = ARTICLE_ONLY.match(e)
    if m:
        num, suffix = m.group(1), m.group(2)
        pat = rf"\bart(?:icle|\.)?\s*{num}\b" + (rf"\s*{suffix}\b" if suffix else "")
        return re.search(pat, haystack) is not None
    return e in haystack


def _all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _all_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _all_strings(v)


def passages_text(passages):
    """Concatène TOUS les textes de chaque passage (contenu + métadonnées : référence, titre...),
    car les noms de champs varient selon le code du groupe."""
    return norm(" ".join(t for p in passages for t in _all_strings(p)))


def passage_label(p):
    for k in ("citation", "reference", "ref", "article", "titre", "title", "source", "document"):
        v = p.get(k) if isinstance(p, dict) else None
        if isinstance(v, str) and v:
            return v[:40]
    return "?"


def abstained(answer):
    a = norm(answer)
    return any(m in a for m in ABSTAIN_MARKERS)


# --------------------------------------------------------------------------- RUN
def cmd_run(args):
    data = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    todo = [q for q in data if q.get("status") == "a_remplir"]
    if todo:
        print(f"ATTENTION : {len(todo)} question(s) encore à remplir, ignorées : {[q['id'] for q in todo]}")
    qs = [q for q in data if q.get("status") != "a_remplir"]
    if args.only:
        wanted = {x.strip().upper() for x in args.only.split(",")}
        qs = [q for q in qs if q["id"].upper() in wanted]
        print(f"Mode test : seulement {[q['id'] for q in qs]}")
    rows = []
    for q in qs:
        row = {"id": q["id"], "type": q["type"], "question": q["question"], "answerable": q["answerable"],
               "reference_answer": q["reference_answer"], "expected_evidence": " ; ".join(" | ".join(g) if isinstance(g, list) else g for g in q["expected_evidence"])}
        t0 = time.time()
        try:
            answer, passages = run_system(q["question"], args.top_k)
            error = ""
        except Exception as e:
            answer, passages, error = "", [], f"{type(e).__name__}: {e}"
        row["latency_s"] = round(time.time() - t0, 2)
        row["modele"] = CURRENT_MODEL
        top = passages[:args.top_k]
        hay = passages_text(top)
        if q["answerable"] and q["expected_evidence"]:
            # expected_evidence = liste de GROUPES ; un groupe = un passage nécessaire,
            # ses éléments sont des alternatives (numéro d'article OU phrase caractéristique).
            groups = [[g] if isinstance(g, str) else g for g in q["expected_evidence"]]
            found = [any(evidence_found(a, hay) for a in g) for g in groups]
            row["recall_at_5"] = int(any(found))          # au moins un passage utile récupéré
            row["recall_all"] = int(all(found))           # tous les passages nécessaires récupérés
            row["evidence_coverage"] = round(sum(found) / len(found), 2)
        else:
            row["recall_at_5"], row["recall_all"], row["evidence_coverage"] = "", "", ""
        row["answer"] = answer
        row["abstained_auto"] = int(abstained(answer))
        row["retrieved"] = " | ".join(passage_label(p) for p in top)
        row["error"] = error
        row.update({c: "" for c in MANUAL_COLS})
        rows.append(row)
        print(f'{q["id"]:<4} {q["type"]:<15} recall@{args.top_k}={row["recall_at_5"]!s:<2} abst={row["abstained_auto"]} {row["latency_s"]}s {error}')
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} questions évaluées -> {args.out}\nProchaine étape : remplir à la main les colonnes {MANUAL_COLS}, puis `summarize`.")



# --------------------------------------------------------------------------- NOTER (mode guidé)
GUIDE = """
=== COMMENT NOTER (0, 1 ou 2) ===
 exactitude  : 2 = la réponse dit la même chose que la référence ; 1 = en partie juste ; 0 = fausse
 fidélité    : 2 = tout ce qui est dit figure dans les passages retrouvés ; 1 = un détail ajouté ; 0 = invention
 complétude  : 2 = rien d'important ne manque ; 1 = il manque une partie ; 0 = presque tout manque
 citations   : 2 = les articles cités sont les bons ; 1 = en partie ; 0 = faux ou absents
 Question HORS CORPUS : exactitude 2 si le système refuse proprement, 0 s'il invente une réponse.
 Commandes : 's' = passer cette question, 'q' = sauvegarder et quitter (vous reprendrez plus tard)
"""


def _ask(label, choices):
    while True:
        v = input(f"  {label} {choices} > ").strip().lower()
        if v in ("q", "s"):
            return v
        if v in choices.strip("[]").split("/"):
            return v
        print("    -> réponse non valide, réessayez.")


def cmd_noter(args):
    with open(args.results, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    def save():
        with open(args.results, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    print(GUIDE)
    todo = [r for r in rows if not r["exactitude"].strip()]
    print(f"{len(todo)} question(s) à noter sur {len(rows)}.\n")
    for r in todo:
        print("=" * 78)
        print(f"{r['id']}  ({r['type']})  - question {'AVEC' if r['answerable'] == 'True' else 'SANS'} réponse dans le corpus")
        print(f"\nQUESTION : {r['question']}")
        print(f"\nRÉFÉRENCE (la bonne réponse) :\n{r['reference_answer']}")
        print(f"\nRÉPONSE DU SYSTÈME :\n{r['answer']}")
        print(f"\nPASSAGES RETROUVÉS : {r['retrieved']}")
        print(f"Preuve attendue : {r['expected_evidence'] or '(aucune)'}   -> recall@5 = {r['recall_at_5'] or 'n/a'}\n")
        vals, quit_now, skip = {}, False, False
        for col in ("exactitude", "fidelite", "completude", "citations"):
            v = _ask(col, "[0/1/2]")
            if v == "q": quit_now = True; break
            if v == "s": skip = True; break
            vals[col] = v
        if quit_now:
            break
        if skip:
            continue
        a = _ask("le système a-t-il refusé de répondre ? a=refus approprié, i=refus inutile, n=pas de refus", "[a/i/n]")
        if a == "q": break
        if a == "s": continue
        inv = _ask("le système a-t-il inventé quelque chose ?", "[o/n]")
        if inv == "q": break
        if inv == "s": continue
        vals["abstention"] = {"a": "appropriee", "i": "inutile", "n": "non"}[a]
        vals["inventee"] = "oui" if inv == "o" else "non"
        vals["notes"] = input("  note libre (Entrée pour passer) > ").strip()
        r.update(vals)
        save()
        print("  -> enregistré.\n")
    save()
    done = sum(1 for r in rows if r["exactitude"].strip())
    print(f"\nSauvegardé dans {args.results}. {done}/{len(rows)} questions notées.")
    if done == len(rows):
        print("Tout est noté : lancez `python -m src.evaluate summarize --results " + args.results + "`")

# --------------------------------------------------------------------------- SUMMARIZE
def _nums(rows, col):
    out = []
    for r in rows:
        v = str(r.get(col, "")).strip()
        if v in {"0", "1", "2", "0.0", "1.0", "2.0"}:
            out.append(float(v))
    return out


def _mean(v):
    return f"{statistics.mean(v):.2f} (n={len(v)})" if v else "non rempli"


def cmd_summarize(args):
    with open(args.results, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["abstained_auto"] = str(int(abstained(r["answer"])))
    ans = [r for r in rows if r["answerable"] == "True"]
    una = [r for r in rows if r["answerable"] != "True"]
    rec = [int(r["recall_at_5"]) for r in ans if r["recall_at_5"] != ""]
    cov = [float(r["evidence_coverage"]) for r in ans if r["evidence_coverage"] != ""]
    lat = [float(r["latency_s"]) for r in rows if r["latency_s"]]
    L = ["# Résumé de l'évaluation", "",
         f"- Questions évaluées : {len(rows)} ({len(ans)} avec réponse dans le corpus, {len(una)} sans)",
         f"- **Recall@5** (au moins une preuve attendue dans le top-5) : {_mean(rec)}",
         f"- Recall@5 strict (TOUS les passages nécessaires récupérés) : {_mean([int(r['recall_all']) for r in ans if r['recall_all'] != ''])}",
         f"- Couverture moyenne des preuves attendues : {_mean(cov)}",
         f"- Latence moyenne : {statistics.mean(lat):.2f} s" if lat else "- Latence : n/a",
         f"- Erreurs d'exécution : {sum(1 for r in rows if r['error'])}", "",
         "## Abstentions (détection automatique, à confirmer à la main)",
         f"- Questions SANS réponse où le système s'abstient (souhaité) : "
         f"{sum(int(r['abstained_auto']) for r in una)}/{len(una)}",
         f"- Questions AVEC réponse où le système s'abstient (abstention inutile) : "
         f"{sum(int(r['abstained_auto']) for r in ans)}/{len(ans)}", "",
         "## Notation manuelle (0 à 2)"]
    for c in ["exactitude", "fidelite", "completude", "citations"]:
        L.append(f"- {c} : {_mean(_nums(rows, c))}")
    for v, lab in (("appropriee", "refus appropriés"), ("inutile", "refus inutiles"), ("non", "pas de refus")):
        L.append(f"- Notation manuelle : {lab} = {sum(1 for r in rows if r['abstention'].strip().lower() == v)}")
    L.append(f"- Réponses inventées (marquées 'oui') : {sum(1 for r in rows if r['inventee'].strip().lower() == 'oui')}")
    L += ["", "## Par type de question", "", "| Type | n | Recall@5 | Exactitude moy. |", "|---|---|---|---|"]
    for t in dict.fromkeys(r["type"] for r in rows):
        sub = [r for r in rows if r["type"] == t]
        rr = [int(r["recall_at_5"]) for r in sub if r["recall_at_5"] != ""]
        ex = _nums(sub, "exactitude")
        L.append(f"| {t} | {len(sub)} | {(f'{statistics.mean(rr):.2f}' if rr else '—')} | {(f'{statistics.mean(ex):.2f}' if ex else '—')} |")
    L += ["", "## Échecs de récupération (recall@5 = 0)"]
    L += [f"- {r['id']} : {r['question']}" for r in ans if r["recall_at_5"] == "0"] or ["- aucun"]
    text = "\n".join(L)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(text, encoding="utf-8")
    print(text + f"\n\n-> {SUMMARY}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--top-k", type=int, default=5)
    r.add_argument("--only", default="", help="ex: F01,F04 pour tester sur quelques questions")
    r.add_argument("--questions", default=str(QUESTIONS))
    r.add_argument("--out", default=str(RESULTS))
    r.set_defaults(fn=cmd_run)
    n = sub.add_parser("noter")
    n.add_argument("--results", default=str(RESULTS))
    n.set_defaults(fn=cmd_noter)
    s = sub.add_parser("summarize")
    s.add_argument("--results", default=str(RESULTS))
    s.set_defaults(fn=cmd_summarize)
    a = ap.parse_args()
    a.fn(a)
