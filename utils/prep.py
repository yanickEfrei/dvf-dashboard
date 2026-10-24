"""Référentiels géographiques et calculs (filtrage, médianes, tables pour les graphiques).

Toutes les fonctions publiques prennent des arguments simples (tuples, int, str)
pour pouvoir être mises en cache par st.cache_data sans hacher le gros DataFrame.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.i18n import in_region, is_en, month_name, t, type_plural  # noqa: F401
from utils.io import load_communes, load_sales

TYPES = ("Appartement", "Maison")
MIN_VENTES = 30          # en dessous, une médiane départementale n'est pas affichée
MIN_VENTES_COMMUNE = 20  # idem pour une commune (stabilité + confidentialité)
BIN_WIDTH = 250          # €/m², largeur des barres de l'histogramme

# --------------------------------------------------------------------------
# Référentiel départements -> nom, région
# --------------------------------------------------------------------------
DEP_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône",
    "14": "Calvados", "15": "Cantal", "16": "Charente", "17": "Charente-Maritime",
    "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud", "2B": "Haute-Corse",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault",
    "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère",
    "39": "Jura", "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne",
    "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise",
    "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres",
    "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse",
    "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion",
    "976": "Mayotte",
}

_REGIONS = {
    "Auvergne-Rhône-Alpes": "01 03 07 15 26 38 42 43 63 69 73 74",
    "Bourgogne-Franche-Comté": "21 25 39 58 70 71 89 90",
    "Bretagne": "22 29 35 56",
    "Centre-Val de Loire": "18 28 36 37 41 45",
    "Corse": "2A 2B",
    "Grand Est": "08 10 51 52 54 55 57 67 68 88",
    "Hauts-de-France": "02 59 60 62 80",
    "Île-de-France": "75 77 78 91 92 93 94 95",
    "Normandie": "14 27 50 61 76",
    "Nouvelle-Aquitaine": "16 17 19 23 24 33 40 47 64 79 86 87",
    "Occitanie": "09 11 12 30 31 32 34 46 48 65 66 81 82",
    "Pays de la Loire": "44 49 53 72 85",
    "Provence-Alpes-Côte d'Azur": "04 05 06 13 83 84",
    "Guadeloupe": "971", "Martinique": "972", "Guyane": "973",
    "La Réunion": "974", "Mayotte": "976",
}
DEP_REGION = {d: r for r, deps in _REGIONS.items() for d in deps.split()}
REGIONS = list(_REGIONS)

# Événements de contexte (dates officielles BCE) pour annoter les courbes
def events() -> list[tuple[str, str]]:
    return [
        ("2022-07-01", t("Juil. 2022 : 1re hausse des taux de la BCE",
                         "Jul 2022: first ECB rate hike")),
        ("2024-06-01", t("Juin 2024 : 1re baisse des taux de la BCE",
                         "Jun 2024: first ECB rate cut")),
    ]


# Taux moyens des crédits immobiliers (hors assurance), moyennes annuelles arrondies,
# d'après l'Observatoire Crédit Logement / CSA (2026 : premier semestre).
# Ce sont des ordres de grandeur : l'appli les propose par défaut et on peut les modifier.
MORTGAGE_RATES = {2022: 1.6, 2023: 3.6, 2024: 3.7, 2025: 3.1, 2026: 3.2}
NOTARY_FEES = 0.075      # frais de notaire dans l'ancien, environ 7 à 8 % du prix


def loan_capacity(monthly: float, rate_pct: float, years: int) -> float:
    """Capital empruntable avec une mensualité donnée (prêt amortissable à taux fixe)."""
    r, n = rate_pct / 100 / 12, years * 12
    return monthly * n if r == 0 else monthly * (1 - (1 + r) ** -n) / r


def dep_label(code: str) -> str:
    return f"{code} – {DEP_NAMES.get(code, code)}"


def deps_for_regions(regions: tuple[str, ...]) -> tuple[str, ...] | None:
    """None = France entière."""
    if not regions:
        return None
    return tuple(sorted(d for d, r in DEP_REGION.items() if r in regions))


def types_for(choice: str) -> tuple[str, ...]:
    return TYPES if choice == "Les deux" else (choice,)


# --------------------------------------------------------------------------
# Période
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def available_years() -> list[int]:
    return sorted(load_sales()["annee"].unique().tolist())


@st.cache_data(show_spinner=False)
def last_month(year: int) -> int:
    """Dernier mois disponible d'une année (12 si année complète)."""
    df = load_sales()
    return int(df.loc[df["annee"] == year, "num_mois"].max())


def is_partial(year: int) -> bool:
    return last_month(year) < 12


def period_label(year: int) -> str:
    m = last_month(year)
    if m == 12:
        return str(year)
    return t(f"{year} (janv.–{month_name(m)})", f"{year} (Jan–{month_name(m)})")


# --------------------------------------------------------------------------
# Sélection
# --------------------------------------------------------------------------
def _select(types, years, deps=None, max_month: int = 12) -> pd.DataFrame:
    df = load_sales()
    m = df["type"].isin(types) & df["annee"].isin(years)
    if deps is not None:
        m &= df["dep"].isin(deps)
    if max_month < 12:
        m &= df["num_mois"] <= max_month
    return df.loc[m]


def pct(new: float, old: float) -> float:
    if old is None or new is None or not old or np.isnan(old) or np.isnan(new):
        return np.nan
    return (new / old - 1) * 100


@st.cache_data(show_spinner=False)
def kpis(types, y0: int, y1: int, deps) -> dict:
    """Indicateurs de l'année y1, comparés à y0 sur les mêmes mois (comparabilité)."""
    mm = last_month(y1)
    cur = _select(types, (y1,), deps)
    ref = _select(types, (y0,), deps, max_month=mm)
    out = {
        "n": len(cur), "n_ref": len(ref),
        "prix_m2": cur["prix_m2"].median(), "prix_m2_ref": ref["prix_m2"].median(),
        "valeur": cur["valeur"].median(), "valeur_ref": ref["valeur"].median(),
        "surface": cur["surface"].median(), "surface_ref": ref["surface"].median(),
    }
    by_dep = cur.groupby("dep", observed=True)["prix_m2"].agg(["median", "size"])
    by_dep = by_dep[by_dep["size"] >= MIN_VENTES]
    if len(by_dep) >= 2:
        out["dep_max"], out["dep_min"] = by_dep["median"].idxmax(), by_dep["median"].idxmin()
        out["ratio"] = by_dep["median"].max() / by_dep["median"].min()
    return out


@st.cache_data(show_spinner=False)
def monthly(types, y0: int, y1: int, deps) -> pd.DataFrame:
    df = _select(types, tuple(range(y0, y1 + 1)), deps)
    return (df.groupby(["mois", "type"], observed=True)["prix_m2"]
              .agg(prix_m2_median="median", n_ventes="size").reset_index())


@st.cache_data(show_spinner=False)
def by_dep(types, y0: int, y1: int, deps) -> pd.DataFrame:
    """Une ligne par département : prix médian y1, évolution vs y0 (mêmes mois), volumes."""
    mm = last_month(y1)
    cur = (_select(types, (y1,), deps).groupby("dep", observed=True)
           .agg(prix=("prix_m2", "median"), n=("prix_m2", "size"),
                surface=("surface", "median"), valeur=("valeur", "median")))
    ref = (_select(types, (y0,), deps, max_month=mm).groupby("dep", observed=True)
           .agg(prix_ref=("prix_m2", "median"), n_ref=("prix_m2", "size")))
    t = cur.join(ref, how="left").reset_index()
    t["dep"] = t["dep"].astype(str)
    ok = (t["n"] >= MIN_VENTES) & (t["n_ref"].fillna(0) >= MIN_VENTES)
    t["evol_prix"] = np.where(ok, (t["prix"] / t["prix_ref"] - 1) * 100, np.nan)
    t["evol_n"] = np.where(ok, (t["n"] / t["n_ref"] - 1) * 100, np.nan)
    t.loc[t["n"] < MIN_VENTES, "prix"] = np.nan
    t["nom"] = t["dep"].map(DEP_NAMES)
    t["region"] = t["dep"].map(DEP_REGION)
    t["label"] = t["dep"] + " – " + t["nom"]
    return t


@st.cache_data(show_spinner=False)
def evol_by_type(y0: int, y1: int, deps) -> pd.DataFrame:
    """Évolution du prix au m² par département, une colonne par type de bien."""
    cols = {typ: by_dep((typ,), y0, y1, deps).set_index("dep")["evol_prix"] for typ in TYPES}
    return pd.DataFrame(cols)


@st.cache_data(show_spinner=False)
def by_region(types, year: int, deps) -> pd.DataFrame:
    df = _select(types, (year,), deps)
    reg = df["dep"].map(DEP_REGION).astype(str)
    return (df.groupby(reg)["prix_m2"].agg(prix="median", n="size")
              .rename_axis("region").reset_index())


@st.cache_data(show_spinner=False)
def dep_yearly(dep: str, types) -> pd.DataFrame:
    df = _select(types, tuple(available_years()), (dep,))
    if df.empty:  # ex. Alsace-Moselle, Mayotte : non couverts par DVF
        return pd.DataFrame(columns=["annee", "type", "median", "n", "q1", "q3", "periode"])
    g = df.groupby(["annee", "type"], observed=True)["prix_m2"]
    t = g.agg(median="median", n="size")
    q = g.quantile([0.25, 0.75]).unstack()
    t["q1"], t["q3"] = q[0.25], q[0.75]
    t = t.reset_index()
    t["periode"] = t["annee"].map(lambda y: f"{y}*" if is_partial(y) else str(y))
    return t


@st.cache_data(show_spinner=False)
def dep_hist(dep: str, year: int, types) -> pd.DataFrame:
    df = _select(types, (year,), (dep,))
    b = (df["prix_m2"] // BIN_WIDTH * BIN_WIDTH).astype(int)
    return (df.assign(bin=b).groupby(["type", "bin"], observed=True).size()
              .rename("n").reset_index())


@st.cache_data(show_spinner=False)
def communes(dep: str, typ: str, y0: int, y1: int) -> pd.DataFrame:
    c = load_communes()
    c = c[(c["dep"] == dep) & (c["type"] == typ)]
    cur = c[c["annee"] == y1].set_index(["code_insee", "commune"])
    ref = c[c["annee"] == y0].set_index(["code_insee", "commune"])
    t = cur[["n_ventes", "prix_m2_median", "prix_m2_q1", "prix_m2_q3"]].join(
        ref[["prix_m2_median", "n_ventes"]].rename(
            columns={"prix_m2_median": "prix_ref", "n_ventes": "n_ref"}), how="left")
    t = t[t["n_ventes"] >= MIN_VENTES_COMMUNE].reset_index()
    ok = t["n_ref"].fillna(0) >= MIN_VENTES_COMMUNE
    t["evol"] = np.where(ok, (t["prix_m2_median"] / t["prix_ref"] - 1) * 100, np.nan)
    return t.sort_values("prix_m2_median", ascending=False)


# --------------------------------------------------------------------------
# Faits « nationaux » qui portent l'histoire (indépendants des filtres)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def story_facts() -> dict:
    years = available_years()
    full = [y for y in years if not is_partial(y)]
    df = load_sales()
    vol = df.groupby("annee").size()
    med = df.groupby(["annee", "type"], observed=True)["prix_m2"].median().unstack()
    f = {"years": years, "full_years": full, "volume": vol.to_dict(),
         "median": med.to_dict(orient="index")}
    if len(full) >= 2:
        first, last = full[0], full[-1]
        f["first"], f["last"] = first, last
        f["vol_min_year"] = int(vol.loc[full].idxmin())
        f["vol_drop"] = pct(vol[f["vol_min_year"]], vol[first])
        f["vol_rebound"] = pct(vol[last], vol[f["vol_min_year"]])
        f["prix_evol"] = {t: pct(med.loc[last, t], med.loc[first, t]) for t in TYPES}
        # pic et creux du prix des appartements
        f["prix_peak_year"] = int(med["Appartement"].loc[full].idxmax())
        f["prix_low_year"] = int(med["Appartement"].loc[full].idxmin())
    ref_year = full[-1] if full else years[-1]
    d = by_dep(TYPES, ref_year, ref_year, None).dropna(subset=["prix"])
    f["ref_year"] = ref_year
    f["dep_max"] = d.loc[d["prix"].idxmax()].to_dict()
    f["dep_min"] = d.loc[d["prix"].idxmin()].to_dict()
    return f


# --------------------------------------------------------------------------
# Filtres choisis dans la barre latérale
# --------------------------------------------------------------------------
from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class Filters:
    type_choice: str                 # "Appartement", "Maison" ou "Les deux"
    y0: int                          # année de référence
    y1: int                          # année étudiée
    regions: tuple[str, ...]         # () = France entière

    @property
    def types(self) -> tuple[str, ...]:
        return types_for(self.type_choice)

    @property
    def deps(self) -> tuple[str, ...] | None:
        return deps_for_regions(self.regions)

    @property
    def zone(self) -> str:
        from utils.i18n import region_name
        if not self.regions:
            return t("France entière", "all of France")
        if len(self.regions) <= 2:
            return ", ".join(region_name(r) for r in self.regions)
        return t(f"{len(self.regions)} régions", f"{len(self.regions)} regions")

    @property
    def type_label(self) -> str:
        return type_plural(self.type_choice)
