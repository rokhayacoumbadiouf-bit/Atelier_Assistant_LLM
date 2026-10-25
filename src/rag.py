import re

import requests

from retrieval import search


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"

TOP_K = 5
MAX_CONTEXT_CHARS = 9000
REQUEST_TIMEOUT = 300

# Score combiné minimal pour qu'un passage soit envoyé au modèle.
# Point de départ : à calibrer avec le diagnostic affiché à l'écran.
MIN_RELEVANCE_SCORE = 0.45
# Mettre à True pour afficher le diagnostic de recherche.
DEBUG = False

MESSAGE_REFUS = (
    "Je n'ai pas trouvé de passage suffisamment pertinent "
    "dans le corpus juridique disponible pour répondre "
    "à cette question."
)


# ============================================================
# FILTRAGE ET CONTEXTE
# ============================================================

def passages_pertinents(passages: list[dict]) -> list[dict]:
    """Garde seulement les passages dont le score combiné atteint le seuil."""
    return [
        passage
        for passage in passages
        if float(passage.get("relevance_score") or 0.0) >= MIN_RELEVANCE_SCORE
    ]


def build_context(passages: list[dict]) -> str:
    """Construit un contexte avec des numéros d'extraits continus."""
    if not passages:
        return ""

    context_parts = []
    total_chars = 0
    numero = 0

    for passage in passages:
        text = str(passage.get("text") or "").strip()
        citation = str(
            passage.get("citation") or "Référence non renseignée"
        ).strip()
        title = str(
            passage.get("titre_document") or "Document juridique"
        ).strip()

        if not text:
            continue

        numero += 1
        excerpt = (
            f"[EXTRAIT {numero}]\n"
            f"Document : {title}\n"
            f"Référence : {citation}\n"
            f"Contenu :\n{text}\n"
        )

        if total_chars + len(excerpt) > MAX_CONTEXT_CHARS:
            remaining = MAX_CONTEXT_CHARS - total_chars
            if remaining > 250:
                context_parts.append(excerpt[:remaining])
            break

        context_parts.append(excerpt)
        total_chars += len(excerpt)

    return "\n\n".join(context_parts)


# ============================================================
# VÉRIFICATION DES CITATIONS
# ============================================================

def verifier_citations(answer: str, nb_extraits: int) -> str:
    """Signale les citations qui renvoient vers un extrait inexistant."""
    cites = {int(n) for n in re.findall(r"EXTRAIT\s+(\d+)", answer)}
    invalides = sorted(n for n in cites if n < 1 or n > nb_extraits)

    if invalides:
        return (
            answer
            + f"\n\n[Avertissement : citations inexistantes : {invalides}]"
        )
    return answer


# ============================================================
# GÉNÉRATION DE LA RÉPONSE
# ============================================================

SYSTEM_PROMPT = """
Tu es un assistant documentaire spécialisé dans les textes
juridiques du Sénégal.

RÈGLES OBLIGATOIRES :

1. Réponds en français, de façon claire et concise.
2. Utilise uniquement les informations présentes dans les extraits.
3. N'ajoute aucune règle de droit issue de tes connaissances générales.
4. N'invente jamais d'article, de référence, de page ou de citation.
5. Chaque affirmation juridique doit être appuyée par un extrait
   pertinent, cité sous la forme [EXTRAIT 1], [EXTRAIT 2], etc.
6. Ne cite que les extraits qui soutiennent réellement l'affirmation.
7. N'intègre pas un extrait simplement parce qu'il parle de personnes,
   de commerce ou d'un autre thème voisin.
8. Si les extraits sont insuffisants, contradictoires ou hors sujet,
   indique clairement que le corpus ne permet pas de répondre.
9. Ne prétends pas qu'un texte est actuellement en vigueur si les
   extraits ne permettent pas de vérifier son actualité.
10. Ne donne pas de conseil personnalisé présenté comme une décision
    juridique définitive.

FORMAT DE RÉPONSE :

Réponse :
[Réponse fondée sur les extraits pertinents.]

Références :
- [EXTRAIT n] — référence fournie dans le contexte.

Si les extraits ne permettent pas de répondre, explique-le
au lieu de fabriquer une réponse.
""".strip()


def generate_answer(question: str, passages: list[dict]) -> str:
    """Génère une réponse à partir des seuls passages pertinents."""

    # Le filtre est appliqué AVANT l'appel au modèle.
    pertinents = passages_pertinents(passages)
    context = build_context(pertinents)

    if not context.strip():
        return MESSAGE_REFUS

    nb_extraits = len(re.findall(r"\[EXTRAIT \d+\]", context))

    user_prompt = f"""
QUESTION :
{question}

EXTRAITS DOCUMENTAIRES DISPONIBLES :
{context}

Réponds uniquement à la question posée.
N'utilise aucun fait juridique qui n'est pas étayé par les extraits.
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 350,
            "num_ctx": 8192,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        return (
            "Impossible de joindre Ollama. Vérifie qu'Ollama est "
            "démarré et que le modèle est disponible."
        )

    except requests.exceptions.Timeout:
        return (
            "La génération a dépassé le délai autorisé. "
            "Réessaie ou vérifie les ressources disponibles."
        )

    except requests.exceptions.HTTPError as error:
        return (
            "Ollama a renvoyé une erreur HTTP : "
            f"{error.response.status_code}."
        )

    except requests.exceptions.RequestException as error:
        return f"Erreur lors de la requête vers Ollama : {error}"

    try:
        data = response.json()
    except ValueError:
        return "Ollama a renvoyé une réponse JSON invalide."

    message = data.get("message") or {}
    answer = str(message.get("content") or "").strip()

    if not answer:
        return (
            "Le modèle n'a pas généré de réponse exploitable. "
            "Réessaie avec une question plus précise."
        )

    return verifier_citations(answer, nb_extraits)


# ============================================================
# AFFICHAGE DES SOURCES
# ============================================================

def display_sources(passages: list[dict]) -> None:
    """Affiche les sources utilisées, de façon compacte."""
    if not passages:
        return

    print("\nSources :")
    for index, passage in enumerate(passages, start=1):
        citation = passage.get("citation") or "Référence non renseignée"
        distance = passage.get("distance")

        ligne = f"  [{index}] {citation}"
        if distance is not None:
            ligne += f"  (distance {float(distance):.3f})"
        print(ligne)

        source_url = passage.get("source_url")
        if source_url:
            print(f"      {source_url}")


def display_diagnostic(passages: list[dict]) -> None:
    """Affiche le détail de la recherche. Utile uniquement en développement."""
    print("\n--- DIAGNOSTIC DE LA RECHERCHE ---")

    for index, passage in enumerate(passages, start=1):
        distance = passage.get("distance")
        distance_txt = "non calculée" if distance is None else f"{float(distance):.4f}"

        print(f"\nPassage {index}")
        print("  Référence      :", passage.get("citation"))
        print("  Distance       :", distance_txt)
        print("  Score lexical  :", round(float(passage.get("lexical_score") or 0.0), 4))
        print("  Score combiné  :", round(float(passage.get("relevance_score") or 0.0), 4))
        print("  Texte          :", (passage.get("text") or "")[:300].replace("\n", " "), "...")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main() -> None:
    print("=" * 60)
    print("ASSISTANT DOCUMENTAIRE JURIDIQUE SÉNÉGALAIS")
    print("=" * 60)

    while True:
        try:
            question = input("\nQuestion (ou 'quitter') : ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nFin du programme.")
            break

        if question.lower() in {"quitter", "quit", "exit"}:
            print("Au revoir.")
            break

        if not question:
            continue

        print("\nRecherche en cours...")

        try:
            passages = search(question, top_k=TOP_K)
        except Exception as error:
            print(f"\nErreur pendant la recherche : {error}")
            continue

        if DEBUG:
            display_diagnostic(passages)

        pertinents = passages_pertinents(passages)

        answer = generate_answer(question, passages)

        print("\n" + "-" * 60)
        print(answer)
        print("-" * 60)

        # N'afficher que les sources effectivement citées dans la réponse.
        pertinents = passages_pertinents(passages)
        cites = {int(n) for n in re.findall(r"EXTRAIT\s+(\d+)", answer)}
        cited = [p for i, p in enumerate(pertinents, start=1) if i in cites]

        display_sources(cited)


if __name__ == "__main__":
    main()