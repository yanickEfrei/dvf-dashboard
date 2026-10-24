"""Chargement des données préparées et informations sur la source."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
GEOJSON_PATH = ROOT / "data" / "departements.geojson"

SOURCE_TITLE = "Demandes de valeurs foncières (DVF)"
SOURCE_PRODUCER = "Direction générale des Finances publiques (DGFiP)"
SOURCE_URL = "https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/"
LICENSE = "Licence Ouverte / Open Licence 2.0 (Etalab)"
GEOJSON_SOURCE = "Contours des départements : france-geojson (G. David), d'après IGN / OpenStreetMap"


def _check(path: Path) -> None:
    if not path.exists():
        st.error(
            f"Fichier introuvable : `{path.relative_to(ROOT)}`. "
            "Lance d'abord `python download_data.py` puis `python prepare_data.py` "
            "(voir le README)."
        )
        st.stop()


@st.cache_resource(show_spinner="Chargement des ventes…")
def load_sales() -> pd.DataFrame:
    """Une ligne = une vente d'un logement. Partagée en lecture seule (pas de copie)."""
    path = PROCESSED / "ventes.parquet"
    _check(path)
    df = pd.read_parquet(path)
    df["annee"] = df["mois"].dt.year.astype("int16")
    df["num_mois"] = df["mois"].dt.month.astype("int8")
    return df


@st.cache_data(show_spinner=False)
def load_communes() -> pd.DataFrame:
    path = PROCESSED / "agg_commune_annee.parquet"
    _check(path)
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def load_quality() -> dict:
    path = PROCESSED / "quality.json"
    _check(path)
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_geojson() -> str:
    """Texte brut du GeoJSON (hachable, donc les contours projetés sont mis en cache)."""
    _check(GEOJSON_PATH)
    return GEOJSON_PATH.read_text(encoding="utf-8")
