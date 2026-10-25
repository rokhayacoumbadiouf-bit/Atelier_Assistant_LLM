"""
Indexation vectorielle du corpus juridique sénégalais.

Entrée : data/processed/chunks.jsonl
Sortie : data/vectorstore/

Lancer depuis la racine du projet : python src/indexation.py
"""

import json
from collections import Counter

import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    CHUNKS_FILE,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    VECTORSTORE_DIR,
)


BATCH_SIZE = 16

METADATA_KEYS = [
    "unit_id", "doc_id", "titre_document", "type_document", "citation",
    "source_url", "version_texte", "date_consultation", "article",
    "intitule", "extraction", "statut_version", "context",
]
METADATA_INT_KEYS = ["page_start", "page_end", "chunk_index", "chunk_count"]


def load_chunks(path: str) -> list[dict]:
    """Charge les passages produits par chunking.py."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Fichier introuvable : {path}\n"
            "Exécute d'abord : python src/chunking.py"
        )


def verifier_ids(chunks: list[dict]) -> None:
    """Stoppe si deux passages partagent le même chunk_id."""
    compte = Counter(chunk["chunk_id"] for chunk in chunks)
    doublons = [cid for cid, n in compte.items() if n > 1]
    if doublons:
        raise ValueError(
            f"{len(doublons)} chunk_id en double, exemple : {doublons[:5]}"
        )


def verifier_troncature(model: SentenceTransformer, documents: list[str]) -> None:
    """Indique combien de passages dépassent la fenêtre du modèle."""
    limite = model.max_seq_length
    trop_longs = sum(
        1 for texte in documents
        if len(model.tokenizer.encode(texte)) > limite
    )
    print(f"Longueur max du modèle : {limite} tokens")
    print(f"Passages tronqués : {trop_longs}/{len(documents)}")


def clean_metadata(chunk: dict) -> dict:
    """Ne conserve que les métadonnées simples acceptées par ChromaDB."""
    metadata = {}

    for key in METADATA_KEYS:
        value = chunk.get(key)
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value

    for key in METADATA_INT_KEYS:
        value = chunk.get(key)
        if isinstance(value, int):
            metadata[key] = value

    # Évite un dictionnaire vide, refusé par certaines versions de ChromaDB.
    return metadata or {"chunk_id": chunk["chunk_id"]}


def main():
    chunks = load_chunks(CHUNKS_FILE)

    if not chunks:
        raise ValueError("Le fichier chunks.jsonl ne contient aucun passage.")

    verifier_ids(chunks)
    print(f"Passages chargés : {len(chunks)}")

    print(f"Chargement du modèle : {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    documents_tous = [chunk["searchable_text"] for chunk in chunks]
    verifier_troncature(model, documents_tous)

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Supprime les anciens passages absents du corpus actuel.
    current_ids = {chunk["chunk_id"] for chunk in chunks}
    existing_ids = collection.get(include=[])["ids"]
    obsolete_ids = [cid for cid in existing_ids if cid not in current_ids]
    if obsolete_ids:
        collection.delete(ids=obsolete_ids)
        print(f"Passages obsolètes supprimés : {len(obsolete_ids)}")

    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        ids = [chunk["chunk_id"] for chunk in batch]
        documents = [chunk["searchable_text"] for chunk in batch]
        metadatas = [clean_metadata(chunk) for chunk in batch]

        embeddings = model.encode(
            documents,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings.tolist(),
        )

        print(f"Indexation : {min(start + len(batch), total)}/{total}")

    print("\nIndexation terminée.")
    print(f"Passages indexés : {collection.count()}")
    print(f"Base vectorielle : {VECTORSTORE_DIR}")
    print(f"Collection : {COLLECTION_NAME}")


if __name__ == "__main__":
    main()