# Données utilisées

| Données | Producteur | Lien | Licence |
|---|---|---|---|
| Demandes de valeurs foncières (DVF), fichiers 2022 à 2026 (1er semestre) | Direction générale des Finances publiques (DGFiP) | <https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/> | Licence Ouverte / Open Licence 2.0 (Etalab) |
| Contours des départements (version simplifiée) | france-geojson (G. David), d'après IGN / OpenStreetMap | <https://github.com/gregoiredavid/france-geojson> | Licence Ouverte / ODbL |
| Taux moyens des crédits immobiliers (valeurs par défaut du simulateur) | Observatoire Crédit Logement / CSA | <https://lobservatoire.creditlogement.fr/> | Chiffres publiés, cités |

Les fichiers bruts DVF (≈ 2 Go) ne sont pas inclus : `python download_data.py` les télécharge,
puis `python prepare_data.py` reconstruit les tables nettoyées de `data/processed/`
(déjà fournies pour que l'appli démarre directement).
