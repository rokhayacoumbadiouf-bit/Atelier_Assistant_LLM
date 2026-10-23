# Assistant RAG juridique sénégalais

Atelier pratique « LLM & Écosystème ». Ce dépôt suit la structure conseillée par le plan de travail.
Cette version contient la **partie de la Personne 1 (corpus et préparation des données)**.

```
llm-assistant/
├── data/raw/            # sources originales (15 fichiers fournis par l'équipe)
├── data/processed/      # textes extraits/nettoyés + articles.jsonl pour la personne 2
│   └── ocr/             #   cache OCR des PDF scannés (corrigeable à la main)
├── data/manifest.csv    # registre des sources
├── src/ingest.py        # extraction/nettoyage (+ OCR en lot et contrôle de traçabilité)
├── requirements.txt
└── README.md
```

Les autres éléments du plan viendront des autres membres : `data/evaluation/questions.json`, `src/chunking.py`, `src/indexing.py`, `src/rag.py`, `src/evaluate.py`, `app.py` et `reports/`.

## Installation et lancement (VS Code)

Il faut Python 3.10 ou plus récent. Tesseract OCR (langue `fra`) est facultatif : il ne sert qu'à OCR de **nouvelles** pages scannées, car les 424 pages déjà traitées sont dans le cache.

Ouvrir le dossier `llm-assistant` dans VS Code (Fichier > Ouvrir le dossier). Ensuite, menu **Terminal > Exécuter la tâche…** :

| Tâche VS Code | Commande équivalente (PowerShell) |
|---|---|
| 1. Installer l'environnement Python | `python -m venv .venv` puis `.venv\Scripts\python -m pip install -r requirements.txt` |
| 2. Ingestion + contrôle de traçabilité (`Ctrl+Maj+B`) | `.venv\Scripts\python src\ingest.py` |
| 3. Contrôle de traçabilité seul | `.venv\Scripts\python src\ingest.py --controle --sample 3` |
| 4. OCR des pages scannées manquantes, puis ingestion | `.venv\Scripts\python src\ingest.py --ocr` |

Le résultat attendu est « 3919 unités écrites » puis « Traçabilité : 3905/3919 unités retrouvées (99.6 %) ».
**Exécuter et déboguer** (F5) permet de suivre l'ingestion pas à pas, sur tout le manifeste ou sur un seul document (`--only <id>`).

## Procédure suivie (plan, section 1)

1. Documents publics fournis par l'équipe, enregistrés tels quels dans `data/raw/`.
2. Registre `data/manifest.csv` : id, titre, organisme, URL, format, date de consultation, version/date du texte. Il contient aussi le type (normatif ou explicatif), les pages, le filtre, les options et le SHA-256.
3. Extraction avec PyMuPDF (colonnes respectées), pypdf en secours, BeautifulSoup pour le HTML, et OCR tesseract pour les scans.
4. Nettoyage des en-têtes, pieds de page, numéros de page et sommaires, **sans toucher** aux titres ni à la numérotation des articles.
5. Textes nettoyés et unités par article dans `data/processed/`.
6. Contrôle : chaque unité est recherchée dans sa page source (`traceability_report.csv`), et des pages ont été vérifiées à la main sur l'image.

**Ajouter un document** : placer le fichier dans `data/raw/`, ajouter sa ligne dans le manifeste (options `ocr=oui`, `intitules=oui` ou `pages=oui`, selon le cas), puis relancer la tâche 2 (ou la 4 pour un scan).

## Corpus (Personne 1)

| Fichier de `data/processed/` | Contenu |
|---|---|
| `articles.jsonl` | **le livrable pour la personne 2** : 3 919 unités normalisées, une par article (ou une par page pour les documents sans articles) |
| `<id>.txt` | le texte nettoyé de chaque document, avec ses marqueurs `[[page N]]` |
| `<id>.json` | les métadonnées, la qualité, les pages et les articles de chaque document |
| `quality_report.csv` | les contrôles par document : pages, pages OCR, articles détectés, doublons, sauts de numérotation, statut |
| `traceability_report.csv` | pour chaque unité, si son texte est retrouvé dans sa page source |
| `exemples_passages.md` | 12 unités commentées pour la personne 2, et des questions de test |
| `ocr/` | le cache OCR (une page = un .txt) ; les corrections manuelles sont listées dans `ocr/CORRECTIONS.md` |

### Sources et versions

| id (manifeste) | Document | Type | Version retenue | Extraction |
|---|---|---|---|---|
| `cf-*` (14 extraits) | Code de la famille, découpé par livre et titre | normatif | Loi 72-61 du 12/06/1972, version consolidée du Ministère de la Justice | texte natif |
| `cf-export-txt` | Code de la famille, export .txt | (non ingéré) | doublon du PDF, vérifié identique à 100 % | non |
| `constitution` | Constitution du 22/01/2001 | normatif | consolidée par le Conseil constitutionnel **jusqu'à la LC 2018-14** | texte natif |
| `constitution-historique` | Notes historiques de la Constitution (p. 48-54) | explicatif | idem | texte natif |
| `an-reglement-interieur` | Règlement intérieur de l'Assemblée nationale | normatif | Loi organique 2025-11 du 18/08/2025 | texte natif |
| `cocc` | Code des obligations civiles et commerciales | normatif | édition non datée ; certains articles sont remplacés par les AU OHADA reproduits | export .txt |
| `code-construction` | Code de la construction | normatif | Loi 2023-21 du 29/12/2023 | OCR |
| `code-urbanisme` | Code de l'urbanisme | normatif | Loi 2023-20 du 29/12/2023, JO 7694 du 17/01/2024 | OCR |
| `code-electoral-legislatif` / `-reglementaire` | Code électoral, édition 2023 | normatif | loi 2021-35 modifiée en 2022 et 2023 ; décret 2021-1196 modifié en 2023 | OCR |
| `ohada-au-dcg` | AU droit commercial général | normatif | 15/12/2010, JO OHADA n° 23 | OCR |
| `ohada-au-suretes` | AU sûretés | normatif | 15/12/2010, JO OHADA n° 22 | OCR |
| `guide-adoption-internationale` | Guide de l'adoption internationale (DESPS) | explicatif | édition 2019 | texte natif |
| `snpe` | Stratégie nationale de protection de l'enfant | politique publique | 2013, édition 2016 | texte natif |
| `desps-outils` | Outils d'intervention harmonisés (DESPS) | explicatif | 2012 | texte natif |
| `desps-audit` | Rapport d'audit des centres (DESPS) | rapport | février 2018 | export .txt |
| `somisen-code-conduite` | Code de conduite et d'éthique SOMISEN | règlement interne | 2025 | OCR (scan de basse qualité) |

Le plan de travail (PDF) a été exclu du corpus, car ce n'est pas une source juridique.

### Format d'une unité (`articles.jsonl`)

```python
import sys; sys.path.insert(0, "src")
from ingest import load_units
units = load_units()          # liste de dicts
```

| Champ | Sens |
|---|---|
| `unit_id` | identifiant stable, par exemple `code-electoral-legislatif::art-L.53` ou `snpe::p12` |
| `doc_id`, `titre_document`, `type_document` | le document (même id que dans le manifeste) ; type : normatif, explicatif, politique publique, rapport ou règlement interne |
| `source_url`, `version_texte`, `date_consultation` | la traçabilité et la version |
| `article`, `intitule` | le numéro (`1`, `L.53`, `R.12`, `LO.142`, `202 AU/DCG`) et le titre de l'article, s'il en a un |
| `partie`, `livre`, `titre`, `chapitre`, `section`, `paragraphe`, `rubrique` | la position dans la structure du texte |
| `modification` | la note de modification (par exemple dans la Constitution consolidée) |
| `page_start`, `page_end` | les pages du fichier dans `data/raw/` (numéros de page PDF) |
| `citation` | la référence prête à afficher, par exemple « Code électoral, art. L.53 (p. 30) » |
| `text` | le texte nettoyé (sans en-têtes, pieds de page ni numéros de page) |
| `extraction` | « texte natif » ou « ocr à vérifier » |
| `statut_version` | « texte tel que publié par la source » (ou « remplacé par … » si un texte plus récent du corpus le modifie) |

### Contrôles

- **Lisibilité** : les 15 documents sont lisibles. Sept PDF sont des scans ou ont une couche texte cassée et ont été passés en OCR (424 pages), ce que signalent le statut `ocr_a_verifier` dans `quality_report.csv` et le champ `extraction`.
- **Traçabilité** (`python src/ingest.py --controle`) : sur 3 919 unités, **3 905 (99,6 %)** sont retrouvées intégralement dans leurs pages sources. Les 14 autres sont retrouvées en partie. Il s'agit de pages explicatives avec des tableaux, de préambules OHADA et SOMISEN, et de 4 articles de l'urbanisme à cheval sur deux colonnes. Aucune unité n'est introuvable.
- **Numérotation** : tous les sauts restants viennent des sources elles-mêmes :
  - Code de la famille : l'art. 688 est absent du PDF.
  - COCC : les art. 392-432, 473-495 et 584-638 sont abrogés et remplacés par les articles AU/DCG reproduits.
  - AU sûretés : l'art. 179 est perdu dans le scan.
  - SOMISEN : le n° 30 est imprimé deux fois.
- **Versions** : la Constitution n'intègre pas les révisions postérieures à 2018. Le Code électoral est l'édition 2023. Le COCC n'est pas daté.

### Conseils pour la personne 2 (découpage et indexation)

- La médiane est de 362 caractères par unité : **un article = un chunk** convient. Seules 78 unités dépassent 3 000 caractères, par exemple les articles de définitions L.2 de l'urbanisme et de la construction. Pour celles-là, il vaut mieux découper par alinéa en répétant `citation` et la hiérarchie.
- Il est utile de préfixer chaque chunk par son contexte, par exemple « Code électoral > Partie législative > Titre I > Chapitre II : art. L.53 : … ». Cela améliore la recherche sur les questions générales.
- Filtrer ou pondérer selon `type_document` : une réponse juridique doit citer en priorité les textes **normatifs**. Le code SOMISEN est un règlement interne d'entreprise.
- Les unités marquées « ocr à vérifier » peuvent contenir des coquilles. Afficher toujours `citation` et `source_url` pour que l'utilisateur puisse vérifier.

### Limites connues

- Le corpus couvre plusieurs domaines (famille, constitutionnel, électoral, urbanisme, OHADA, protection de l'enfance…), parce qu'il reprend tous les documents fournis. Le plan recommandait un seul domaine.
- L'OCR n'a pas été relu en entier : seules 6 corrections ponctuelles ont été faites (voir `data/processed/ocr/CORRECTIONS.md`).
- Le COCC et le rapport d'audit DESPS viennent d'exports .txt. Leurs « pages » sont des blocs de l'export, pas les pages imprimées, et les intitulés du COCC sont déduits automatiquement.
- Quelques titres de hiérarchie sont tronqués quand ils tiennent sur deux lignes dans la source.
- Le premier corpus, centré sur le droit de la famille (avec le Code pénal et les lois 2013-05 et 2020-05), n'est pas dans le projet. Il est archivé à part.
