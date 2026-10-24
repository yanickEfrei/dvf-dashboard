"""Accroche, contexte, question, public et mode d'emploi."""
import streamlit as st

from utils import prep
from utils.i18n import t
from utils.viz import fmt_eur, fmt_num


def render() -> None:
    f = prep.story_facts()
    budget = 250_000
    hi, lo = f["dep_max"], f["dep_min"]
    m2_hi, m2_lo = budget / hi["prix"], budget / lo["prix"]
    ratio = fmt_num(hi["prix"] / lo["prix"])

    st.markdown(t(
        f"### Avec {fmt_eur(budget)}, on achète environ **{m2_hi:.0f} m²** dans le département "
        f"le plus cher… et **{m2_lo:.0f} m²** dans le moins cher.",
        f"### With {fmt_eur(budget)}, you can buy about **{m2_hi:.0f} m²** in the most "
        f"expensive département… and **{m2_lo:.0f} m²** in the cheapest one.",
    ))
    st.caption(t(
        f"Prix médians au m² des ventes de {f['ref_year']} (appartements et maisons confondus) : "
        f"{fmt_eur(hi['prix'], '€/m²')} ({hi['label']}) contre {fmt_eur(lo['prix'], '€/m²')} "
        f"({lo['label']}), soit un rapport de 1 à {ratio}.",
        f"Median price per m² of {f['ref_year']} sales (apartments and houses combined): "
        f"{fmt_eur(hi['prix'], '€/m²')} ({hi['label']}) vs {fmt_eur(lo['prix'], '€/m²')} "
        f"({lo['label']}), a ratio of 1 to {ratio}. A département is a French administrative "
        "area, roughly like a county.",
    ))

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown(t(
            """
**Le contexte.** La sortie de la crise du Covid a dopé l'immobilier. Avec des taux
d'emprunt historiquement bas (autour de 1 %) et l'essor du télétravail, beaucoup de ménages
cherchent plus d'espace, souvent une maison avec jardin, parfois loin des grandes villes.
En 2021, environ 1,18 million de logements anciens sont vendus en France, un record, et les
prix grimpent, surtout pour les maisons et en province.

Puis la reprise post-Covid et la crise de l'énergie font flamber l'inflation : la Banque
centrale européenne relève ses taux à partir de juillet 2022. Emprunter coûte d'un coup
beaucoup plus cher, et la capacité d'achat des ménages fond. Les vendeurs, eux, mettent du
temps à baisser leurs prix. Nos données commencent en 2022, c'est-à-dire au sommet de ce
cycle.

**La question.** *Les prix de l'immobilier ont-ils baissé depuis la hausse des taux,
et cette baisse a-t-elle rendu l'achat plus accessible partout en France ?*

1. **Quand ?** Comment ont évolué le prix au m² et le nombre de ventes depuis 2022 ?
2. **Où ?** Quels départements sont les plus chers, lesquels ont le plus baissé ?
3. **Quoi ?** Appartements et maisons ont-ils suivi la même trajectoire ?
   Que peut-on acheter avec une mensualité donnée, maintenant que le crédit coûte plus cher ?
""",
            """
**The context.** The end of the Covid crisis gave the housing market a big boost. With
record-low mortgage rates (around 1%) and the rise of remote work, many households looked
for more space, often a house with a garden, sometimes far from big cities. In 2021, about
1.18 million existing homes were sold in France, a record, and prices climbed, especially
for houses and outside Paris.

Then the post-Covid recovery and the energy crisis sent inflation soaring: the European
Central Bank started raising its rates in July 2022. Borrowing suddenly became much more
expensive, and households' buying power shrank. Sellers, on the other hand, were slow to
lower their prices. Our data starts in 2022, right at the top of this cycle.

**The question.** *Have property prices fallen since rates went up, and has that made
buying a home more affordable everywhere in France?*

1. **When?** How have the price per m² and the number of sales changed since 2022?
2. **Where?** Which départements are the most expensive, and which fell the most?
3. **What?** Did apartments and houses follow the same path?
   What can a given monthly payment buy, now that credit costs more?
""",
        ))
    with c2:
        st.info(t(
            "**Pour qui ?** Un jeune actif qui se demande s'il peut acheter, et où, "
            "ou toute personne curieuse du marché immobilier.\n\n"
            "**Mode d'emploi.** Le menu en haut mène aux différentes pages du récit. Les "
            "filtres de la barre latérale (type de bien, années, régions) s'appliquent à "
            "toutes les pages. Survolez les graphiques pour voir les valeurs exactes.",
            "**Who is it for?** A young professional wondering whether they can buy, and "
            "where, or anyone curious about the housing market.\n\n"
            "**How to use it.** The menu at the top leads to each page of the story. The "
            "sidebar filters (property type, years, regions) apply to every page. Hover "
            "over the charts to see exact values.",
        ), icon=":material/person:")
        st.warning(t(
            "**À garder en tête.** Les chiffres portent sur les ventes **d'un seul logement "
            "dans l'ancien**. L'Alsace, la Moselle et Mayotte ne sont pas couvertes par la "
            "source. Détails dans la page *Qualité des données*.",
            "**Keep in mind.** Figures cover sales of **a single existing home** (no new "
            "builds). Alsace, Moselle and Mayotte are not covered by the source. Details in "
            "the *Data quality* page.",
        ), icon=":material/info:")
