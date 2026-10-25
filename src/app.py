
import re

import streamlit as st

from rag import (
    MESSAGE_REFUS,
    TOP_K,
    generate_answer,
    passages_pertinents,
)
from retrieval import search


# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================

st.set_page_config(
    page_title="Assistant juridique sénégalais",
    page_icon="⚖️",
    layout="centered",
)

st.title("Assistant documentaire juridique sénégalais")

st.caption(
    "Les réponses s'appuient sur les textes retrouvés dans le corpus "
    "documentaire. Elles ne constituent pas un avis juridique."
)


# ============================================================
# FONCTIONS D'AFFICHAGE
# ============================================================

def extraire_numeros_cites(answer: str) -> set[int]:
    """Extrait les numéros d'extraits cités dans la réponse."""
    return {
        int(numero)
        for numero in re.findall(
            r"\[?\s*EXTRAIT\s+(\d+)\s*\]?",
            answer,
            flags=re.IGNORECASE,
        )
    }


def afficher_sources(passages: list[dict], answer: str) -> None:
    """
    Affiche uniquement les sources correspondant aux extraits cités.

    Les numéros correspondent à l'ordre des passages transmis au modèle.
    """
    numeros_cites = extraire_numeros_cites(answer)

    if not numeros_cites:
        st.caption(
            "Aucune citation d'extrait détectée dans la réponse. "
            "Les sources ne peuvent pas être associées automatiquement."
        )
        return

    # L'ordre doit être identique à celui utilisé par build_context().
    sources_citees = [
        (numero, passage)
        for numero, passage in enumerate(passages, start=1)
        if numero in numeros_cites
    ]

    if not sources_citees:
        st.warning(
            "La réponse contient des références à des extraits "
            "qui ne correspondent pas aux passages transmis."
        )
        return

    st.markdown("### Sources citées")

    for numero, passage in sources_citees:
        citation = (
            passage.get("citation")
            or "Référence non renseignée"
        )

        distance = passage.get("distance")
        titre = f"[EXTRAIT {numero}] — {citation}"

        if distance is not None:
            try:
                titre += f" (distance : {float(distance):.3f})"
            except (TypeError, ValueError):
                pass

        with st.expander(titre):
            document = passage.get("titre_document")
            if document:
                st.write(f"**Document :** {document}")

            source_url = passage.get("source_url")
            if source_url:
                st.markdown(f"[Consulter le document source]({source_url})")

            contenu = passage.get("text") or ""
            if contenu:
                st.write(contenu)

            metadata = passage.get("metadata") or {}
            page = metadata.get("page")
            if page is not None:
                st.caption(f"Page : {page}")


# ============================================================
# FORMULAIRE DE QUESTION
# ============================================================

with st.form("question_form"):
    question = st.text_input(
        "Pose ta question juridique",
        placeholder=(
            "Ex. À quel moment commence la personnalité juridique ?"
        ),
    )

    submitted = st.form_submit_button(
        "Rechercher",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# TRAITEMENT DE LA QUESTION
# ============================================================

if submitted:
    question = question.strip()

    if not question:
        st.warning("Saisis une question avant de rechercher.")
        st.stop()

    # --------------------------------------------------------
    # 1. Recherche documentaire
    # --------------------------------------------------------

    try:
        with st.spinner("Recherche des passages pertinents..."):
            passages_bruts = search(question, top_k=TOP_K)

    except Exception as error:
        st.error(
            "Une erreur est survenue pendant la recherche documentaire."
        )
        with st.expander("Détails techniques"):
            st.code(str(error))
        st.stop()

    if not passages_bruts:
        st.info(MESSAGE_REFUS)
        st.stop()

    # --------------------------------------------------------
    # 2. Filtrage unique des passages
    # --------------------------------------------------------

    passages = passages_pertinents(passages_bruts)

    if not passages:
        st.info(MESSAGE_REFUS)

        with st.expander("Diagnostic de la recherche"):
            st.write(
                "Des passages ont été retrouvés, mais aucun n'a atteint "
                "le seuil de pertinence configuré."
            )

            for index, passage in enumerate(passages_bruts, start=1):
                st.markdown(f"**Passage {index}**")
                st.write(
                    passage.get("citation")
                    or "Référence non renseignée"
                )
                st.write(
                    "Score de pertinence :",
                    passage.get("relevance_score"),
                )
                st.write((passage.get("text") or "")[:500])

        st.stop()

    # --------------------------------------------------------
    # 3. Génération à partir de la même liste filtrée
    # --------------------------------------------------------

    with st.spinner("Génération de la réponse..."):
        answer = generate_answer(question, passages)

    st.markdown("### Réponse")

    if answer == MESSAGE_REFUS:
        st.info(answer)
        st.stop()

    # Ne pas traiter les messages d'erreur comme des réponses juridiques.
    erreurs_techniques = (
        "Impossible de joindre Ollama.",
        "La génération a dépassé le délai autorisé.",
        "Ollama a renvoyé une erreur HTTP",
        "Ollama a renvoyé une réponse JSON invalide.",
        "Le modèle n'a pas généré de réponse exploitable.",
        "Erreur lors de la requête vers Ollama",
    )

    if answer.startswith(erreurs_techniques):
        st.error(answer)
        st.stop()

    st.markdown(answer)

    # --------------------------------------------------------
    # 4. Sources citées
    # --------------------------------------------------------

    afficher_sources(passages, answer)

    # --------------------------------------------------------
    # 5. Avertissement documentaire
    # --------------------------------------------------------

    st.divider()

    st.caption(
        "Vérifie les références dans le texte juridique original. "
        "La présence d'un extrait dans le corpus ne garantit ni son "
        "actualité ni l'exhaustivité de la réponse."
    )
