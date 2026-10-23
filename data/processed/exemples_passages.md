# Passages d'exemple pour la personne 2 (RAG / génération)

Chaque bloc est une unité telle qu'elle se trouve dans `data/processed/articles.jsonl` (une ligne JSON par unité). Les champs vides sont omis ici pour la lisibilité. Chargement : `from ingest import load_units`.

Le champ `citation` est déjà prêt à afficher dans la réponse ; `source_url`, `version_texte` et les pages permettent de remonter au document de `data/raw/`.

## 1. Constitution, art. 18 (p. 10)

Article court du texte constitutionnel, avec sa hiérarchie (titre et rubrique « MARIAGE ET FAMILLE »).

```json
{
 "unit_id": "constitution::art-18",
 "doc_id": "constitution",
 "titre_document": "Constitution de la République du Sénégal (loi n° 2001-03 du 22 janvier 2001, modifiée), version consolidée",
 "type_document": "normatif",
 "source_url": "https://www.vie-publique.sn/code-senegal/constitution-senegal",
 "version_texte": "Version compilée et consolidée par le Conseil constitutionnel, à jour de la loi constitutionnelle n° 2018-14 du 11 mai 2018 (page imprimée depuis Vie-Publique.sn le 18/02/2025)",
 "date_consultation": "2026-10-23",
 "article": "18",
 "titre": "TITRE II - DES DROITS ET LIBERTES FONDAMENTAUX ET DES DEVOIRS DES",
 "rubrique": "MARIAGE ET FAMILLE",
 "page_start": 10,
 "page_end": 10,
 "citation": "Constitution, art. 18 (p. 10)",
 "text": "Le mariage forcé est une violation de la liberté individuelle. Elle est interdite et punie dans les conditions fixées par la loi.",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 2. Constitution, art. 27 (p. 13)

Article modifié : le champ `modification` cite la loi constitutionnelle de 2016 qui l'a réécrit. Attention, la version consolidée s'arrête en 2018.

```json
{
 "unit_id": "constitution::art-27",
 "doc_id": "constitution",
 "titre_document": "Constitution de la République du Sénégal (loi n° 2001-03 du 22 janvier 2001, modifiée), version consolidée",
 "type_document": "normatif",
 "source_url": "https://www.vie-publique.sn/code-senegal/constitution-senegal",
 "version_texte": "Version compilée et consolidée par le Conseil constitutionnel, à jour de la loi constitutionnelle n° 2018-14 du 11 mai 2018 (page imprimée depuis Vie-Publique.sn le 18/02/2025)",
 "date_consultation": "2026-10-23",
 "article": "27",
 "modification": "Article premier de la loi constitutionnelle n° 2016-10 du 05 avril 2016 portant révision de la Constitution (JORS, numéro spécial 6926 du 07 avril 2016, p. 505), article modifiant et remplaçant l'article 27.",
 "titre": "TITRE III - DU PRESIDENT DE LA REPUBLIQUE",
 "page_start": 13,
 "page_end": 13,
 "citation": "Constitution, art. 27 (p. 13)",
 "text": "« La durée du mandat du Président de la République est de cinq ans.\nNul ne peut exercer plus de deux mandats consécutifs ».",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 3. Code de la famille, art. 111 (p. 22)

Code de la famille : l'intitulé en gras du PDF (« Sexe et âge ») est conservé dans `intitule`.

```json
{
 "unit_id": "cf-l2-lien-matrimonial::art-111",
 "doc_id": "cf-l2-lien-matrimonial",
 "titre_document": "Code de la famille - Livre II : Du lien matrimonial (fiançailles, mariage, divorce, séparation de corps)",
 "type_document": "normatif",
 "source_url": "https://justice.sec.gouv.sn/wp-content/uploads/2021/01/CODE-DE-LA-FAMILLE.pdf",
 "version_texte": "Loi n° 72-61 du 12 juin 1972, version consolidée diffusée par le Ministère (PDF créé le 20/03/2003)",
 "date_consultation": "2026-10-23",
 "article": "111",
 "intitule": "Sexe et âge",
 "livre": "LIVRE II - DU LIEN MATRIMONIAL",
 "chapitre": "CHAPITRE I - DU MARIAGE",
 "section": "SECTION II - CONDITIONS DE FOND DU MARIAGE",
 "paragraphe": "Paragraphe II - Conditions particulières à chacun des époux",
 "page_start": 22,
 "page_end": 22,
 "citation": "Code de la famille, art. 111 (p. 22)",
 "text": "Le mariage ne peut être contracté qu'entre un homme âgé de plus de 18 ans et une femme âgée de plus de 16 ans sauf dispense d'âge accordée pour motif grave par le Président du tribunal régional après enquête.",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 4. COCC, art. 437 (p. 53)

COCC : l'intitulé est déduit par heuristique, parce que l'export texte n'a pas de mise en forme, et les pages sont des blocs de l'export, pas de vraies pages.

```json
{
 "unit_id": "cocc::art-437",
 "doc_id": "cocc",
 "titre_document": "Code des obligations civiles et commerciales (COCC) - export texte",
 "type_document": "normatif",
 "source_url": "https://justice.sec.gouv.sn/publications/textes/droit-civil-et-procedure-civile/obligations-civiles-et-commerciales/",
 "version_texte": "« Nouveau Code des obligations civiles et commerciales » (édition non datée)",
 "date_consultation": "2026-10-23",
 "article": "437",
 "intitule": "Concernant la livraison",
 "partie": "DEUXIEME PARTIE DES CONTRATS SPECIAUX (Loi N° 66 - 70 du 13 Juillet",
 "livre": "LIVRE II - LES CONTRATS UNIQUEMENT GENERATEURS D'OBLIGATIONS DE FAIRE",
 "chapitre": "CHAPITRE I - LE CONTRAT D'ENTREPRISE",
 "section": "SECTION I - REGLES COMMUNES A TOUS LES CONTRATS D'ENTREPRISE",
 "paragraphe": "Paragraphe I",
 "page_start": 53,
 "page_end": 53,
 "citation": "COCC, art. 437 (p. 53)",
 "text": "Obligé d'exécuter l'ouvrage dans le délai fixé par la convention ou les usages, l'entrepreneur doit, après achèvement, livrer la chose au maître de l'œuvre. La délivrance vaut transfert de la propriété pour la matière fournie par l'entrepreneur qui supporte les risques de perte de la chose durant l'exécution du contrat. La délivrance opère restitution de la matière fournie par le maître de l'œuvre. L'entrepreneur est responsable de la perte de la matière durant l'exécution du contrat. S'il y a cas fortuit, le maître de l'œuvre est délié de ses obligations.",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 5. COCC, art. 202 AU/DCG (p. 39)

Article de l'Acte uniforme OHADA reproduit dans le COCC, avec le suffixe AU/DCG et la mention dans `modification`.

```json
{
 "unit_id": "cocc::art-202AU/DCG",
 "doc_id": "cocc",
 "titre_document": "Code des obligations civiles et commerciales (COCC) - export texte",
 "type_document": "normatif",
 "source_url": "https://justice.sec.gouv.sn/publications/textes/droit-civil-et-procedure-civile/obligations-civiles-et-commerciales/",
 "version_texte": "« Nouveau Code des obligations civiles et commerciales » (édition non datée)",
 "date_consultation": "2026-10-23",
 "article": "202 AU/DCG",
 "modification": "article de l'Acte uniforme OHADA AU/DCG reproduit",
 "partie": "DEUXIEME PARTIE DES CONTRATS SPECIAUX (Loi N° 66 - 70 du 13 Juillet",
 "livre": "LIVRE I - LES CONTRATS TRANSLATIFS DE PROPRIETE",
 "titre": "TITRE I - CHAMP D'APPLICATION ET DISPOSITIONS GENERALES CHAMP D'APPLICATION",
 "page_start": 39,
 "page_end": 39,
 "citation": "COCC, art. 202 AU/DCG (p. 39)",
 "text": "Les dispositions du présent Livre s'appliquent aux contrats de vente de marchandises entre commerçants, personnes physiques ou personnes morales.",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 6. Code électoral, art. L.53 (p. 30)

Code électoral, partie législative (préfixe L.). Texte obtenu par OCR, donc `extraction` = « ocr à vérifier ».

```json
{
 "unit_id": "code-electoral-legislatif::art-L.53",
 "doc_id": "code-electoral-legislatif",
 "titre_document": "Code électoral - Partie législative (loi n° 2021-35 du 23 juillet 2021, modifiée)",
 "type_document": "normatif",
 "source_url": "fourni par l'équipe (code-electoral-senegal-2023.pdf)",
 "version_texte": "Édition 2023 : loi n° 2021-35 du 23/07/2021 modifiée par les lois n° 2022-15 du 03/05/2022 et n° 2023-16 du 18/08/2023",
 "date_consultation": "2026-10-23",
 "article": "L.53",
 "partie": "PARTIE LEGISLATIVE",
 "titre": "TITRE I - DISPOSITIONS COMMUNES À L'ELECTION DU PRESIDENT DE LA REPUBLIQUE, AUX ELECTIONS DES DEPUTES, DES HAUTS CONSEILLERS, DES CONSEILLERS DEPARTEMENTAUX ET MUNICIPAUX",
 "chapitre": "Chapitre II - Les listes électorales",
 "section": "Section 4 - Cartes d'électeur",
 "page_start": 30,
 "page_end": 30,
 "citation": "Code électoral, art. L.53 (p. 30)",
 "text": "La carte d'électeur est couplée à la carte d'identité biométrique CEDEAO. Celle-ci fait office de carte d'électeur. Les données électorales sont mentionnées au verso. Elles comprennent le numéro d'électeur, la région, le département, l'arrondissement, la commune, le lieu de vote, le bureau de vote et le numéro d'identification nationale.\nL'Administration est chargée de l'impression et de l'établissement des cartes d'électeur aux frais de l'Etat.\nLa carte d'électeur a une durée de validité de dix (10) ans.\nEn cas de demande de duplicata pour cause d'altération ou de perte de la carte d'identité biométrique CEDEAO faisant office de carte d'électeur, devant un centre d'instruction ou une commission administrative, celle-ci est rééditée à l'identique avec le même délai de validité et porte la mention \"duplicata”.\nCependant, une demande de modification des données électorales ne peut se faire que devant une commission administrative et pendant la période de révision des listes électorales.\nSi l'électeur fait la déclaration de perte de sa carte d'électeur auprès d'une commission administrative, celle-ci établit une attestation sur la base de laquelle il peut demander la délivrance d'un duplicata.\nLe renouvellement de la carte d'électeur expirée est effectué l'année qui suit l'expiration, pendant la révision ordinaire.\nEn cas de révision exceptionnelle précédant une élection générale, le renouvellement est fait auprès des commissions administratives crées à cet effet.\nToutefois, la carte d'électeur qui expire entre une révision des listes électorales et une élection peut être utilisée à titre exceptionnel.\nLors du renouvellement, les données électorales peuvent faire l'objet de modifications.",
 "extraction": "ocr à vérifier",
 "statut_version": "texte tel que publié par la source"
}
```

## 7. Code de l'urbanisme, art. L.89 (p. 16)

Anomalie de la source : L.89 et L.90 ont un texte identique dans le JO (vérifié sur l'image). Le texte n'a pas été dédoublonné.

```json
{
 "unit_id": "code-urbanisme::art-L.89",
 "doc_id": "code-urbanisme",
 "titre_document": "Loi n° 2023-20 du 29 décembre 2023 portant Code de l'Urbanisme",
 "type_document": "normatif",
 "source_url": "fourni par l'équipe (code-urbanisme-senegal.pdf)",
 "version_texte": "Loi n° 2023-20 du 29/12/2023, JO n° 7694 du 17/01/2024 ; abroge et remplace la loi n° 2008-43 du 20/08/2008",
 "date_consultation": "2026-10-23",
 "article": "L.89",
 "livre": "LIVRE II - LES SERVITUDES D'UTILITE PUBLIQUE",
 "titre": "TITRE I - SERVITUDES RELATIVES À LA CONSERVATION DU PATRIMOINE NATUREL OU CULTUREL",
 "chapitre": "Chapitre V - Zones agro-sylvo-pastorales",
 "page_start": 16,
 "page_end": 16,
 "citation": "Code de l'urbanisme, art. L.89 (p. 16)",
 "text": "Dans les zones de culture, il est créé ou restauré des zones de pâturages reliées par des couloirs de passage et d'accès aux points d'abreuvement. Ces couloirs sont d'une largeur d'au moins 100 mètres bordés de haies de protection. Le Ministre chargé de l'Equipement, le Ministre chargé du Développement rural ainsi que les communautés rurales concernées (agriculteurs et éleveurs) sont chargés de l'exécution et de la mise en place des aménagements.",
 "extraction": "ocr à vérifier",
 "statut_version": "texte tel que publié par la source"
}
```

## 8. AU sûretés (OHADA), art. 4 (p. 3-4)

Article qui s'étend sur deux pages (`page_start` 3, `page_end` 4).

```json
{
 "unit_id": "ohada-au-suretes::art-4",
 "doc_id": "ohada-au-suretes",
 "titre_document": "Acte uniforme OHADA portant organisation des sûretés (révisé)",
 "type_document": "normatif",
 "source_url": "fourni par l'équipe ; texte officiel sur https://www.ohada.org/actes-uniformes/",
 "version_texte": "Adopté le 15/12/2010 à Lomé, JO OHADA n° 22 du 15/02/2011",
 "date_consultation": "2026-10-23",
 "article": "4",
 "titre": "TITRE PRELIMINAIRE - DEFINITIONS ET DOMAINE D'APPLICATION DES SURETES - AGENT DES SURETES",
 "chapitre": "CHAPITRE 1 - DEFINITIONS ET DOMAINE D'APPLICATION DES SURETES",
 "page_start": 3,
 "page_end": 4,
 "citation": "AU sûretés (OHADA), art. 4 (p. 3-4)",
 "text": "Les sûretés personnelles, au sens du présent Acte uniforme, consistent en l'engagement d'une personne de répondre de l'obligation du débiteur principal en cas de défaillance de celui-ci ou à première demande du bénéficiaire de la garantie.\nSauf disposition contraire du présent Acte uniforme, les seules sûretés réelles valablement constituées sont celles qui sont régies par cet Acte. Elles consistent soit dans le droit du créancier de se faire payer par préférence sur le prix de réalisation d'un bien affecté à la garantie de l'obligation de son débiteur, soit dans le droit de recouvrer la libre disposition d'un bien dont il est propriétaire à titre de garantie de cette obligation. |\nLes süretés réelles peuvent être constituées par le débiteur lui-même ou un tiers en garantie de l'obligation sous réserve des dispositions particulières du présent Acte uniforme.\nLes süûretés propres au droit fluvial, maritime et aérien, les sûretés légales autres que celles régies par le présent Acte uniforme, ainsi que les sûretés garantissant l'exécution de contrats conclus exclusivement entre établissements de financement, peuvent faire l'objet de législations particulières.",
 "extraction": "ocr à vérifier",
 "statut_version": "texte tel que publié par la source"
}
```

## 9. Règlement intérieur de l'Assemblée nationale, art. 1 (p. 6)

Texte récent (loi organique 2025-11) en texte natif.

```json
{
 "unit_id": "an-reglement-interieur::art-1",
 "doc_id": "an-reglement-interieur",
 "titre_document": "Loi organique n° 2025-11 du 18 août 2025 portant Règlement intérieur de l'Assemblée nationale",
 "type_document": "normatif",
 "source_url": "https://assemblee.sn",
 "version_texte": "Loi organique n° 2025-11 du 18/08/2025, édition octobre 2025",
 "date_consultation": "2026-10-23",
 "article": "1",
 "titre": "TITRE I - ORGANISATION ET FONCTIONNEMENT DE L'ASSEMBLEE NATIONALE",
 "chapitre": "CHAPITRE I - DISPOSITIONS GENERALES",
 "page_start": 6,
 "page_end": 6,
 "citation": "Règlement intérieur de l'Assemblée nationale, art. 1 (p. 6)",
 "text": "Le présent Règlement intérieur régit l'organisation et le fonctionnement de l'Assemblée nationale, conformément aux dispositions de la Constitution de la République du Sénégal.",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 10. Code de conduite SOMISEN, art. 1 (p. 4)

Règlement interne d'entreprise (`type_document` = « règlement interne »), à ne pas présenter comme une norme publique.

```json
{
 "unit_id": "somisen-code-conduite::art-1",
 "doc_id": "somisen-code-conduite",
 "titre_document": "Code de conduite et d'éthique de la SOMISEN SA (Société des Mines du Sénégal)",
 "type_document": "règlement interne",
 "source_url": "fourni par l'équipe (code-de-conduite-et-dethique-somisen-2025.pdf)",
 "version_texte": "Code adopté en 2025, lettre de transmission du 08/04/2025",
 "date_consultation": "2026-10-23",
 "article": "1",
 "intitule": "AU SENS DU PRESENT CODE, ON ENTEND PAR :",
 "titre": "TITRE I - VALEURS FONDAMENTALES ET CULTURE D'ENTREPRISE",
 "page_start": 4,
 "page_end": 4,
 "citation": "Code de conduite SOMISEN, art. 1 (p. 4)",
 "text": "1. Conduite : l'ensemble des directives qui influencent les actions des employés :\n2. Ethique : L'éthique est l'ensemble des principes moraux qui sont à la base de la conduite de l'organisation ;\n3. Code de conduite et d'éthique : d'écrit, en termes concrets et précis, les règles de conduite minimales auxquelles tous les employés sont censés obéir :\n4. Employé : toute personne qui est employée par la SOMISEN au sens du Code du travail ;\n5. Famille immédiate : se rapporte aux époux et enfants de l'employé y compris les beaux fils belles filles, les beaux-parents ainsi que les enfants adoptés conformément au Code de la Famille ;\n6. Collaborateur : toute tierce personne externe à l'entreprise qui concours à la réalisation des objectifs de la SOMISEN.",
 "extraction": "ocr à vérifier",
 "statut_version": "texte tel que publié par la source"
}
```

## 11. Guide de l'adoption internationale, p. 12

Document explicatif sans articles : une unité par page, avec une citation « p. N ».

```json
{
 "unit_id": "guide-adoption-internationale::p12",
 "doc_id": "guide-adoption-internationale",
 "titre_document": "Guide de l'adoption internationale au Sénégal",
 "type_document": "explicatif",
 "source_url": "https://justice.sec.gouv.sn/wp-content/uploads/2022/04/GUIDE-DE-LADOPTION-INTERNATIONALE.pdf",
 "version_texte": "Édition 2019 (PDF du 27/11/2020)",
 "date_consultation": "2026-10-23",
 "page_start": 12,
 "page_end": 12,
 "citation": "Guide de l'adoption internationale, p. 12",
 "text": "Au besoin, l'ACCAI peut demander tout autre document jugé nécessaire.\n\n3.2.5. Agrément des Futurs Parents Adoptants (FPA)\n\nLes candidats à l'adoption internationale résidant au Sénégal adressent, au Garde des Sceaux, Ministre de la justice, une demande d'agrément accompagnée des pièces suivantes :\n\n- une copie littérale de l'acte de naissance ;\n- une copie littérale de l'acte de mariage, le cas échéant;\n- une copie d'une pièce d'identification ;\n- un bulletin n° 3 du casier judiciaire de moins de trois mois ;\n- un certificat de nationalité ;\n- un certificat médical datant de moins de trois mois ;\n- un livret de famille ;\n- un justificatif de résidence ;\n- des justificatifs de revenus ou de ressources.\n\nDès réception de la demande, l'Autorité centrale procède à l'instruction. Elle peut à cet effet procéder ou faire procéder à une enquête de moralité, à une enquête sociale et à une expertise médicale, psychologique notamment. Elle doit surtout s'assurer que les futurs parents adoptifs sont qualifiés et aptes à adopter et qu'ils ont été entourés de conseils nécessaires.\n\nL'enquête terminée, l'Autorité émet un avis. Si l'avis est favorable, elle soumet le dossier au Ministre en charge de la Justice qui, par arrêté, procède à l'agrément. Si l'avis est défavorable, celui-ci prend une décision motivant le rejet. Cette décision est notifiée au pétitionnaire qui peut soit demander un nouvel examen de sa demande par l'Autorité ou saisir la juridiction administrative d'un recours dans les conditions légales.\n\nL'agrément est valable pour une durée de cinq (05) ans. A l'expiration du délai il est renouvelé dans les mêmes conditions.\n\nEn cas de comportements contraires à la loi ou aux bonnes mœurs, l'agrément est retiré par arrêté du Ministre en charge de la Justice après avis de l'Autorité centrale.\n\nLa décision de retrait ou de refus de renouvellement est susceptible de recours administratif gracieux ou juridictionnel.\n\nL'agrément devient caduc lorsque l'une ou plusieurs conditions l'ayant motivés disparaissent (divorce, décès, naissance d'un enfant biologique, séparation de corps...)\n\nLe délai de traitement de la demande d'agrément ne saurait excéder six (06) mois.\n\n3.2 les Autorités judiciaires compétentes",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## 12. Stratégie nationale de protection de l'enfant, p. 12

Politique publique (SNPE) : également une unité par page.

```json
{
 "unit_id": "snpe::p12",
 "doc_id": "snpe",
 "titre_document": "Stratégie nationale de protection de l'enfant (SNPE)",
 "type_document": "politique publique",
 "source_url": "fourni par l'équipe (SNPE21845.pdf)",
 "version_texte": "Stratégie de décembre 2013, édition juin 2016",
 "date_consultation": "2026-10-23",
 "page_start": 12,
 "page_end": 12,
 "citation": "Stratégie nationale de protection de l'enfant, p. 12",
 "text": "CHAPITRE 1\n\nPOURQUOI UNE STRATEGIE NATIONALE DE PROTECTION DE\n\nL'ENFANT ?\n\n1.1. Contexte\n\nLa population du Sénégal est estimée en 2011 à 12.855.153 habitants dont plus de 55% ont moins de 18 ans.\nLa structure démographique du Sénégal est donc très fortement ponctuée par la jeunesse de sa population.\nLe taux de natalité est de 39,1‰ pour un accroissement moyen annuel de la population de 2,5% sur la base d'un indice de fécondité de 5,3 enfants par femme avec plus de 65% de la population ayant moins de 35 ans donc en plein âge de procréer. Cette courbe démographique a toutes les chances de se maintenir dans les 35 prochaines années d'autant que plus de 50% des Sénégalais sont dans la fourchette des 1-16 ans.\n\nCette situation renseigne sur l'importance de l'action de protection et de promotion de l'enfance et de la jeunesse. Sur le terrain, les données de l'Enquête Démographique et de Santé (EDS II) révèlent que 19% des enfants de moins de 18 ans seraient en situation de travail au Sénégal dont plus de 38% dans des travaux domestiques (petites filles essentiellement) et 11% engagés dans des activités économiques ou génératrices de revenus.\n\nPar ailleurs, s'agissant de l'enregistrement des enfants à la naissance, le taux reste encore faible. Estimé à 75% pour l'ensemble des enfants de moins de cinq ans, le taux d'enregistrement est légèrement plus faible en milieu rural qu'en milieu urbain (66% contre 89% pour le milieu urbain selon l'EDS MICS de 2010-2011). Aussi, selon le même rapport (EDS-MICS 2010-2011), la pratique de l'excision reste encore répandue au Sénégal.\nElle concerne 26% des femmes âgées de 15 à 49 ans.\n\nA ces pratiques, s'ajoutent d'autres situations telles que les violences domestiques, les sévices infligés aux enfants dans le milieu familial, et les violences sexuelles dans tous les milieux qui paraissent avoir une ampleur notable mais pas suffisamment connue. Quelques données permettent toutefois de considérer ce phénomène inquiétant.\n\nEn ce qui concerne les violences et sévices sexuels infligés aux enfants, 26,5% des femmes rapportent avoir été victimes d'attouchements sexuels avant l'âge de 13 ans, les cas d'inceste occupant une place importante.\nD'une manière générale, les informations chiffrées restent rares en ce qui concerne les formes de violence verbale, morale ou psychologique, les coups et blessures, les violences sexuelles.\nPour tous les enfants, où qu'ils vivent, le soutien et la sécurité doivent être la norme. Le Gouvernement du Sénégal s'est engagé à les protéger contre l'exploitation ou la violence et à prendre, le cas échéant, des mesures efficaces pour combattre ces pratiques. Alors même que le pays fait état de progrès considérables en matière de survie des enfants et d'éducation, la protection complète des enfants reste néanmoins difficile à assurer.\n\nDurant ces dix dernières années, la protection de l'enfant a acquis une place plus importante parmi les objectifs de la Communauté Internationale. Il est largement reconnu que les enfants sont souvent peu protégés et que les problèmes dans ce domaine, à la fois dans les pays développés et en développement, dépassent les frontières nationales. Il est aussi admis que l'amélioration de la protection des enfants et la réalisation des Objectifs du Millénaire pour le Développement vont de pair. Comme la présente Stratégie contribue à l'illustrer, les occasions ne manquent pas de mettre davantage en relief la protection de l'enfant, que ce soit dans les\n\n12 | Stratégie Nationale de Protection de l'Enfant",
 "extraction": "texte natif",
 "statut_version": "texte tel que publié par la source"
}
```

## Questions de test suggérées (pour la personne 3)

| Question | Unité attendue |
|---|---|
| À partir de quel âge peut-on se marier au Sénégal ? | Code de la famille, art. 111 |
| Le mariage forcé est-il interdit par la Constitution ? | Constitution, art. 18 |
| Combien de temps dure le mandat présidentiel ? | Constitution, art. 27 (vérifier les révisions après 2018) |
| La carte d'identité CEDEAO sert-elle de carte d'électeur ? | Code électoral, art. L.53 |
| Qu'est-ce qu'une sûreté personnelle ? | AU sûretés (OHADA), art. 4 |
| Quand l'entrepreneur doit-il livrer l'ouvrage ? | COCC, art. 437 |
| Qui peut demander l'agrément pour une adoption internationale ? | Guide de l'adoption internationale, p. 12 |
| Quel est l'objet du Code de la construction ? | Code de la construction, art. L.1 |
