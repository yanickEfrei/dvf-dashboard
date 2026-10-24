"""Traduction français / anglais.

La langue est choisie dans la barre latérale (clé de session « lang »).
Usage :  t("Texte en français", "English text")
"""
import pandas as pd
import streamlit as st

LANG_KEY = "lang"


def is_en() -> bool:
    return st.session_state.get(LANG_KEY) == "EN"


def t(fr: str, en: str) -> str:
    return en if is_en() else fr


# ---- Types de bien ---------------------------------------------------------
_TYPE = {  # valeur interne -> (singulier FR, pluriel FR, singulier EN, pluriel EN)
    "Appartement": ("Appartement", "appartements", "Apartment", "apartments"),
    "Maison": ("Maison", "maisons", "House", "houses"),
    "Les deux": ("Les deux", "appartements et maisons", "Both", "apartments and houses"),
}


def type_name(x: str) -> str:
    v = _TYPE.get(x)
    return x if v is None else (v[2] if is_en() else v[0])


def type_plural(x: str) -> str:
    v = _TYPE.get(x)
    return x if v is None else (v[3] if is_en() else v[1])


# ---- Mois ------------------------------------------------------------------
_MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.",
              "oct.", "nov.", "déc."]
_MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
              "Dec"]


def month_name(m: int) -> str:
    return (_MONTHS_EN if is_en() else _MONTHS_FR)[m - 1]


def month_label(ts: pd.Timestamp) -> str:
    return f"{month_name(ts.month)} {ts.year}"


# ---- Régions ---------------------------------------------------------------
_REGION_EN = {"Bretagne": "Brittany", "Normandie": "Normandy", "Corse": "Corsica",
              "Occitanie": "Occitania", "Guyane": "French Guiana", "La Réunion": "Réunion"}
_REGION_PREP_FR = {"Grand Est": "dans le", "Hauts-de-France": "dans les",
                   "Pays de la Loire": "dans les", "La Réunion": "à", "Mayotte": "à"}


def region_name(r: str) -> str:
    return _REGION_EN.get(r, r) if is_en() else r


def in_region(r: str) -> str:
    """« en Bretagne », « dans le Grand Est »… / « in Brittany »."""
    if is_en():
        return f"in {'the ' if r == 'Grand Est' else ''}{region_name(r)}"
    return f"{_REGION_PREP_FR.get(r, 'en')} {r}"


# ---- Filtres conservés quand on change de langue -------------------------
# Quand la langue change, les libellés des widgets changent et Streamlit les recrée.
# On stocke donc chaque valeur à part (« _nom ») et on donne aux widgets une clé
# par langue (« nom_FR », « nom_EN ») initialisée avec la valeur mémorisée.
def wkey(name: str) -> str:
    return f"{name}_{'EN' if is_en() else 'FR'}"


def remember(name: str, default):
    return st.session_state.setdefault(f"_{name}", default)


def keep(name: str, value):
    st.session_state[f"_{name}"] = value
    return value
