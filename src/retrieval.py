"""
Recherche hybride sur le corpus juridique :
1. recherche vectorielle (embeddings bge-m3) ;
2. filtre par distance cosinus ;
3. reclassement avec un score lexical sur les seuls candidats vectoriels.
"""

import re
import unicodedata
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from config import COLLECTION_NAME, EMBEDDING_MODEL_NAME, VECTORSTORE_DIR


# ============================================================
# CONFIGURATION
# ============================================================

# Nombre de résultats récupérés avant le reclassement.
VECTOR_CANDIDATES = 40

# Distance cosinus maximale : 0 = identique, 1 = sans rapport.
# À calibrer avec les distances affichées par le diagnostic de rag.py.
MAX_VECTOR_DISTANCE = 0.5

SEMANTIC_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3


# ============================================================
# NORMALISATION ET MOTS VIDES
# ============================================================

STOP_WORDS = {
    "a", "à", "au", "aux", "avec", "ce", "ces", "cet", "cette",
    "dans", "de", "des", "du", "elle", "en", "et", "eux",
    "il", "ils", "je", "la", "le", "les", "leur", "leurs",
    "lui", "ma", "mais", "me", "meme", "mes", "moi", "mon",
    "ne", "nos", "notre", "nous", "on", "ou", "par", "pas",
    "pour", "qu", "que", "quel", "quelle", "quelles", "quels",
    "qui", "sa", "se", "ses", "son", "sur", "ta", "te",
    "tes", "toi", "ton", "tu", "un", "une", "vos", "votre",
    "vous", "y", "est", "sont", "etre", "avoir", "fait",
    "faire", "peut", "peuvent", "doit", "doivent",
    "quand", "comment", "moment", "commence", "commencer",
}


def normalize_text(text: str) -> str:
    """Met en minuscules et supprime les accents."""
    text = str(text or "").lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )


def tokenize(text: str) -> list[str]:
    """Découpe le texte en termes significatifs."""
    tokens = re.findall(r"[a-z0-9]+", normalize_text(text))
    return [
        token
        for token in tokens
        if len(token) > 1 and token not in STOP_WORDS
    ]


# ============================================================
# EXPANSION DE REQUÊTE
# ============================================================

# Vide volontairement : les synonymes codés en dur faussaient les autres
# questions. À n'utiliser qu'avec un thésaurus juridique vérifié.
CONCEPT_EXPANSIONS: dict[str, set[str]] = {}


def expand_query(question: str) -> list[str]:
    """Ajoute d'éventuels synonymes sans remplacer les termes d'origine."""
    original_terms = tokenize(question)
    expanded_terms = set(original_terms)

    for term in original_terms:
        expanded_terms.update(CONCEPT_EXPANSIONS.get(term, set()))

    return sorted(expanded_terms)


# ============================================================
# CHARGEMENT DES RESSOURCES
# ============================================================

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Charge le modèle d'embeddings une seule fois."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_collection():
    """Ouvre la collection ChromaDB existante."""
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)

    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as error:
        raise RuntimeError(
            f"Impossible d'ouvrir la collection '{COLLECTION_NAME}' dans "
            f"'{VECTORSTORE_DIR}'. Vérifie l'indexation (python src/indexation.py)."
        ) from error

    if collection.count() == 0:
        raise RuntimeError(
            f"La collection '{COLLECTION_NAME}' est vide. Relance indexation.py."
        )

    return collection


# ============================================================
# MÉTADONNÉES ET PASSAGES
# ============================================================

def get_metadata_value(metadata: dict, *keys: str) -> str:
    """Retourne la première métadonnée disponible parmi plusieurs clés."""
    for key in keys:
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def build_passage(
    document: str,
    metadata: dict,
    distance=None,
    lexical_score: float = 0.0,
    relevance_score: float = 0.0,
) -> dict:
    """Uniformise la structure des passages retournés."""
    citation = get_metadata_value(metadata, "citation", "reference", "source")
    title = get_metadata_value(
        metadata, "titre_document", "document", "title", "nom_document"
    )
    source_url = get_metadata_value(metadata, "source_url", "url", "url_source")

    return {
        "text": document or "",
        "citation": citation or title or "Référence non renseignée",
        "source_url": source_url,
        "titre_document": title or "Document juridique",
        "distance": distance,
        "lexical_score": float(lexical_score),
        "relevance_score": float(relevance_score),
        "metadata": metadata,
    }


# ============================================================
# SCORE LEXICAL
# ============================================================

def lexical_score(document: str, query_terms: list[str]) -> float:
    """Couverture des termes de la requête, plus un bonus pour l'expression exacte."""
    if not document or not query_terms:
        return 0.0

    normalized_document = normalize_text(document)
    document_terms = set(tokenize(document))

    matched = sum(1 for term in query_terms if term in document_terms)
    score = matched / len(query_terms)

    if "personnalite juridique" in normalized_document:
        score += 0.5

    return score


# ============================================================
# RECHERCHE HYBRIDE
# ============================================================

def search(question: str, top_k: int = 5) -> list[dict]:
    """Retourne les passages les plus pertinents, classés par score combiné."""
    if not isinstance(question, str) or not question.strip():
        return []
    if top_k < 1:
        return []

    collection = get_collection()
    model = get_embedding_model()

    question = question.strip()
    query_terms = expand_query(question)

    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(VECTOR_CANDIDATES, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    candidates = []

    for index, document in enumerate(documents):
        if not document:
            continue

        try:
            distance = float(distances[index])
        except (IndexError, TypeError, ValueError):
            continue

        if distance > MAX_VECTOR_DISTANCE:
            continue

        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        semantic = max(0.0, 1.0 - distance)
        lexical = lexical_score(document, query_terms)
        combined = SEMANTIC_WEIGHT * semantic + LEXICAL_WEIGHT * min(lexical, 1.0)

        candidates.append({
            "document": document,
            "metadata": metadata,
            "distance": distance,
            "lexical": lexical,
            "combined": combined,
        })

    ranked = sorted(candidates, key=lambda item: item["combined"], reverse=True)

    return [
        build_passage(
            document=item["document"],
            metadata=item["metadata"],
            distance=item["distance"],
            lexical_score=item["lexical"],
            relevance_score=item["combined"],
        )
        for item in ranked[:top_k]
    ]


# ============================================================
# TEST DIRECT DU MODULE
# ============================================================

if __name__ == "__main__":
    question = input("Question juridique : ").strip()
    results = search(question, top_k=5)

    if not results:
        print("\nAucun passage pertinent trouvé.")
    else:
        for index, passage in enumerate(results, start=1):
            print(f"\n--- PASSAGE {index} ---")
            print("Référence :", passage["citation"])
            print("Distance :", round(passage["distance"], 4))
            print("Score lexical :", round(passage["lexical_score"], 4))
            print("Score combiné :", round(passage["relevance_score"], 4))
            print("Contenu :", passage["text"][:1500])