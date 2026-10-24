"""Formules utilisées dans l'appli : un seul texte, affiché sous chaque page et dans la page Qualité."""
import streamlit as st

from utils import prep
from utils.i18n import is_en, t


def _notary() -> str:
    return f"{prep.NOTARY_FEES * 100:.1f}".replace(".", t(",", "."))


def _rates() -> str:
    if is_en():
        return "; ".join(f"{y}: {r:.1f}%" for y, r in prep.MORTGAGE_RATES.items())
    return " ; ".join(f"{y} : {r:.1f} %".replace(".", ",") for y, r in prep.MORTGAGE_RATES.items())


# Chaque sujet renvoie une liste de puces (markdown).
def _base() -> list[str]:
    return [
        t("**Prix au m² d'une vente** = valeur foncière ÷ surface réelle bâtie.",
          "**Price per m² of a sale** = sale value ÷ actual built floor area."),
        t("**Prix médian au m²** : la moitié des ventes est au-dessus, l'autre en dessous. On "
          "utilise la médiane plutôt que la moyenne, qui est tirée vers le haut par les ventes de "
          f"luxe. Elle n'est affichée que si elle repose sur au moins **{prep.MIN_VENTES} ventes** "
          f"(département) ou **{prep.MIN_VENTES_COMMUNE} ventes** (commune).",
          "**Median price per m²**: half of the sales are above, half below. The median is used "
          "rather than the average, which luxury sales pull upwards. It is only shown when based "
          f"on at least **{prep.MIN_VENTES} sales** (département) or "
          f"**{prep.MIN_VENTES_COMMUNE} sales** (town)."),
    ]


def _evol() -> list[str]:
    return [
        t("**Évolution (%)** = (médiane de l'année étudiée ÷ médiane de l'année de référence − 1) "
          "× 100. Même formule pour le nombre de ventes.",
          "**Change (%)** = (median of the year studied ÷ median of the baseline year − 1) × 100. "
          "Same formula for the number of sales."),
        t("**Année partielle** : si l'année étudiée s'arrête en juin, l'année de référence est "
          "limitée aux mêmes mois (janvier à juin), pour comparer à période égale.",
          "**Partial year**: if the year studied stops in June, the baseline year is limited to "
          "the same months (January to June), for a like-for-like comparison."),
    ]


def _gap() -> list[str]:
    return [t("**Écart entre départements** = médiane du département le plus cher ÷ médiane du "
              "moins cher (parmi ceux qui ont assez de ventes).",
              "**Gap between départements** = median of the most expensive département ÷ median "
              "of the cheapest one (among those with enough sales).")]


def _when() -> list[str]:
    return [t("**Courbes** : une médiane par mois et par type de bien. Les lignes pointillées "
              "marquent la 1re hausse (juillet 2022) et la 1re baisse (juin 2024) des taux de la "
              "BCE : c'est un repère de contexte, pas une preuve de cause à effet.",
              "**Charts**: one median per month and property type. Dotted lines mark the ECB's "
              "first rate hike (July 2022) and first cut (June 2024): a context marker, not proof "
              "of cause and effect.")]


def _quadrants() -> list[str]:
    return [
        t("**Plus fortes baisses** : départements classés selon l'évolution du prix médian de "
          "l'ensemble des biens choisis ; les barres détaillent chaque type de bien.",
          "**Biggest falls**: départements ranked by the change in median price for all the "
          "selected homes; the bars show each property type."),
        t("**Quadrants prix × ventes** : chaque département est classé selon le signe de ses deux "
          "évolutions (prix en hausse ou en baisse, ventes en hausse ou en baisse). La taille du "
          "point est proportionnelle au nombre de ventes.",
          "**Prices × sales quadrants**: each département is placed according to the sign of its "
          "two changes (prices up or down, sales up or down). Dot size is proportional to the "
          "number of sales."),
    ]


def _fixed() -> list[str]:
    return [t("**Budget fixe** : surface achetable = budget ÷ prix médian au m² de la région.",
              "**Fixed budget**: affordable area = budget ÷ median price per m² in the region.")]


def _credit() -> list[str]:
    n = _notary()
    return [
        t("**Capital empruntable** (prêt à taux fixe) = M × (1 − (1 + r)⁻ⁿ) ÷ r, avec M la "
          "mensualité, r le taux annuel ÷ 12 et n la durée en mois. Hors assurance.",
          "**Borrowing capacity** (fixed-rate loan) = M × (1 − (1 + r)⁻ⁿ) ÷ r, where M is the "
          "monthly payment, r the annual rate ÷ 12 and n the term in months. Excluding insurance."),
        t(f"**Budget d'achat** = (capital empruntable + apport) ÷ (1 + {n} %) si les frais de "
          "notaire sont déduits.",
          f"**Purchase budget** = (borrowing capacity + down payment) ÷ (1 + {n}%) when notary "
          "fees are deducted."),
        t("**Surface finançable** = budget d'achat ÷ prix médian au m².",
          "**Affordable area** = purchase budget ÷ median price per m²."),
        t("**Effet des prix** = surface obtenue avec le budget de l'année de référence aux prix "
          "actuels, moins la surface de l'année de référence. **Effet des taux** = surface "
          "actuelle, moins cette même surface intermédiaire. Les deux s'additionnent exactement.",
          "**Price effect** = area bought with the baseline-year budget at current prices, minus "
          "the baseline-year area. **Rate effect** = current area minus that same intermediate "
          "area. The two add up exactly."),
        t("**Taux qui permettrait de retrouver la surface de référence** : calculé par "
          "approximations successives (dichotomie) sur la formule du capital empruntable.",
          "**Rate needed to get back the baseline area**: found by successive approximation "
          "(bisection) on the borrowing-capacity formula."),
        t(f"**Taux par défaut** (moyennes annuelles arrondies, Observatoire Crédit Logement / "
          f"CSA) : {_rates()}. Modifiables dans le simulateur.",
          f"**Default rates** (rounded annual averages, Observatoire Crédit Logement / CSA): "
          f"{_rates()}. They can be changed in the simulator."),
    ]


def _dep() -> list[str]:
    return [
        t("**Points et barres par année** : le point est la médiane ; la barre va du 1er quartile "
          "(25 % des ventes sont moins chères) au 3e quartile (75 %).",
          "**Dots and bars by year**: the dot is the median; the bar runs from the 1st quartile "
          "(25% of sales are cheaper) to the 3rd quartile (75%)."),
        t(f"**Histogramme** : nombre de ventes par tranche de {prep.BIN_WIDTH} €/m² ; les 0,5 % "
          "de ventes les plus chères sont masquées pour garder une échelle lisible.",
          f"**Histogram**: number of sales per €{prep.BIN_WIDTH}/m² bracket; the most expensive "
          "0.5% of sales are hidden to keep the scale readable."),
        t("**Comparaison nationale** : même médiane, même période, calculée sur toute la France.",
          "**National comparison**: same median, same period, computed for all of France."),
    ]


def _insights() -> list[str]:
    return [
        t("**Lecture automatique** : moins de 1 % = quasi-stabilité ; moins de 3 % = légère ; "
          "moins de 8 % = nette ; au-delà = forte. « Le marché s'ajuste par les volumes » : ventes "
          "en baisse de plus de 10 % et prix qui bougent de moins de 5 %. Ces seuils sont des "
          "conventions choisies pour ce projet.",
          "**Automatic reading**: under 1% = near stability; under 3% = slight; under 8% = "
          "clear; above = sharp. \"The market adjusts through volumes\": sales down by more than "
          "10% while prices move by less than 5%. These thresholds are conventions chosen for "
          "this project."),
        t("**Lien niveau de prix / évolution** : corrélation des rangs (Spearman) entre le prix de "
          "l'année de référence et l'évolution ; un lien est signalé au-delà de ± 0,3.",
          "**Link between price level and change**: rank correlation (Spearman) between the "
          "baseline price and the change; a link is reported beyond ± 0.3."),
    ]


PAGES = {
    "quand": [_base, _evol, _gap, _when, _insights],
    "ou": [_base, _evol, _quadrants, _gap, _insights],
    "pouvoir-achat": [_credit, _fixed, _insights],
    "departement": [_base, _evol, _dep, _insights],
}


def _bullets(parts) -> str:
    return "\n".join(f"- {b}" for part in parts for b in part())


def render(page: str) -> None:
    """Volet « Comment c'est calculé ? » sous les chiffres d'une page."""
    with st.expander(t("Comment c'est calculé ?", "How is this calculated?"),
                     icon=":material/calculate:"):
        st.markdown(_bullets(PAGES[page]))
        st.caption(t("Toutes les formules sont réunies dans la page *Qualité des données*.",
                     "All formulas are gathered on the *Data quality* page."))


def render_all() -> None:
    """Liste complète, pour la page Qualité des données."""
    st.markdown(t("##### Méthodes de calcul", "##### How the figures are calculated"))
    st.caption(t("Chaque chiffre de l'appli est calculé avec l'une des formules ci-dessous.",
                 "Every figure in the app comes from one of the formulas below."))
    groups = [
        (t("Prix, évolutions et comparaisons", "Prices, changes and comparisons"),
         [_base, _evol, _gap, _when, _quadrants]),
        (t("Simulateurs de pouvoir d'achat", "Affordability simulators"), [_fixed, _credit]),
        (t("Zoom département", "Département focus"), [_dep]),
        (t("Lecture automatique des résultats", "Automatic reading of the results"), [_insights]),
    ]
    for title, parts in groups:
        with st.expander(title):
            st.markdown(_bullets(parts))
