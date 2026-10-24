# Storyboard

**Titre** : Acheter un logement en 2026 : où le rêve est-il encore possible ?
**Sous-titre** : cinq ans de ventes immobilières en France, de la sortie du Covid à aujourd'hui.
**Auteur** : Yanick SHAN — Majeure Data Engineering — enseignant : Mano Joseph MATHEW

## Public, question, message

- **Public** : un jeune actif qui envisage d'acheter ; plus largement, le grand public.
- **Question** : les prix de l'immobilier ont-ils baissé depuis la hausse des taux, et cette
  baisse a-t-elle rendu l'achat plus accessible partout en France ?
- **Message attendu** : la hausse des taux a d'abord **bloqué les ventes** ; les **prix** ont
  peu bougé ; avec une même mensualité, on achète **moins grand qu'en 2022**, surtout à cause
  du **crédit** ; et **l'endroit** où l'on achète compte bien plus que le moment.

## Structure de l'appli

Un menu en haut mène à 7 pages ; la barre latérale porte les filtres communs à toutes les
pages (type de bien, années comparées, régions) et, sur la page *Où ?*, la variable de la carte.
Chaque page d'analyse s'ouvre sur une phrase-titre (l'insight principal) et se termine par une
**lecture automatique des résultats** (règles fixes, sans IA).

## Arc narratif

| # | Page | Étape | Ce que voit l'utilisateur | Question à laquelle on répond | Interaction |
|---|---|---|---|---|---|
| 0 | Accueil | **Accroche** | « Avec 250 000 €, X m² dans le département le plus cher… et Y m² dans le moins cher. » | Pourquoi s'y intéresser ? | — |
| 1 | Accueil | **Contexte** | Boom de l'après-Covid (taux à 1 %, record de 2021), puis inflation et hausse des taux de la BCE (juillet 2022) ; question, public, mises en garde ; cartes vers les pages | Que s'est-il passé ? | Liens vers les pages |
| 2 | Quand ? | **Indicateurs** | 4 KPI liés aux filtres : prix médian au m², ventes, prix d'un bien, écart entre départements, avec variation vs l'année de référence | Combien coûte un m² aujourd'hui ? | Type de bien, années, régions |
| 3 | Quand ? | **Tendances** | Courbes mensuelles du prix au m² et du nombre de ventes, annotées des dates BCE | Les prix ont-ils baissé ? Le marché s'est-il bloqué ? | Survol, filtres |
| 4 | Où ? | **Carte** | Carte des départements colorée selon l'évolution du prix (ou le prix, ou l'évolution des ventes) | Où les prix bougent-ils ? | Variable de la carte (barre latérale) |
| 5 | Où ? | **Classement** | Les 12 plus fortes baisses (ou hausses), une barre par type de bien | Où est-il devenu plus intéressant d'acheter ? | Baisses / hausses |
| 6 | Où ? | **Prix × ventes** | Nuage de points en 4 quadrants (correction, repli, blocage, dynamique), taille = ventes, losange = France | Les prix baissent-ils vraiment, ou le marché ralentit-il seulement ? | Survol |
| 7 | Où ? | **Niveaux** | 10 départements les plus chers / moins chers, tableau complet | Où est-ce le plus cher ? | Tableau dépliable |
| 8 | Pouvoir d'achat | **Quoi ? (crédit)** | Simulateur : même mensualité en année de référence et en année étudiée ; budget, surface, **effet des prix vs effet des taux** ; surface par région | La baisse des prix a-t-elle compensé la hausse des taux ? | Mensualité, durée, apport, taux, frais de notaire |
| 9 | Pouvoir d'achat | **Quoi ? (budget fixe)** | Surface achetable par région pour un budget donné | Qu'achète-t-on avec une somme fixe ? | Curseur de budget |
| 10 | Zoom département | **Et chez moi ?** | Médiane et dispersion par année (appartements / maisons), histogramme des prix, communes les plus chères | Et dans mon département ? | Département à explorer |
| 11 | Qualité des données | **Confiance** | Entonnoir de nettoyage, valeurs manquantes, contrôles, limites et éthique | Peut-on croire ces chiffres ? | Tableaux dépliables |
| 12 | Conclusions | **Implications** | 3 enseignements, implications (acheteurs, décideurs), pistes | Que faut-il retenir ? Et ensuite ? | — |

## Script de la vidéo (2 à 4 minutes)

1. **(0:00–0:20) Accueil — accroche** : lire la phrase sur les 250 000 €, annoncer la question.
2. **(0:20–0:45) Contexte et données** : l'après-Covid puis la hausse des taux ; la source DVF
   (3,4 millions de ventes après nettoyage) ; le public ; montrer le menu et les filtres.
3. **(0:45–1:20) Quand ?** : les KPI, puis les deux courbes ; pointer juillet 2022 et la chute
   des ventes ; les prix bougent peu. Lire la lecture automatique (« le marché s'ajuste par les
   volumes, pas par les prix »).
4. **(1:20–2:05) Où ?** : la carte des évolutions ; les plus fortes baisses (Hauts-de-Seine,
   Paris…) ; le nuage prix × ventes : la majorité des départements est « bloquée ». Changer la
   variable de la carte dans la barre latérale ; filtrer une région.
5. **(2:05–2:45) Pouvoir d'achat** : 1 200 €/mois sur 25 ans → environ 111 m² en 2022 contre
   92 m² en 2026 ; l'effet des taux pèse bien plus que l'effet des prix. Bouger le taux pour
   montrer le seuil qui permettrait de retrouver la surface de 2022.
6. **(2:45–3:05) Zoom** : choisir Paris, puis un département rural, et comparer.
7. **(3:05–3:25) Qualité** : l'entonnoir (1 ligne sur 5 retenue, et pourquoi), les limites
   (Alsace-Moselle, neuf exclu, taux moyens, pas de causalité).
8. **(3:25–3:50) Conclusions** : les trois enseignements et les pistes.
