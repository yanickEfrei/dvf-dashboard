"""Indicateurs clés et tendances dans le temps (« Quand ? »)."""
import streamlit as st

from utils import prep
from utils.i18n import t, type_name
from utils.viz import fmt_eur, fmt_int, fmt_num, fmt_pct, line_chart, show


def _delta(new, old):
    v = prep.pct(new, old)
    return None if v != v else fmt_pct(v)  # NaN -> pas de delta


def _headline(f: prep.Filters, evol_prix: float, evol_n: float) -> str:
    amp = fmt_num(abs(evol_prix), 1)
    if abs(evol_prix) < 0.5:
        p_fr, p_en = "est resté quasi stable", "remained almost unchanged"
    elif evol_prix < 0:
        p_fr, p_en = f"a baissé de {amp} %", f"fell by {amp}%"
    else:
        p_fr, p_en = f"a augmenté de {amp} %", f"rose by {amp}%"
    if evol_n < -5:
        n_fr, n_en = "chuté", "dropped"
    elif evol_n > 5:
        n_fr, n_en = "progressé", "grown"
    else:
        n_fr, n_en = "peu varié", "barely changed"
    return t(
        f"#### Entre {f.y0} et {f.y1}, le prix médian au m² des {f.type_label} {p_fr} ; "
        f"le nombre de ventes a {n_fr} ({fmt_pct(evol_n)}).",
        f"#### Between {f.y0} and {f.y1}, the median price per m² of {f.type_label} {p_en}; "
        f"the number of sales has {n_en} ({fmt_pct(evol_n)}).",
    )


def render(f: prep.Filters) -> None:
    k = prep.kpis(f.types, f.y0, f.y1, f.deps)
    if k["n"] == 0:
        st.warning(t("Aucune vente pour cette sélection. Élargissez les filtres.",
                     "No sales for this selection. Try wider filters."))
        return

    p1 = prep.period_label(f.y1)
    comparable = prep.is_partial(f.y1) and f.y0 != f.y1
    evol_prix, evol_n = prep.pct(k["prix_m2"], k["prix_m2_ref"]), prep.pct(k["n"], k["n_ref"])

    if f.y0 != f.y1:
        st.markdown(_headline(f, evol_prix, evol_n))
    st.caption(
        t(f"Zone : {f.zone} · Type : {f.type_label} · Année étudiée : {p1} · Référence : {f.y0}",
          f"Area: {f.zone} · Type: {f.type_label} · Year studied: {p1} · Baseline: {f.y0}")
        + (t(" (mêmes mois, pour comparer à période égale)",
             " (same months, for a like-for-like comparison)") if comparable else "")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Prix médian au m²", "Median price per m²"), fmt_eur(k["prix_m2"], "€/m²"),
              _delta(k["prix_m2"], k["prix_m2_ref"]), delta_color="inverse",
              help=t("La moitié des ventes s'est faite au-dessus, l'autre moitié en dessous. "
                     "La médiane résiste mieux que la moyenne aux ventes de luxe.",
                     "Half of the sales were above it, half below. The median is less "
                     "affected than the average by luxury sales."),
              border=True)
    c2.metric(t("Ventes retenues", "Sales kept"), fmt_int(k["n"]), _delta(k["n"], k["n_ref"]),
              help=t("Ventes d'un seul logement dans l'ancien, après nettoyage.",
                     "Sales of a single existing home, after cleaning."), border=True)
    c3.metric(t("Prix médian d'un bien", "Median price of a home"), fmt_eur(k["valeur"]),
              _delta(k["valeur"], k["valeur_ref"]), delta_color="inverse", border=True)
    if "ratio" in k:
        c4.metric(t("Écart entre départements", "Gap between départements"),
                  f"× {fmt_num(k['ratio'], 1)}",
                  help=t(f"Prix au m² du département le plus cher ({prep.dep_label(k['dep_max'])}) "
                         f"divisé par celui du moins cher ({prep.dep_label(k['dep_min'])}), "
                         f"parmi ceux qui ont au moins {prep.MIN_VENTES} ventes.",
                         f"Price per m² of the most expensive département "
                         f"({prep.dep_label(k['dep_max'])}) divided by the cheapest one "
                         f"({prep.dep_label(k['dep_min'])}), among those with at least "
                         f"{prep.MIN_VENTES} sales."),
                  border=True)
    else:
        c4.metric(t("Surface médiane", "Median floor area"), f"{k['surface']:.0f} m²", border=True)
    st.caption(t("Les variations sont calculées par rapport à l'année de référence. Pour les prix, "
                 "une baisse (en vert) est une bonne nouvelle pour l'acheteur.",
                 "Changes are measured against the baseline year. For prices, a decrease "
                 "(in green) is good news for buyers."))

    m = prep.monthly(f.types, min(f.y0, f.y1), max(f.y0, f.y1), f.deps)
    if m["mois"].nunique() < 2:
        st.info(t("Choisissez au moins deux années différentes pour voir l'évolution dans le temps.",
                  "Pick two different years to see the trend over time."))
        return

    st.markdown(t("##### Le prix au m², mois par mois", "##### Price per m², month by month"))
    fig = line_chart(m, "mois", "prix_m2_median", "type",
                     t("Prix médian au m² (€)", "Median price per m² (€)"),
                     events=prep.events(), y_unit=" €/m²")
    show(fig, t(
        f"courbe du prix médian au m² par mois pour les {f.type_label}, {f.zone}, "
        f"de {m['mois'].min():%m/%Y} à {m['mois'].max():%m/%Y}. Les lignes pointillées "
        "marquent la première hausse (juillet 2022) et la première baisse (juin 2024) des taux "
        "de la BCE.",
        f"line chart of the monthly median price per m² for {f.type_label}, {f.zone}, "
        f"from {m['mois'].min():%m/%Y} to {m['mois'].max():%m/%Y}. Dotted lines mark the "
        "ECB's first rate hike (July 2022) and first rate cut (June 2024).",
    ))

    st.markdown(t("##### Le nombre de ventes, mois par mois", "##### Number of sales, month by month"))
    fig = line_chart(m, "mois", "n_ventes", "type",
                     t("Nombre de ventes par mois", "Number of sales per month"),
                     events=prep.events(), y_unit=t(" ventes", " sales"))
    show(fig, t(
        f"courbe du nombre de ventes retenues par mois, {f.type_label}, {f.zone}. On y voit la "
        "saisonnalité (creux en hiver, pic avant l'été) et le niveau général du marché.",
        f"line chart of the number of sales kept per month, {f.type_label}, {f.zone}. It shows "
        "seasonality (low in winter, peak before summer) and the overall market level.",
    ))
    st.caption(t("Les deux mesures n'ont pas la même échelle : elles sont dans deux graphiques "
                 "séparés plutôt que sur un double axe, qui fausserait la lecture.",
                 "The two measures have different scales, so they are shown in two separate "
                 "charts rather than on a misleading dual axis."))

    with st.expander(t("Voir les données des courbes", "Show the chart data")):
        st.dataframe(
            m.assign(type=m["type"].map(type_name)), hide_index=True, width="stretch",
            column_config={
                "mois": st.column_config.DateColumn(t("Mois", "Month"), format="MM/YYYY"),
                "type": t("Type", "Type"),
                "prix_m2_median": st.column_config.NumberColumn(
                    t("Prix médian (€/m²)", "Median price (€/m²)"), format="%.0f"),
                "n_ventes": st.column_config.NumberColumn(t("Ventes", "Sales"), format="%d"),
            })
