"""Qualité des données : manquants, doublons, étapes de nettoyage, contrôles, limites."""
import pandas as pd
import streamlit as st

from utils import prep
from utils.i18n import t
from utils.io import LICENSE, SOURCE_URL, load_quality, load_sales
from utils.viz import fmt_eur, fmt_int, funnel, show

# Clé dans quality.json -> (libellé FR, libellé EN)
STAGES = [
    ("lignes_brutes", "Fichiers bruts", "Raw files"),
    ("apres_doublons", "Sans doublons exacts", "Exact duplicates removed"),
    ("apres_filtre_vente", "Ventes classiques uniquement", "Standard sales only"),
    ("ventes_distinctes", "Regroupées en ventes", "Grouped into sales"),
    ("ventes_un_logement", "Ventes d'un seul logement", "Single-home sales"),
    ("apres_valeur_surface_valides", "Prix et surface valides", "Valid price and area"),
    ("lignes_finales", "Sans prix aberrants", "Outliers removed"),
]


def _stage_labels() -> dict:
    return {k: t(fr, en) for k, fr, en in STAGES}


def _checks() -> pd.DataFrame:
    """Contrôles de validation exécutés à chaque lancement sur la table finale."""
    df = load_sales()
    q = load_quality()["seuils"]
    rows = [
        (t("Aucune valeur manquante dans la table finale", "No missing values in the final table"),
         not df.isna().any().any()),
        (t(f"Tous les prix au m² entre {fmt_eur(q['prix_m2_min'])} et {fmt_eur(q['prix_m2_max'])}",
           f"All prices per m² between {fmt_eur(q['prix_m2_min'])} and {fmt_eur(q['prix_m2_max'])}"),
         bool(df["prix_m2"].between(q["prix_m2_min"], q["prix_m2_max"]).all())),
        (t(f"Toutes les surfaces ≥ {q['surface_min_m2']} m²",
           f"All floor areas ≥ {q['surface_min_m2']} m²"),
         bool((df["surface"] >= q["surface_min_m2"]).all())),
        (t("Uniquement des maisons et des appartements", "Only houses and apartments"),
         set(df["type"].unique()) <= set(prep.TYPES)),
        (t("Tous les codes département sont connus", "All département codes are valid"),
         set(df["dep"].astype(str).unique()) <= set(prep.DEP_NAMES)),
        (t("Dates dans la période des fichiers", "Dates within the files' period"),
         df["annee"].min() >= min(prep.available_years())),
    ]
    out = pd.DataFrame(rows, columns=["check", "ok"])
    out["ok"] = out["ok"].map({True: t("✅ Réussi", "✅ Passed"), False: t("❌ Échec", "❌ Failed")})
    return out


def render() -> None:
    st.subheader(t("Peut-on faire confiance à ces chiffres ?", "Can we trust these figures?"))
    rep = load_quality()
    files = pd.DataFrame(rep["fichiers"])
    keys = [k for k, _, _ in STAGES]
    tot = files[keys].sum()
    kept = tot["lignes_finales"] / tot["lignes_brutes"] * 100
    st.markdown(t(
        f"#### Sur {fmt_int(tot['lignes_brutes'])} lignes brutes, {fmt_int(tot['lignes_finales'])} "
        f"ventes sont retenues ({kept:.0f} %), non pas parce que les autres sont fausses, mais "
        "parce qu'elles ne mesurent pas la même chose.",
        f"#### Out of {fmt_int(tot['lignes_brutes'])} raw rows, {fmt_int(tot['lignes_finales'])} "
        f"sales are kept ({kept:.0f}%), not because the others are wrong, but because they "
        "do not measure the same thing.",
    ))

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        labels = _stage_labels()
        stages = pd.DataFrame({"etape": [labels[k] for k in keys], "lignes": [tot[k] for k in keys]})
        show(funnel(stages), t(
            "entonnoir horizontal du nombre de lignes à chaque étape du nettoyage, de "
            f"{fmt_int(tot['lignes_brutes'])} lignes brutes à {fmt_int(tot['lignes_finales'])} "
            "ventes retenues.",
            "horizontal funnel of the number of rows at each cleaning step, from "
            f"{fmt_int(tot['lignes_brutes'])} raw rows to {fmt_int(tot['lignes_finales'])} "
            "sales kept.",
        ))
    with c2:
        st.markdown(t(
            """
**Pourquoi chaque étape ?**
- **Doublons** : lignes strictement identiques (erreurs d'export).
- **Ventes classiques** : on écarte échanges, ventes aux enchères, ventes sur plan (neuf)
  et terrains, qui n'ont pas un prix comparable.
- **Regroupement** : une vente « appartement + cave + parking » occupe 3 lignes
  avec le même prix. Il n'y a pas d'identifiant de vente : on le reconstitue
  (date, prix, adresse, numéro de disposition).
- **Un seul logement** : pour un immeuble vendu en bloc, on ne peut pas calculer
  de prix au m² par logement. Caves et parkings sont tolérés.
- **Valeurs aberrantes** : surface < 9 m², prix < 300 €/m² (ventes symboliques)
  ou > 30 000 €/m² (erreurs de surface).
""",
            """
**Why each step?**
- **Duplicates**: strictly identical rows (export errors).
- **Standard sales**: swaps, auctions, off-plan sales (new builds) and building plots are
  excluded because their prices are not comparable.
- **Grouping**: a sale of “apartment + cellar + parking space” takes 3 rows with the same
  price. There is no sale ID, so we rebuild one (date, price, address, disposal number).
- **Single home**: when a whole building is sold at once, there is no way to compute a
  price per m² for each home. Cellars and parking spaces are allowed.
- **Outliers**: floor area < 9 m², price < €300/m² (token sales) or > €30,000/m²
  (floor-area errors).
""",
        ))

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(t("##### Valeurs manquantes dans les fichiers bruts (%)",
                      "##### Missing values in the raw files (%)"))
        na = pd.DataFrame({r["fichier"].replace("ValeursFoncieres-", "").replace(".txt", ""):
                           r["manquants_pct"] for r in rep["fichiers"]})
        st.dataframe(na, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.1f")
                                    for c in na.columns})
        n_empty = rep["fichiers"][0].get("colonnes_vides_90pct", "–")
        n_cols = rep["fichiers"][0].get("colonnes_brutes", "–")
        st.caption(t(
            "« Type local » et « Surface » sont vides pour les terrains et parcelles agricoles, "
            f"qui ne sont pas des logements : ce n'est pas un défaut. {n_empty} colonnes sur "
            f"{n_cols} sont vides à plus de 90 % et ne sont pas utilisées.",
            "“Type local” (property type) and “Surface” (floor area) are empty for land and farm "
            f"plots, which are not homes: this is expected. {n_empty} of the {n_cols} columns are "
            "more than 90% empty and are not used.",
        ))
    with c2:
        st.markdown(t("##### Contrôles automatiques sur la table finale",
                      "##### Automatic checks on the final table"))
        st.dataframe(_checks(), hide_index=True, width="stretch",
                     column_config={"check": t("Contrôle", "Check"), "ok": t("Résultat", "Result")})
        st.caption(t("Ces contrôles sont recalculés à chaque lancement de l'appli.",
                     "These checks run every time the app starts."))

    with st.expander(t("Détail par fichier", "Details by file")):
        st.dataframe(files[["fichier"] + keys + ["valeurs_aberrantes_retirees"]]
                     .rename(columns={**_stage_labels(), "fichier": t("Fichier", "File"),
                                      "valeurs_aberrantes_retirees":
                                          t("Nb de valeurs aberrantes retirées", "Number of outliers dropped")}),
                     hide_index=True, width="stretch")

    last = prep.period_label(max(prep.available_years()))
    st.markdown(t("##### Limites et biais connus", "##### Known limitations and biases"))
    st.markdown(t(
        f"""
- **Couverture** : DVF ne couvre pas le Bas-Rhin, le Haut-Rhin et la Moselle (régime du
  livre foncier) ni Mayotte. {last} est une année partielle : on la compare toujours aux
  mêmes mois des autres années.
- **Ce qu'on mesure** : un prix **déclaré** au m², sans l'état du bien, l'étage, la vue ou
  les travaux. Une médiane départementale mélange centres-villes et campagnes.
- **Ce qu'on ne mesure pas** : le neuf, les ventes en bloc, et le **coût du crédit**.
  Les dates de la BCE sur les courbes sont un contexte : elles ne prouvent pas un lien de
  cause à effet.
- **Publication** : DVF est publié avec plusieurs mois de décalage et mis à jour tous les
  semestres ; des ventes récentes peuvent manquer.
- **Confidentialité** : aucune vente individuelle ni adresse n'est affichée ; seules des
  médianes sur au moins {prep.MIN_VENTES_COMMUNE} ventes (communes) ou {prep.MIN_VENTES}
  ventes (départements) sont montrées, conformément aux conditions de réutilisation de DVF.

Source : [{SOURCE_URL}]({SOURCE_URL}) ({LICENSE}).
""",
        f"""
- **Coverage**: DVF does not cover Bas-Rhin, Haut-Rhin and Moselle (which use a different
  land registry system), nor Mayotte. {last} is a partial year: it is always compared with
  the same months of other years.
- **What we measure**: a **declared** price per m², without the home's condition, floor,
  view or renovation work. A département median mixes city centres and countryside.
- **What we do not measure**: new builds, bulk sales, and the **cost of credit**. The ECB
  dates on the charts are context: they do not prove cause and effect.
- **Publication**: DVF is published several months late and updated every six months;
  recent sales may be missing.
- **Privacy**: no individual sale or address is shown; only medians based on at least
  {prep.MIN_VENTES_COMMUNE} sales (towns) or {prep.MIN_VENTES} sales (départements) are
  displayed, in line with DVF's terms of reuse.

Source: [{SOURCE_URL}]({SOURCE_URL}) ({LICENSE}).
""",
    ))
