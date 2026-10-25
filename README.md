# ⚖️ Assistant juridique intelligent — RAG

**Projet d'assistant juridique fondé sur le Retrieval-Augmented Generation (RAG), conçu pour rechercher des informations dans un corpus documentaire juridique et générer des réponses sourcées en français.**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![ChromaDB](https://img.shields.io/badge/Vector%20Database-ChromaDB-green)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black)](https://ollama.com/)
[![Streamlit](https://img.shields.io/badge/Interface-Streamlit-red)](https://streamlit.io/)

## 1. Présentation du projet

Ce projet consiste à développer un assistant conversationnel capable de répondre à des questions juridiques en français en s'appuyant sur un corpus documentaire public, notamment des textes juridiques sénégalais.

Contrairement à un chatbot qui s'appuie uniquement sur les connaissances acquises pendant son entraînement, l'assistant utilise une approche **RAG (Retrieval-Augmented Generation)** : il recherche d'abord des passages pertinents dans une base documentaire, puis transmet ces passages à un modèle de langage pour produire une réponse contextualisée.

L'objectif est de proposer un outil qui facilite la recherche d'informations juridiques, conserve les références des documents consultés et limite les réponses non justifiées par les sources disponibles.

> **Avertissement :** cet assistant est un outil expérimental d'information documentaire. Ses réponses ne constituent pas un avis juridique professionnel. Les textes doivent être vérifiés dans leurs versions officielles et à jour avant toute utilisation juridique.

## 2. Objectifs

Le projet vise à :

- constituer et préparer un corpus documentaire juridique exploitable ;
- découper les documents en passages adaptés à la recherche ;
- transformer les passages en représentations vectorielles (*embeddings*) ;
- indexer les passages dans une base vectorielle ;
- retrouver les extraits pertinents à partir d'une question en langage naturel ;
- générer des réponses fondées sur les passages récupérés ;
- afficher les références des sources utilisées ;
- refuser de répondre lorsque les informations disponibles sont insuffisantes ;
- évaluer la pertinence des résultats et la fidélité des réponses générées.

## 3. Technologies utilisées

| Technologie | Rôle |
|---|---|
| Python 3.11 | Langage principal |
| Sentence Transformers | Calcul des embeddings des passages et des questions |
| ChromaDB | Stockage et recherche vectorielle |
| Ollama | Exécution locale du modèle de langage |
| Qwen 2.5 (7B prévu ; 3B utilisé pour l'évaluation, PC de 8 Go) | Génération des réponses |
| Requests | Communication HTTP avec l'API Ollama |
| Streamlit | Interface utilisateur web |
| Git et GitHub | Gestion du code et collaboration |

**Important :** le modèle de génération et le modèle d'embeddings sont deux composants distincts. Qwen 2.5 7B sert à générer les réponses. Le modèle d'embeddings doit être celui défini dans `src/config.py` et correspondre au modèle utilisé pour construire l'index vectoriel.

## 4. Architecture du système RAG

Le fonctionnement général du système suit les étapes ci-dessous.

```text
Corpus juridique public
          |
          v
1. Ingestion et préparation
          |
          v
articles.jsonl
          |
          v
2. Découpage en passages
          |
          v
chunks.jsonl
          |
          v
3. Calcul des embeddings
          |
          v
4. Indexation dans ChromaDB
          |
          v
5. Question de l'utilisateur
          |
          v
6. Recherche des passages pertinents
          |
          v
7. Construction du contexte
          |
          v
8. Génération par Qwen via Ollama
          |
          v
9. Réponse sourcée et affichage
          |
          v
10. Vérification des citations et des limites
```

### Explication des étapes

**1. Ingestion du corpus**

Les documents sont collectés et préparés pour être exploitables par le système. Les informations textuelles et les métadonnées utiles sont conservées dans un format structuré.

**2. Découpage en passages (*chunking*)**

Les documents sont divisés en unités plus petites afin de permettre une recherche ciblée. Le découpage doit préserver autant que possible le sens juridique des articles et de leurs subdivisions.

**3. Calcul des embeddings**

Chaque passage est converti en représentation numérique permettant de comparer son contenu avec celui d'une question.

**4. Indexation vectorielle**

Les représentations sont enregistrées dans ChromaDB pour permettre leur récupération lors d'une requête.

**5. Recherche**

La question est vectorisée à l'aide du même modèle d'embeddings que celui utilisé pour l'indexation. Les passages candidats sont récupérés et classés selon leur pertinence.

**6. Construction du contexte**

Les passages retenus, accompagnés de leurs références, sont assemblés pour constituer le contexte transmis au modèle de langage.

**7. Génération**

Ollama exécute Qwen 2.5 7B pour produire une réponse à partir de la question et du contexte documentaire.

**8. Contrôle des sources**

Les citations produites doivent correspondre aux extraits réellement transmis au modèle. Une vérification automatique des numéros de citations ne garantit pas, à elle seule, que leur contenu justifie effectivement la réponse.

## 5. État actuel du projet

Le corpus compte actuellement **4 367 unités**, selon le dernier décompte communiqué.

| Élément | État |
|---|---|
| Préparation initiale du corpus | Réalisée |
| Fichier `articles.jsonl` | Disponible |
| Découpage en passages | Réalisé précédemment ; à actualiser si le corpus a changé |
| Fichier `chunks.jsonl` | Disponible ; nombre actuel de passages à vérifier |
| Base vectorielle ChromaDB | Créée précédemment ; synchronisation à vérifier |
| Fonction de recherche | Implémentée et testée sur des exemples |
| Génération avec Ollama et Qwen | Module préparé ; validation systématique nécessaire |
| Vérification des citations | Contrôle élémentaire implémenté ; qualité à évaluer |
| Interface Streamlit | Préparée ; test de bout en bout nécessaire |
| Évaluation sur un jeu de questions | **Réalisée** : 20 questions, 2 passages d'évaluation (voir section 10) |
| Rapport final et démonstration | Rapport rédigé (`reports/rapport.md`) ; démonstration à préparer |

Un premier test de recherche a notamment retrouvé l'article 1 du Code de la famille pour une question relative au commencement de la personnalité juridique. Ce résultat constitue un test fonctionnel initial, et non une preuve de performance générale.

**Point de vigilance :** le nombre d'unités du corpus, le nombre de passages après découpage et le nombre de documents indexés dans ChromaDB sont trois mesures différentes. Elles doivent être vérifiées séparément.

## 6. Organisation des fichiers

L'organisation cible du projet est la suivante. Certains emplacements doivent être confirmés à partir de l'arborescence effective du dépôt.

```text
Atelier_Assistant_LLM/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/                      (documents sources d'origine)
│   ├── processed/
│   │   ├── articles.jsonl
│   │   └── chunks.jsonl
│   ├── vectorstore/              (index ChromaDB)
│   ├── manifest.csv              (registre des sources)
│   └── evaluation/
│       └── questions.json        (jeu de 20 questions d'évaluation)
│
├── reports/
│   ├── rapport.md                (rapport d'évaluation)
│   ├── results_run1.csv, summary_run1.md        (évaluation, top_k = 5)
│   └── results_run2_k8.csv, summary_run2_k8.md  (amélioration testée, top_k = 8)
│
└── src/
    ├── config.py
    ├── ingest.py
    ├── chunking.py
    ├── indexation.py
    ├── retrieval.py
    ├── rag.py
    ├── app.py
    ├── evaluate.py               (évaluation : Recall@k, notation guidée, résumé)
    └── outils_notes.py           (contrôle des références, correction de notes)
```

### Rôle des fichiers

- `README.md` : documentation du projet et instructions d'utilisation.
- `requirements.txt` : dépendances Python.
- `data/processed/articles.jsonl` : unités documentaires préparées.
- `data/processed/chunks.jsonl` : passages obtenus après découpage.
- `data/vectorstore/` : stockage persistant de l'index vectoriel.
- `src/config.py` : paramètres de configuration.
- `src/ingest.py` : ingestion et préparation des documents.
- `src/retrieval.py` : recherche et classement des passages.
- `src/rag.py` : construction du contexte et génération des réponses.
- `src/app.py` : interface Streamlit, si le fichier est placé dans `src/`.
- `src/chunking.py` et `src/indexation.py` : découpage en passages et indexation dans ChromaDB.
- `data/evaluation/questions.json` : jeu de 20 questions avec réponses de référence et preuves attendues.
- `src/evaluate.py` : exécution du jeu de questions, calcul du Recall@k, notation guidée et résumé.
- `src/outils_notes.py` : contrôle des numéros d'articles attendus et correction de notes.
- `reports/` : résultats d'évaluation et rapport.

Les noms de fichiers et leur emplacement doivent correspondre au dépôt réel. Si l'interface se trouve à la racine du projet, sa commande de lancement sera différente.

## 7. Installation et configuration

### Prérequis

Avant de commencer, installer :

1. Python 3.11 : https://www.python.org/downloads/
2. Git : https://git-scm.com/downloads
3. Ollama : https://ollama.com/download

Une connexion Internet est nécessaire pour récupérer le dépôt, installer les bibliothèques et télécharger les modèles lors de la première installation. Une fois les composants téléchargés, une partie du fonctionnement peut s'effectuer localement.

### Étape 1 — Cloner le dépôt

Dans PowerShell ou un terminal :

```powershell
git clone https://github.com/rokhayacoumbadiouf-bit/Atelier_Assistant_LLM.git
cd Atelier_Assistant_LLM
```

Le dépôt pèse environ 160 Mo. Si le clonage échoue (« early EOF »), relancer avec un clone léger :

```powershell
git config --global http.postBuffer 524288000
git config --global http.version HTTP/1.1
git clone --depth 1 https://github.com/rokhayacoumbadiouf-bit/Atelier_Assistant_LLM.git
```

### Étape 2 — Créer un environnement virtuel

```powershell
py -3.11 -m venv .venv
```

Activer l'environnement :

```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell bloque l'activation (« l'exécution de scripts est désactivée »), autoriser les scripts pour la fenêtre en cours uniquement, puis réactiver :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Ou bien utiliser un terminal Command Prompt et exécuter :

```bat
.venv\Scripts\activate.bat
```

### Étape 3 — Installer les dépendances Python

Mettre à jour pip :

```powershell
python -m pip install --upgrade pip
```

Installer les bibliothèques à partir du fichier de dépendances :

```powershell
python -m pip install -r requirements.txt
```

Le fichier `requirements.txt` doit contenir les dépendances réellement nécessaires au projet. À défaut, les bibliothèques principales identifiées sont `sentence-transformers`, `chromadb`, `requests` et `streamlit`.

### Étape 4 — Installer le modèle de génération

Télécharger Qwen 2.5 7B avec Ollama :

```powershell
ollama pull qwen2.5:7b
```

Vérifier que le modèle est disponible :

```powershell
ollama list
```

Le modèle doit apparaître sous le nom `qwen2.5:7b`.

Le modèle peut nécessiter plusieurs gigaoctets de stockage et une quantité suffisante de mémoire vive. Les performances dépendent de la configuration matérielle.

**PC de 8 Go de mémoire :** le modèle 7B est trop lourd. L'évaluation a été réalisée avec `qwen2.5:3b` (`ollama pull qwen2.5:3b`). `src/evaluate.py` utilise `qwen2.5:3b` par défaut ; pour utiliser un autre modèle, définir la variable d'environnement avant de lancer l'évaluation (par exemple `$env:OLLAMA_MODEL="qwen2.5:7b"`). L'application Streamlit utilise, elle, le nom du modèle défini dans `src/rag.py` (`OLLAMA_MODEL`).

### Étape 5 — Vérifier le modèle d'embeddings

Ouvrir `src/config.py` et repérer le paramètre `EMBEDDING_MODEL_NAME`.

Le modèle configuré doit être identique à celui qui a servi à construire l'index ChromaDB. Il est possible que les poids du modèle soient téléchargés lors de sa première utilisation.

**Ne pas changer le modèle d'embeddings sans vérifier la compatibilité avec l'index existant.** Si le modèle doit changer, les embeddings des passages doivent être recalculés et la base réindexée de façon cohérente.

### Étape 6 — Vérifier les données

Confirmer que les fichiers suivants sont présents :

- `data/processed/articles.jsonl`
- `data/processed/chunks.jsonl`, si le découpage a déjà été effectué
- `data/vectorstore/`, si l'index existant est fourni

Si les données ou l'index ne sont pas inclus dans le dépôt, il faut récupérer les fichiers nécessaires auprès de l'équipe ou exécuter les scripts de préparation et d'indexation disponibles dans le projet.

Ne pas relancer l'indexation sans avoir vérifié les scripts, les chemins et le nom de la collection configurée.

## 8. Lancement de l'application

Si `app.py`, `rag.py` et `retrieval.py` sont placés dans le dossier `src/`, lancer depuis la racine du dépôt :

```powershell
python -m streamlit run src/app.py
```

Si `app.py` est placé à la racine, utiliser plutôt :

```powershell
python -m streamlit run app.py
```

Streamlit indique ensuite l'adresse locale à ouvrir dans le navigateur.

### Vérifications en cas de problème

- **Module introuvable :** vérifier l'environnement virtuel et l'emplacement des fichiers Python.
- **Erreur de connexion à Ollama :** vérifier qu'Ollama est installé, que son service fonctionne et que le modèle est téléchargé.
- **Modèle introuvable :** vérifier le nom utilisé dans `src/rag.py` et la sortie de `ollama list`.
- **Aucun passage pertinent :** vérifier le corpus, l'index, le modèle d'embeddings et les paramètres de recherche.
- **Erreur ChromaDB :** vérifier le chemin de la base, le nom de la collection et la compatibilité de l'index avec le modèle utilisé.
- **Réponse sans citation correcte :** vérifier les extraits fournis au modèle et la correspondance entre leurs numéros et les sources affichées.

## 9. Recherche et génération : points de contrôle

### Qualité de la recherche

La pertinence des résultats est essentielle : même un bon modèle de langage ne peut pas produire une réponse fiable si les passages récupérés sont hors sujet ou incomplets.

La fonction de recherche doit notamment être évaluée sur :
- la présence du passage juridique attendu parmi les premiers résultats ;
- la pertinence des extraits récupérés ;
- la conservation des références et métadonnées ;
- le comportement face aux formulations différentes d'une même question ;
- le choix des seuils de distance et de classement.

Les seuils de similarité doivent être calibrés sur les résultats observés. Une distance vectorielle ne doit pas être interprétée automatiquement comme une probabilité de pertinence.

### Fiabilité de la génération

Le modèle doit être guidé pour :
- répondre uniquement à partir du contexte fourni ;
- citer les extraits qui soutiennent ses affirmations ;
- signaler les informations absentes ou insuffisantes ;
- éviter de fabriquer des articles, des références ou des URL ;
- distinguer ce que disent les documents de ce qu'ils ne permettent pas d'établir.

Le contrôle automatique du format des citations est utile, mais une vérification de leur pertinence juridique reste nécessaire.

### Limites du corpus

Le corpus peut contenir des erreurs de reconnaissance de caractères (OCR), des documents incomplets ou des versions qui ne sont plus en vigueur. La présence d'un texte dans la base ne garantit donc ni son actualité ni son applicabilité à une situation donnée.

L'assistant doit éviter de présenter une disposition comme étant en vigueur sans source permettant de le confirmer.

## 10. Évaluation du système

Un jeu de **20 questions juridiques avec réponses de référence** a été constitué (`data/evaluation/questions.json`) : 5 factuelles, 4 procédures, 4 conditions multiples, 3 multi-passages, 2 hors corpus, 2 ambiguës. Il a été écrit avant les essais. Les numéros d'articles attendus ont été contrôlés automatiquement dans le corpus (une référence sur 21 était erronée et a été corrigée).

Chaque question est évaluée selon les critères suivants :

| Critère | Question à vérifier |
|---|---|
| Pertinence de la recherche | Le passage attendu figure-t-il parmi les résultats ? (Recall@k, calcul automatique) |
| Fidélité de la réponse | La réponse respecte-t-elle le contenu des sources ? (note manuelle 0–2) |
| Exactitude et complétude | La réponse dit-elle la même chose que la référence, sans rien omettre ? (notes 0–2) |
| Exactitude des citations | Les références existent-elles et correspondent-elles aux extraits ? (note 0–2) |
| Gestion de l'incertitude | Le système refuse-t-il lorsque les sources sont insuffisantes ? |
| Latence | Combien de temps faut-il pour obtenir une réponse ? |

### Relancer l'évaluation

```powershell
python -m src.evaluate run --out reports/results_run1.csv                      # pose les 20 questions (top_k = 5)
python -m src.evaluate noter --results reports/results_run1.csv                # notation guidée à la main (0, 1, 2)
python -m src.evaluate summarize --results reports/results_run1.csv            # calcule le résumé
python src/outils_notes.py verifier                                            # contrôle les numéros d'articles attendus
python -m src.evaluate run --top-k 8 --out reports/results_run2_k8.csv         # variante testée : 8 passages
```

L'application doit pouvoir répondre (Ollama lancé, modèle téléchargé, index présent) avant de lancer `run`. Compter 10 à 15 minutes pour les 20 questions avec `qwen2.5:3b` sur un PC de 8 Go.

### Résultats du premier passage (top_k = 5, `qwen2.5:3b`)

| Indicateur | Valeur |
|---|---|
| Passage nécessaire retrouvé (Recall@5) | 0,94 (17 questions sur 18) |
| Exactitude / fidélité moyennes (0–2) | 1,50 / 1,65 |
| Complétude / citations moyennes (0–2) | 1,40 / 1,20 |
| Refus corrects sur les questions hors corpus | 2 sur 2 |
| Latence moyenne | 45,8 s par question |

Les questions à une seule règle sont très bien traitées ; celles qui demandent d'énumérer ou de combiner plusieurs règles le sont moins. Passer à 8 passages améliore la recherche (1,00) mais pas les réponses sur les cas examinés, et augmente la latence de 68 %. Le détail, les erreurs analysées et les limites figurent dans `reports/rapport.md`.

## 11. Collaboration et contribution

Le projet est développé dans le cadre d'un travail collaboratif.

Dépôt GitHub :

https://github.com/rokhayacoumbadiouf-bit/Atelier_Assistant_LLM

Pour contribuer :

1. Cloner le dépôt.
2. Créer et activer un environnement virtuel.
3. Installer les dépendances.
4. Vérifier la configuration et la disponibilité des données.
5. Tester la fonctionnalité sur laquelle on travaille.
6. Documenter les modifications apportées.
7. Envoyer les changements sur une branche de travail et ouvrir une pull request si ce mode de collaboration est retenu par l'équipe.

Il est recommandé de ne pas versionner l'environnement virtuel `.venv/`, les secrets, ni les fichiers volumineux générés automatiquement sans décision collective. Le traitement du corpus et de l'index doit être documenté afin que les membres de l'équipe puissent reproduire les étapes nécessaires.

## 12. Améliorations envisagées

Les pistes de travail prioritaires sont :

- améliorer le découpage des documents pour préserver la structure des articles ;
- évaluer et optimiser le classement des passages ;
- ajuster les paramètres de recherche sur un jeu de questions représentatif ;
- renforcer la vérification des citations ;
- améliorer la gestion des questions hors corpus ;
- tester la robustesse des réponses face aux erreurs OCR ;
- mesurer la latence et documenter les limites de performance ;
- finaliser l'interface et les messages d'erreur ;
- compléter la documentation technique et le rapport d'évaluation.

## 13. Conclusion

Ce projet met en œuvre les principaux composants d'un assistant juridique basé sur le RAG : préparation du corpus, découpage, embeddings, indexation vectorielle, récupération de passages et génération de réponses.

Le travail restant consiste principalement à vérifier la synchronisation des données et de l'index, à valider le fonctionnement de bout en bout, à mesurer la qualité de la recherche et des réponses, puis à documenter les résultats et les limites du système.

La priorité n'est pas seulement de faire fonctionner le chatbot, mais de garantir que ses réponses sont **traçables, justifiées par des sources identifiables et prudentes lorsque les informations disponibles ne suffisent pas**.

---

*Document de travail : les nombres de passages indexés, le modèle d'embeddings exact et l'état de l'interface doivent être confirmés par leurs responsables à partir de la version courante du dépôt avant de présenter ce README comme un état final du projet. Les résultats d'évaluation ci-dessus proviennent de `reports/`.*