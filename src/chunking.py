"""
Découpage des unités juridiques pour le système RAG.

Entrée : data/processed/articles.jsonl
Sortie : data/processed/chunks.jsonl
"""

import json
import re

from config import ARTICLES_FILE, CHUNKS_FILE


# Taille maximale indicative d'un passage, en caractères.
MAX_CHARS = 1500

# Lettres minuscules françaises, pour la réparation des coupures de mots.
MINUSCULES = "a-zàâçéèêëîïôûùüÿñæœ"


# ============================================================
# NETTOYAGE DU TEXTE
# ============================================================

def nettoyer_texte(text: str) -> str:
    """Répare les coupures de mots et les espaces parasites des PDF."""
    text = str(text or "").replace("\r", "\n")

    # Coupure en fin de ligne : "imma-\ntriculation" -> "immatriculation"
    text = re.sub(
        rf"([{MINUSCULES}])-\s*\n\s*([{MINUSCULES}])",
        r"\1\2",
        text,
    )

    # Coupure avec espace : "imma- triculation" -> "immatriculation"
    # Seules les minuscules des deux côtés sont concernées, pour éviter
    # de fusionner des noms propres comme "Dakar- Plateau".
    text = re.sub(
        rf"([{MINUSCULES}])-\s+([{MINUSCULES}])",
        r"\1\2",
        text,
    )

    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ============================================================
# DÉCOUPAGE
# ============================================================

def split_long_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Découpe un texte en passages, en privilégiant les paragraphes."""
    text = nettoyer_texte(text)
    if not text:
        return []

    # Un paragraphe = un bloc séparé par une ligne vide.
    # Dans un paragraphe, les retours à la ligne deviennent des espaces.
    paragraphs = [
        re.sub(r"\s*\n\s*", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        # Paragraphe trop long : découpage par phrases.
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            fragment = ""
            for sentence in re.split(r"(?<=[.!?;])\s+", paragraph):
                # Phrase elle-même trop longue : découpage brutal.
                if len(sentence) > max_chars:
                    if fragment:
                        chunks.append(fragment)
                        fragment = ""
                    for start in range(0, len(sentence), max_chars):
                        chunks.append(sentence[start:start + max_chars])
                    continue

                candidate = f"{fragment} {sentence}".strip()
                if len(candidate) <= max_chars:
                    fragment = candidate
                else:
                    if fragment:
                        chunks.append(fragment)
                    fragment = sentence

            if fragment:
                chunks.append(fragment)
            continue

        # Paragraphe normal : on l'ajoute au passage courant si la taille le permet.
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


# ============================================================
# CONTEXTE ET PASSAGES
# ============================================================

def build_context(unit: dict) -> str:
    """Construit le fil d'Ariane de l'article. Stocké en métadonnée, pas vectorisé."""
    parts = [
        unit.get("titre_document", ""),
        unit.get("partie", ""),
        unit.get("livre", ""),
        unit.get("titre", ""),
        unit.get("chapitre", ""),
        unit.get("section", ""),
        unit.get("paragraphe", ""),
        unit.get("rubrique", ""),
    ]

    clean_parts = []
    for part in parts:
        part = str(part).strip()
        if part and part not in clean_parts:
            clean_parts.append(part)

    article = unit.get("article", "")
    if article:
        clean_parts.append(f"Article {article}")

    return " > ".join(clean_parts)


def make_chunks(units: list[dict]) -> list[dict]:
    """Transforme les unités du corpus en passages indexables."""
    chunks = []

    for unit in units:
        text = str(unit.get("text", "")).strip()
        if not text:
            continue

        context = build_context(unit)
        citation = unit.get("citation", "")
        source_url = unit.get("source_url", "")

        parts = split_long_text(text)

        # En-tête court : titre du document et chapitre seulement.
        entete = " > ".join(
            p for p in [
                str(unit.get("titre_document", "")).strip(),
                str(unit.get("chapitre", "")).strip(),
            ]
            if p
        )

        for index, part in enumerate(parts, start=1):
            chunk_id = f"{unit.get('unit_id', 'unit')}::chunk-{index}"

            # Texte vectorisé : référence, en-tête court, puis contenu de l'article.
            searchable_text = f"{citation} | {entete}\n\n{part}"

            chunks.append({
                "chunk_id": chunk_id,
                "unit_id": unit.get("unit_id", ""),
                "doc_id": unit.get("doc_id", ""),
                "titre_document": unit.get("titre_document", ""),
                "type_document": unit.get("type_document", ""),
                "citation": citation,
                "source_url": source_url,
                "version_texte": unit.get("version_texte", ""),
                "date_consultation": unit.get("date_consultation", ""),
                "article": unit.get("article", ""),
                "intitule": unit.get("intitule", ""),
                "page_start": unit.get("page_start"),
                "page_end": unit.get("page_end"),
                "extraction": unit.get("extraction", ""),
                "statut_version": unit.get("statut_version", ""),
                "chunk_index": index,
                "chunk_count": len(parts),
                "text": part,
                "context": context,
                "searchable_text": searchable_text,
            })

    return chunks


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    try:
        with open(ARTICLES_FILE, "r", encoding="utf-8") as file:
            units = [json.loads(line) for line in file if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Corpus introuvable : {ARTICLES_FILE}\n"
            "Vérifie que src/ingest.py a généré articles.jsonl."
        )

    chunks = make_chunks(units)

    ids = [chunk["chunk_id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Des chunk_id sont en double. Vérifie les unit_id.")

    with open(CHUNKS_FILE, "w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print("Découpage terminé.")
    print(f"Unités juridiques lues : {len(units)}")
    print(f"Passages créés : {len(chunks)}")
    print(f"Fichier de sortie : {CHUNKS_FILE}")

    if chunks:
        example = chunks[0]
        print("\nExemple de passage :")
        print(f"ID : {example['chunk_id']}")
        print(f"Référence : {example['citation']}")
        print(f"Texte : {example['text'][:300]}")


if __name__ == "__main__":
    main()