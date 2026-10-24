"""Enseignements, implications et pistes (calculés sur toute la France, indépendamment des filtres)."""
import streamlit as st

from utils import prep
from utils.i18n import t
from utils.viz import fmt_eur, fmt_int, fmt_num, fmt_pct


def render() -> None:
    st.subheader(t("Ce qu'il faut retenir", "Key takeaways"))
    f = prep.story_facts()
    if "first" not in f:
        st.info(t("Il faut au moins deux années complètes pour tirer des conclusions.",
                  "At least two full years are needed to draw conclusions."))
        return

    first, last, low = f["first"], f["last"], f["vol_min_year"]
    med, vol = f["median"], f["volume"]
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        if f["vol_drop"] < -10:
            st.markdown(t("##### 1. Le marché s'est d'abord bloqué",
                          "##### 1. The market stalled first"))
        else:
            st.markdown(t("##### 1. Le nombre de ventes a peu varié",
                          "##### 1. The number of sales barely changed"))
        if low in (first, last):
            ch = fmt_pct(prep.pct(vol[last], vol[first]))
            txt = t(f"Le nombre de ventes retenues passe de **{fmt_int(vol[first])}** en {first} à "
                    f"**{fmt_int(vol[last])}** en {last} ({ch}).",
                    f"The number of sales kept goes from **{fmt_int(vol[first])}** in {first} to "
                    f"**{fmt_int(vol[last])}** in {last} ({ch}).")
        else:
            txt = t(f"Le nombre de ventes retenues passe de **{fmt_int(vol[first])}** en {first} "
                    f"à **{fmt_int(vol[low])}** en {low} ({fmt_pct(f['vol_drop'])}), puis atteint "
                    f"**{fmt_int(vol[last])}** en {last} ({fmt_pct(f['vol_rebound'])}).",
                    f"The number of sales kept falls from **{fmt_int(vol[first])}** in {first} "
                    f"to **{fmt_int(vol[low])}** in {low} ({fmt_pct(f['vol_drop'])}), then reaches "
                    f"**{fmt_int(vol[last])}** in {last} ({fmt_pct(f['vol_rebound'])}).")
        st.markdown(txt)

    with c2:
        prix_max = max(abs(v) for v in f["prix_evol"].values())
        if prix_max < abs(f["vol_drop"]) / 2:
            st.markdown(t("##### 2. Les prix ont bien moins bougé que les volumes",
                          "##### 2. Prices moved far less than volumes"))
            morale = t("Quand le crédit se renchérit, on vend d'abord moins, avant de vendre moins cher.",
                       "When credit gets more expensive, people first sell less, before selling cheaper.")
        else:
            st.markdown(t("##### 2. Les prix ont bougé autant que les volumes",
                          "##### 2. Prices moved as much as volumes"))
            morale = t("Prix et volumes ont évolué dans des proportions comparables.",
                       "Prices and volumes changed in similar proportions.")
        a0, a1 = fmt_eur(med[first]["Appartement"], "€/m²"), fmt_eur(med[last]["Appartement"], "€/m²")
        st.markdown(t(
            f"Entre {first} et {last}, le prix médian au m² évolue de "
            f"**{fmt_pct(f['prix_evol']['Appartement'])}** pour les appartements ({a0} → {a1}) et "
            f"de **{fmt_pct(f['prix_evol']['Maison'])}** pour les maisons. ",
            f"Between {first} and {last}, the median price per m² changes by "
            f"**{fmt_pct(f['prix_evol']['Appartement'])}** for apartments ({a0} → {a1}) and by "
            f"**{fmt_pct(f['prix_evol']['Maison'])}** for houses. ",
        ) + morale)

    with c3:
        st.markdown(t("##### 3. La géographie compte plus que le calendrier",
                      "##### 3. Location matters more than timing"))
        hi, lo = f["dep_max"], f["dep_min"]
        ratio = fmt_num(hi["prix"] / lo["prix"])
        st.markdown(t(
            f"En {f['ref_year']}, un m² coûte **{fmt_eur(hi['prix'])}** dans le département le plus "
            f"cher ({hi['label']}) contre **{fmt_eur(lo['prix'])}** dans le moins cher "
            f"({lo['label']}), un rapport de 1 à {ratio}. Aucune baisse conjoncturelle ne comble "
            "un tel écart.",
            f"In {f['ref_year']}, one m² costs **{fmt_eur(hi['prix'])}** in the most expensive "
            f"département ({hi['label']}) versus **{fmt_eur(lo['prix'])}** in the cheapest "
            f"({lo['label']}), a ratio of 1 to {ratio}. No cyclical dip can close such a gap.",
        ))

    st.success(t(
        "**Pour un acheteur.** Le bon moment compte moins que le bon endroit : d'un département à "
        "l'autre, la surface accessible pour un même budget varie bien plus que d'une année à "
        "l'autre. La carte et les simulateurs de la page *Pouvoir d'achat* aident à repérer les zones où les prix ont reculé ou "
        "restent abordables.\n\n"
        "**Pour les décideurs.** Un marché où l'on vend peu est un marché où l'on déménage peu : "
        "le blocage des ventes pèse sur la mobilité professionnelle et sur les recettes des "
        "collectivités (droits de mutation).",
        "**For buyers.** The right place matters more than the right time: for the same budget, "
        "the floor area you can afford varies far more from one département to another than "
        "from one year to the next. The map and the simulators on the *Affordability* page help spot areas where prices have "
        "dropped or remain affordable.\n\n"
        "**For policymakers.** A market with few sales is a market where few people move: "
        "stalled sales weigh on job mobility and on local authorities' revenue (property "
        "transfer taxes).",
    ), icon=":material/lightbulb:")

    st.markdown(t("##### Pour aller plus loin", "##### Going further"))
    st.markdown(t(
        """
- Croiser le simulateur de crédit avec les **revenus** par territoire (INSEE) pour mesurer
  le *taux d'effort* réel des ménages de chaque département.
- Utiliser la version **géolocalisée** de DVF pour descendre au quartier.
- Comparer avec les **indices Notaires-INSEE**, qui corrigent les différences de qualité
  des biens vendus d'une année à l'autre.
""",
        """
- Combine the mortgage simulator with **incomes** by area (INSEE) to measure households'
  real *housing cost burden* in each département.
- Use the **geolocated** version of DVF to zoom down to the neighbourhood.
- Compare with the **Notaires-INSEE indices**, which adjust for differences in the quality
  of homes sold from one year to the next.
""",
    ))
    st.caption(t("Ces conclusions portent sur toute la France et tous les logements, quels que "
                 "soient les filtres. Elles décrivent des évolutions simultanées, pas des causes "
                 "démontrées.",
                 "These conclusions cover all of France and all homes, whatever the filters. "
                 "They describe changes that happened at the same time, not proven causes."))
