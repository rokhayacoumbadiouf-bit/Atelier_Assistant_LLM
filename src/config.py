"""Constantes partagées par le pipeline RAG.

Tous les chemins sont relatifs à la racine du projet :
lancer les scripts depuis la racine, par exemple
python src/rag.py
"""

ARTICLES_FILE = "data/processed/articles.jsonl"
CHUNKS_FILE = "data/processed/chunks.jsonl"
VECTORSTORE_DIR = "data/vectorstore"

COLLECTION_NAME = "corpus_juridique_senegalais"

# Modèle utilisé à l'indexation ET à la recherche. Doit rester identique.
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"