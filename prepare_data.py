"""
Préparation des données DVF (Demandes de valeurs foncières) pour le dashboard.

Lit tous les fichiers bruts data/raw/ValeursFoncieres-*.txt, les nettoie,
puis écrit dans data/processed/ :
  - ventes.parquet            une ligne = une vente d'un logement (colonnes compactes)
  - agg_commune_annee.parquet prix au m² par commune, année et type de bien
  - quality.json              rapport qualité (valeurs manquantes, lignes retirées à chaque étape)

Usage :  python prepare_data.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")

# Seuils de nettoyage (documentés dans le README et dans l'appli)
SURFACE_MIN = 9          # m², surface minimale d'un logement décent (décret 2002-120)
PRIX_M2_MIN = 300        # €/m², en dessous : vente symbolique ou erreur
PRIX_M2_MAX = 30_000     # €/m², au-dessus : valeur aberrante (erreur de surface)

COLS = [
    "No disposition", "Date mutation", "Nature mutation", "Valeur fonciere",
    "No voie", "Voie", "Code postal", "Commune", "Code departement",
    "Code commune", "Type local", "Surface reelle bati",
    "Nombre pieces principales",
]
# Colonnes dont on mesure le taux de valeurs manquantes dans le fichier brut
NA_COLS = ["Date mutation", "Valeur fonciere", "Code departement", "Code commune",
           "Type local", "Surface reelle bati", "Nombre pieces principales"]

# Une vente n'a pas d'identifiant dans le fichier brut (colonne vide à 100 %) :
# on la reconstitue avec ces colonnes (méthode classique sur DVF).
MUTATION_KEY = ["Date mutation", "Valeur fonciere", "Code departement",
                "Code commune", "Voie", "No voie", "No disposition"]


def to_float(s: pd.Series) -> pd.Series:
    """Convertit '130000,00' en 130000.0."""
    return pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")


def clean_file(path: Path) -> tuple[pd.DataFrame, dict]:
    q = {"fichier": path.name}
    df = pd.read_csv(path, sep="|", dtype=str, low_memory=False)
    q["lignes_brutes"] = len(df)
    q["colonnes_brutes"] = df.shape[1]
    q["manquants_pct"] = {c: round(float(df[c].isna().mean() * 100), 1) for c in NA_COLS}
    q["colonnes_vides_90pct"] = int((df.isna().mean() > 0.9).sum())

    # 1. Doublons exacts sur TOUTES les colonnes (avant de réduire les colonnes,
    #    sinon deux caves distinctes d'une même vente seraient fusionnées)
    df = df.drop_duplicates()[COLS]
    q["apres_doublons"] = len(df)

    # 2. Ventes classiques uniquement (ni échange, ni adjudication, ni VEFA, ni terrain)
    df = df[df["Nature mutation"] == "Vente"]
    q["apres_filtre_vente"] = len(df)

    df["valeur"] = to_float(df["Valeur fonciere"])
    df["surface"] = to_float(df["Surface reelle bati"])
    df["is_logement"] = df["Type local"].isin(["Maison", "Appartement"])
    df["is_local_pro"] = df["Type local"].str.startswith("Local", na=False)

    # 3. Une ligne = un bien. On regroupe par vente.
    ventes = (df.groupby(MUTATION_KEY, dropna=False, sort=False)
                .agg(n_logements=("is_logement", "sum"),
                     n_locaux_pro=("is_local_pro", "sum"))
                .reset_index())
    q["ventes_distinctes"] = len(ventes)

    # 4. Ventes d'UN seul logement (cave/parking tolérés), sinon le prix
    #    couvre plusieurs biens et le prix au m² n'a pas de sens.
    ventes = ventes[(ventes["n_logements"] == 1) & (ventes["n_locaux_pro"] == 0)]
    log = df[df["is_logement"]].merge(ventes[MUTATION_KEY], on=MUTATION_KEY)
    q["ventes_un_logement"] = len(log)

    # 5. Prix et surface présents, surface plausible
    log = log.dropna(subset=["valeur", "surface"])
    log = log[log["surface"] >= SURFACE_MIN]
    q["apres_valeur_surface_valides"] = len(log)

    # 6. Prix au m² aberrants
    log["prix_m2"] = log["valeur"] / log["surface"]
    ok = log["prix_m2"].between(PRIX_M2_MIN, PRIX_M2_MAX)
    q["valeurs_aberrantes_retirees"] = int((~ok).sum())
    log = log[ok]

    # 7. Dates valides
    log["date"] = pd.to_datetime(log["Date mutation"], format="%d/%m/%Y", errors="coerce")
    q["dates_invalides_retirees"] = int(log["date"].isna().sum())
    log = log.dropna(subset=["date"])
    q["lignes_finales"] = len(log)

    dep = log["Code departement"].str.zfill(2)
    commune = log["Code commune"].str.zfill(3)
    # Code INSEE : 2 chiffres du département + 3 de la commune ; DOM : 97 + 3 chiffres
    code_insee = np.where(dep.str.len() == 3, "97" + commune, dep + commune)
    out = pd.DataFrame({
        "date": log["date"],
        "dep": dep,
        "code_insee": code_insee,
        "commune": log["Commune"],
        "type": log["Type local"],
        "surface": log["surface"],
        "valeur": log["valeur"],
        "prix_m2": log["prix_m2"],
    })
    return out, q


def main():
    files = sorted(RAW_DIR.glob("ValeursFoncieres-*.txt"))
    if not files:
        raise SystemExit(f"Aucun fichier ValeursFoncieres-*.txt dans {RAW_DIR}/")

    parts, quality = [], []
    for f in files:
        print(f"Traitement de {f.name}...")
        d, q = clean_file(f)
        parts.append(d)
        quality.append(q)
        print(f"  {q['lignes_brutes']:,} lignes brutes -> {q['lignes_finales']:,} ventes retenues")

    df = pd.concat(parts, ignore_index=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Table principale, compacte : ~3,4 M lignes mais quelques dizaines de Mo
    ventes = pd.DataFrame({
        "mois": df["date"].dt.to_period("M").dt.to_timestamp(),
        "dep": df["dep"].astype("category"),
        "type": df["type"].astype("category"),
        "prix_m2": df["prix_m2"].round().astype("uint16"),
        "surface": df["surface"].clip(upper=65_000).round().astype("uint16"),
        "valeur": df["valeur"].round().astype("uint32"),
    })
    ventes.to_parquet(OUT_DIR / "ventes.parquet", index=False, compression="zstd")

    # Agrégat par commune (pour le zoom sur un département)
    df["annee"] = df["date"].dt.year
    g = df.groupby(["annee", "dep", "code_insee", "commune", "type"], observed=True)["prix_m2"]
    communes = g.agg(n_ventes="size", prix_m2_median="median")
    quart = g.quantile([0.25, 0.75]).unstack()
    communes["prix_m2_q1"], communes["prix_m2_q3"] = quart[0.25], quart[0.75]
    communes.reset_index().to_parquet(OUT_DIR / "agg_commune_annee.parquet", index=False)

    report = {
        "seuils": {"surface_min_m2": SURFACE_MIN, "prix_m2_min": PRIX_M2_MIN,
                   "prix_m2_max": PRIX_M2_MAX},
        "fichiers": quality,
        "periode": [str(df["date"].min().date()), str(df["date"].max().date())],
    }
    (OUT_DIR / "quality.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    # Les anciennes tables de la 1re version ne servent plus
    for old in ["agg_dep_mois.parquet", "hist_prix_m2.parquet"]:
        (OUT_DIR / old).unlink(missing_ok=True)
    print(f"Terminé : {len(df):,} ventes, tables écrites dans {OUT_DIR}/")


if __name__ == "__main__":
    main()
