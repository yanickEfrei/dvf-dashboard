# Acheter un logement en 2026 : où le rêve est-il encore possible ?

Dashboard de *data storytelling* réalisé avec Streamlit sur les **Demandes de valeurs
foncières (DVF)** : toutes les ventes immobilières enregistrées en France de 2022 à juin 2026.

- **Auteur** : Yanick SHAN — n° étudiant 20241145 — groupe DE2 (Majeure Data Engineering)
- **Enseignant** : Mano Joseph MATHEW
- **Cours** : Data Visualization — EFREI Paris — #EFREIDataStories2026
- **Appli en ligne** : [URL Streamlit Community Cloud]
- **Vidéo de démonstration** : [lien]

## La question

> **Les prix de l'immobilier ont-ils baissé depuis la hausse des taux, et cette baisse
> a-t-elle rendu l'achat plus accessible partout en France ?**

| Sous-question | Page de l'appli |
|---|---|
| **Quand ?** Comment ont évolué le prix au m² et le nombre de ventes depuis 2022 ? | *Quand ?* : indicateurs clés + courbes mensuelles |
| **Où ?** Quels départements sont les plus chers, lesquels ont le plus baissé ? | *Où ?* : carte des variations, plus fortes baisses, nuage prix × ventes, classements |
| **Quoi ?** Que peut-on acheter avec une mensualité donnée, taux compris ? Appartements et maisons ont-ils suivi la même trajectoire ? | *Pouvoir d'achat* : simulateur de crédit (effet prix / effet taux) et à budget fixe ; *Zoom département* |

L'appli est découpée en pages (menu de navigation en haut) : Accueil, Quand ?, Où ?,
Pouvoir d'achat, Zoom département, Qualité des données, Conclusions. Les filtres de la
barre latérale (type de bien, années, régions) s'appliquent à toutes les pages.

**Public visé** : un jeune actif qui se demande s'il peut acheter, et où.
Le récit complet est décrit dans [`storyboard.md`](storyboard.md).

## Données

| | |
|---|---|
| Jeu de données | [Demandes de valeurs foncières](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) |
| Producteur | Direction générale des Finances publiques (DGFiP) |
| Portail | data.gouv.fr |
| Licence | Licence Ouverte / Open Licence 2.0 (Etalab) |
| Fichiers utilisés | `ValeursFoncieres-2022.txt` à `ValeursFoncieres-2025.txt`, `ValeursFoncieres-2026-S1.txt` |
| Taux de crédit | Observatoire Crédit Logement / CSA (moyennes annuelles arrondies, modifiables dans l'appli) |
| Contexte Covid (intro) | Notaires de France, notes de conjoncture immobilière 2021-2022 |
| Contours des départements | [france-geojson](https://github.com/gregoiredavid/france-geojson) (simplifié) |

Les fichiers bruts (~2 Go au total) ne sont **pas** inclus : `download_data.py` les
télécharge. Les tables nettoyées (`data/processed/`, ~25 Mo) sont versionnées pour que
l'appli démarre directement.

### Nettoyage (`prepare_data.py`)

Dans le fichier brut, **une ligne = un bien dans une vente** (un appartement vendu avec
une cave et un parking occupe 3 lignes avec le même prix). Étapes :

1. Suppression des **doublons exacts** (toutes colonnes).
2. Conservation des **ventes classiques** uniquement (exclusion des échanges,
   adjudications, ventes en l'état futur d'achèvement et terrains à bâtir).
3. **Reconstitution des ventes** (aucun identifiant fourni) avec la clé
   date + prix + département + commune + voie + n° de voie + n° de disposition.
4. Conservation des ventes d'**un seul logement** (maison ou appartement ; caves et
   parkings tolérés ; pas de local professionnel).
5. Prix et surface présents, **surface ≥ 9 m²**.
6. Retrait des **prix aberrants** : moins de 300 €/m² ou plus de 30 000 €/m².
7. Retrait des dates invalides.

Chaque étape est comptée dans `data/processed/quality.json` et affichée dans l'appli
(section « Qualité des données »), avec les taux de valeurs manquantes des fichiers bruts
et des contrôles automatiques sur la table finale.

Indicateur principal : **prix médian au m²** (plus robuste que la moyenne aux ventes de
luxe). Une médiane n'est affichée que si elle repose sur au moins 30 ventes (département)
ou 20 ventes (commune). L'année 2026 étant partielle, elle est toujours comparée aux
**mêmes mois** des autres années.

### Limites

- DVF ne couvre ni le Bas-Rhin, ni le Haut-Rhin, ni la Moselle, ni Mayotte.
- Prix **déclarés**, sans l'état du bien, l'étage ou les travaux.
- Le neuf et les ventes en bloc sont exclus.
- Le simulateur de crédit utilise des **taux moyens nationaux arrondis** (hors assurance) et
  ne tient pas compte des revenus : c'est un ordre de grandeur, pas une offre de prêt.
- Les dates de la BCE sur les courbes sont un contexte, pas une preuve de causalité.
- Aucune vente individuelle ni adresse n'est affichée (conditions de réutilisation DVF).

## Lancer le projet

Python 3.12 ou plus récent.

```bash
pip install -r requirements.txt
python download_data.py        # télécharge les fichiers bruts (≈ 2 Go) et les contours
python prepare_data.py         # nettoie et agrège -> data/processed/  (≈ 5 à 10 min)
streamlit run app.py
```

Si `data/processed/` est déjà présent (cas du dépôt Git), seule la dernière commande
est nécessaire. Le traitement est **déterministe** : aucun échantillonnage aléatoire,
mêmes fichiers d'entrée → mêmes résultats.

## Structure

```
app.py                  # barre latérale (filtres communs) + navigation entre les pages
sections/
  intro.py              # accroche, contexte, question, public, mises en garde
  overview.py           # indicateurs clés (liés aux filtres) + tendances mensuelles
  deep_dives.py         # page Où ? (carte, baisses, prix × ventes, classements) + zoom département
  budget.py             # page Pouvoir d'achat : simulateur de crédit et à budget fixe
  quality.py            # entonnoir de nettoyage, manquants, contrôles, limites
  conclusions.py        # enseignements, implications, pistes
utils/
  io.py                 # chargement des données (mis en cache), source et licence
  prep.py               # référentiels géographiques, filtres, calculs de médianes
  viz.py                # fonctions graphiques au style commun
  i18n.py               # traduction FR / EN
  insights.py           # lecture automatique des résultats (règles, sans IA)
  ai.py                 # interprétation par l'IA (Claude), désactivée sans clé API
data/
  departements.geojson  # contours des départements
assets/logo_efrei.svg   # logo de l'école
  processed/            # tables nettoyées (générées par prepare_data.py)
download_data.py        # téléchargement des données brutes (avec cache)
prepare_data.py         # nettoyage + agrégation
storyboard.md           # plan du récit
.streamlit/config.toml  # thème
```

**Performance** : la table des ventes (~3,4 M lignes, types compacts `uint16`/`category`)
est chargée une seule fois (`st.cache_resource`) ; chaque calcul dépendant des filtres est
mis en cache (`st.cache_data`).

**Bilingue** : un sélecteur FR / EN en haut de la barre latérale traduit toute l'appli
(textes, graphiques, formats de nombres) sans perdre les filtres choisis (`utils/i18n.py`).

**Accessibilité** : palette testée pour le daltonisme (bleu/orange), chaque graphique est
suivi d'une description textuelle, d'axes et d'unités explicites, et d'un tableau de
données consultable.

## Lecture automatique des résultats

Les pages *Quand ?*, *Où ?*, *Pouvoir d'achat* et *Zoom département* se terminent par un
panneau « Lecture automatique des résultats » (`utils/insights.py`). Il ne s'agit **pas d'une
IA** : des règles fixes transforment les chiffres de la page en phrases (diagnostic prix /
volumes, lien entre niveau de prix et évolution, effet des taux contre effet des prix, taux
qu'il faudrait pour retrouver la surface de l'année de référence, etc.). Chaque phrase est
donc vérifiable et suit les filtres choisis ; les seuils (« légère » baisse sous 3 %,
« forte » au-delà de 8 %) sont des conventions, rappelées dans un avertissement.

> **Pourquoi pas une vraie IA ?** Une interprétation par un modèle de langage (Claude,
> d'Anthropic) a été codée et testée avec une IA simulée (`utils/ai.py`), mais elle n'est
> **pas activée**, faute de budget : l'API est payante à l'usage. Le panneau n'apparaît que
> si une clé est configurée dans `.streamlit/secrets.toml` (fichier ignoré par Git) :
>
> ```toml
> ANTHROPIC_API_KEY = "sk-ant-..."
> ```

## Déploiement (Streamlit Community Cloud)

1. Pousser le dépôt sur GitHub **avec** `data/processed/` et `data/departements.geojson`.
2. Sur [share.streamlit.io](https://share.streamlit.io), *New app* → choisir le dépôt,
   la branche et `app.py`.
