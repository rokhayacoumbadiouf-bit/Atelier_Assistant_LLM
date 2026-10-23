# Cache OCR : mode d'emploi et corrections manuelles

`src/ingest.py` lit le texte OCR des pages scannées dans `data/processed/ocr/<nom du PDF>/pNNN.txt`
(numéro de page PDF sur 3 chiffres). Ce cache est produit par `python src/ingest.py --ocr`
(tesseract, langue `fra`, 300 dpi). Une page déjà présente n'est pas refaite.

**Pour corriger une erreur d'OCR** : modifier le fichier `pNNN.txt` concerné, puis relancer
`python src/ingest.py` (qui refait aussi le contrôle de traçabilité). Pour refaire l'OCR d'une page,
supprimer son fichier puis lancer `python src/ingest.py --ocr`.

## Corrections déjà faites (vérifiées sur l'image de la page)

| Fichier | Correction | Raison |
|---|---|---|
| ohada_au_suretes_2010/p046.txt | « ATUCIE 1024 » → « Article 182 » | numéro d'article mal lu |
| code_urbanisme/p035.txt | « .… Article L. 266. » → « Article L. 266. » | parasites devant le numéro |
| code_urbanisme/p042.txt | page refaite colonne par colonne (`--psm 4`) ; l'ancienne version est gardée dans `p042.txt.psm3_avant_correction` | les deux colonnes étaient mélangées (articles L.321 à L.327) |
| code_electoral_2023/p058.txt | « Article » remis sur la ligne de « LO.142.- » | le mot était collé au titre du chapitre |
| code_electoral_2023/p082.txt | « Article L.230.- » remis sur sa propre ligne | collé au titre « Conseillers départementaux » |
| ohada_au_droit_commercial_general_2010/p061.txt | « ARTIGLE:212- » → « ARTICLE 212- » | mot mal lu |

## Lacunes qui viennent de la source (pas de l'OCR)

- AU sûretés : l'article 179 n'apparaît pas dans le scan. Le bas de la page 44 et le haut de la page 45 sont coupés.
- Code de conduite SOMISEN : le numéro 30 est imprimé deux fois, et il n'y a pas d'article 31.
- Code de l'urbanisme : L.89 et L.90 ont le même texte dans le JO.
