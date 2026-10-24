"""
Acheter un logement en 2026 : où le rêve est-il encore possible ?
Dashboard de data storytelling sur les Demandes de valeurs foncières (DVF). FR / EN.

Lancement :  streamlit run app.py
"""
import streamlit as st

from utils.i18n import LANG_KEY, keep, region_name, remember, t, type_name, wkey  # noqa: E402

st.set_page_config(
    page_title=t("Immobilier : où acheter en 2026 ?", "Housing: where to buy in 2026?"),
    page_icon=":material/home:",
    layout="wide",
)

AUTHOR = "Yanick SHAN"
TEACHER = "Mano Joseph MATHEW"
MAJOR_FR, MAJOR_EN = "Majeure Data Engineering", "Data Engineering major"
COURSE = "Data Visualization · EFREI Paris · 2026"

from sections import budget, conclusions, deep_dives, intro, overview, quality  # noqa: E402
from utils import ai, insights, prep  # noqa: E402
from utils.io import GEOJSON_SOURCE, LICENSE, SOURCE_PRODUCER, SOURCE_TITLE, SOURCE_URL  # noqa: E402

# ---------------------------------------------------------------- Barre latérale
years = prep.available_years()
st.logo("assets/logo_efrei.svg", size="large", link="https://www.efrei.fr")
with st.sidebar:
    with st.container(border=True):
        st.markdown(t(
            f"**Réalisé par**  \n{AUTHOR}  \n:gray[{MAJOR_FR}]  \n\n"
            f"**Enseignant**  \n{TEACHER}",
            f"**Made by**  \n{AUTHOR}  \n:gray[{MAJOR_EN}]  \n\n"
            f"**Instructor**  \n{TEACHER}",
        ))
    st.radio("Langue / Language", ["FR", "EN"], horizontal=True, key=LANG_KEY)
    st.header(t("Filtres", "Filters"))
    types3 = ["Appartement", "Maison", "Les deux"]
    type_choice = keep("type", st.radio(
        t("Type de bien", "Property type"), types3, horizontal=True, format_func=type_name,
        index=types3.index(remember("type", "Les deux")), key=wkey("type")))
    if len(years) > 1:
        saved = remember("years", (years[0], years[-1]))
        if not set(saved) <= set(years):
            saved = (years[0], years[-1])
        y0, y1 = keep("years", st.select_slider(
            t("Années comparées", "Years compared"), options=years, value=saved, key=wkey("years"),
            help=t("L'année de gauche sert de référence, celle de droite est l'année étudiée. "
                   "Si l'année étudiée est incomplète, on compare les mêmes mois.",
                   "The left year is the baseline, the right one is the year studied. If the "
                   "year studied is incomplete, the same months are compared.")))
    else:
        y0 = y1 = years[0]
    regions = keep("regions", st.multiselect(
        t("Régions", "Regions"), prep.REGIONS, default=remember("regions", []),
        format_func=region_name, key=wkey("regions"),
        placeholder=t("France entière", "All of France"),
        help=t("Laisser vide pour toute la France.", "Leave empty for all of France.")))
    st.caption(t("Ces filtres s'appliquent à toutes les pages.",
                 "These filters apply to every page."))
    page_controls = st.container()  # réglages propres à la page affichée (rempli plus bas)

    st.divider()
    st.caption(t(
        f"**Source** : [{SOURCE_TITLE}]({SOURCE_URL}), {SOURCE_PRODUCER} ({LICENSE}).  \n"
        f"{GEOJSON_SOURCE}.  \nTaux de crédit : Observatoire Crédit Logement / CSA.  \n"
        "Traitements : ventes d'un seul logement dans l'ancien, médianes ; voir *Qualité des "
        "données*.",
        f"**Source**: [{SOURCE_TITLE}]({SOURCE_URL}) (French property sales records), "
        f"French Public Finances Directorate (DGFiP), {LICENSE}.  \n"
        "Département boundaries: france-geojson (G. David), based on IGN / OpenStreetMap.  \n"
        "Mortgage rates: Observatoire Crédit Logement / CSA.  \n"
        "Processing: sales of a single existing home, medians; see *Data quality*.",
    ))

f = prep.Filters(type_choice, min(y0, y1), max(y0, y1), tuple(regions))


# ---------------------------------------------------------------- Pages
def _credits_line() -> None:
    st.markdown(t(
        f":gray[{AUTHOR} · {MAJOR_FR} · Enseignant : {TEACHER} · {COURSE}]",
        f":gray[{AUTHOR} · {MAJOR_EN} · Instructor: {TEACHER} · {COURSE}]",
    ))


def _page_title(fr: str, en: str, sub_fr: str, sub_en: str) -> None:
    st.title(t(fr, en))
    st.caption(t(sub_fr, sub_en))


def _has_sales() -> bool:
    if prep.kpis(f.types, f.y0, f.y1, f.deps)["n"] > 0:
        return True
    st.warning(t("Aucune vente pour cette sélection (Mayotte, le Bas-Rhin, le Haut-Rhin et la "
                 "Moselle ne sont pas couverts par DVF). Élargissez les filtres.",
                 "No sales for this selection (Mayotte, Bas-Rhin, Haut-Rhin and Moselle are not "
                 "covered by DVF). Try wider filters."),
               icon=":material/warning:")
    return False


def page_home() -> None:
    st.title(t("Acheter un logement en 2026 : où le rêve est-il encore possible ?",
               "Buying a home in 2026: where is it still within reach?"))
    st.caption(t(f"Cinq ans de ventes immobilières en France. Source :{SOURCE_TITLE} "
                 f"(data.gouv.fr, {LICENSE})",
                 "Five years of property sales in France. Source:Demandes de valeurs foncières "
                 f"(DVF, data.gouv.fr, {LICENSE})"))
    _credits_line()
    intro.render()
    st.divider()
    st.subheader(t("Explorer le récit", "Explore the story"))
    cards = [
        (p_when, t("Prix et nombre de ventes, mois par mois, depuis 2022.",
                   "Prices and number of sales, month by month, since 2022.")),
        (p_where, t("Carte, plus fortes baisses et lecture prix / volumes.",
                    "Map, biggest falls and prices vs volumes.")),
        (p_budget, t("Ce qu'une mensualité permet d'acheter, taux compris.",
                     "What a monthly payment buys, rates included.")),
        (p_dep, t("Un département en détail, jusqu'aux communes.",
                  "One département in detail, down to towns.")),
    ]
    cols = st.columns(len(cards))
    for col, (page, desc) in zip(cols, cards):
        with col, st.container(border=True, height="stretch"):
            st.page_link(page)
            st.caption(desc)


def page_when() -> None:
    _page_title("Quand ? Prix et ventes depuis 2022", "When? Prices and sales since 2022",
                "Comment ont évolué le prix au m² et le nombre de ventes depuis la hausse des taux ?",
                "How have the price per m² and the number of sales changed since rates went up?")
    if _has_sales():
        overview.render(f)
        insights.render("quand", f)
        ai.render("quand", f)


def page_where() -> None:
    _page_title("Où ? Les écarts entre territoires", "Where? Gaps between areas",
                "Quels départements sont les plus chers, lesquels ont le plus baissé ?",
                "Which départements are the most expensive, and which fell the most?")
    if _has_sales():
        deep_dives.render_where(f)
        insights.render("ou", f)
        ai.render("ou", f)


def page_budget() -> None:
    _page_title("Quoi ? Ce que l'on peut vraiment acheter", "What? What you can really buy",
                "La baisse des prix a-t-elle compensé la hausse des taux ?",
                "Has the fall in prices made up for the rise in rates?")
    if _has_sales():
        budget.render(f)
        insights.render("pouvoir-achat", f)
        ai.render("pouvoir-achat", f)


def page_dep() -> None:
    _page_title("Zoom sur un département", "Focus on one département",
                "Appartements et maisons ont-ils suivi la même trajectoire ?",
                "Did apartments and houses follow the same path?")
    deep_dives.render_focus(f)
    insights.render("departement", f)
    ai.render("departement", f)


def page_quality() -> None:
    _page_title("Qualité des données et limites", "Data quality and limitations",
                "D'où viennent les chiffres, et ce qu'ils ne disent pas.",
                "Where the figures come from, and what they do not say.")
    quality.render()


def page_conclusions() -> None:
    _page_title("Conclusions", "Conclusions",
                "Ce qu'il faut retenir, pour un acheteur et pour les décideurs.",
                "Key takeaways, for buyers and for policymakers.")
    conclusions.render()


p_home = st.Page(page_home, title=t("Accueil", "Home"), icon=":material/home:",
                 url_path="accueil", default=True)
p_when = st.Page(page_when, title=t("Quand ?", "When?"), icon=":material/show_chart:",
                 url_path="quand")
p_where = st.Page(page_where, title=t("Où ?", "Where?"), icon=":material/map:", url_path="ou")
p_budget = st.Page(page_budget, title=t("Pouvoir d'achat", "Affordability"),
                   icon=":material/savings:", url_path="pouvoir-achat")
p_dep = st.Page(page_dep, title=t("Zoom département", "Département focus"),
                icon=":material/location_city:", url_path="departement")
p_quality = st.Page(page_quality, title=t("Qualité des données", "Data quality"),
                    icon=":material/fact_check:", url_path="qualite")
p_conclusions = st.Page(page_conclusions, title=t("Conclusions", "Conclusions"),
                        icon=":material/lightbulb:", url_path="conclusions")

page = st.navigation([p_home, p_when, p_where, p_budget, p_dep, p_quality, p_conclusions],
                     position="top")
if page.url_path == p_where.url_path:
    with page_controls:
        st.subheader(t("Réglage de la page", "Page setting"))
        deep_dives.pick_map_metric()
page.run()

st.divider()
_credits_line()
