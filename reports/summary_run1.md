# Résumé de l'évaluation

- Questions évaluées : 20 (18 avec réponse dans le corpus, 2 sans)
- **Recall@5** (au moins une preuve attendue dans le top-5) : 0.94 (n=18)
- Recall@5 strict (TOUS les passages nécessaires récupérés) : 0.89 (n=18)
- Couverture moyenne des preuves attendues : 0.92 (n=18)
- Latence moyenne : 45.83 s
- Erreurs d'exécution : 0

## Abstentions (détection automatique, à confirmer à la main)
- Questions SANS réponse où le système s'abstient (souhaité) : 2/2
- Questions AVEC réponse où le système s'abstient (abstention inutile) : 0/18

## Notation manuelle (0 à 2)
- exactitude : 1.50 (n=20)
- fidelite : 1.65 (n=20)
- completude : 1.40 (n=20)
- citations : 1.20 (n=20)
- Notation manuelle : refus appropriés = 2
- Notation manuelle : refus inutiles = 1
- Notation manuelle : pas de refus = 17
- Réponses inventées (marquées 'oui') : 1

## Par type de question

| Type | n | Recall@5 | Exactitude moy. |
|---|---|---|---|
| factuelle | 5 | 1.00 | 2.00 |
| procedure | 4 | 0.75 | 1.75 |
| conditions | 4 | 1.00 | 1.00 |
| multi_passages | 3 | 1.00 | 1.00 |
| absente | 2 | — | 2.00 |
| ambigue | 2 | 1.00 | 1.00 |

## Échecs de récupération (recall@5 = 0)
- P04 : Comment et quand un homme peut-il souscrire l'option de monogamie ou de limitation de polygamie ?