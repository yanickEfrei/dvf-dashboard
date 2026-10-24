"""Pouvoir d'achat immobilier : simulateur de crédit (prix + taux) et simulateur à budget fixe."""
import plotly.graph_objects as go
import streamlit as st

from utils import prep
from utils.i18n import in_region, is_en, keep, region_name, remember, t, wkey
from utils.viz import AXIS, INK_2, _style, fmt_eur, fmt_num, show


def _region_table(f: prep.Filters, budget0: float, budget1: float):
    """Surface achetable par région : budget0 aux prix de y0, budget1 aux prix de y1."""
    cur = prep.by_region(f.types, f.y1, f.deps).set_index("region")
    ref = prep.by_region(f.types, f.y0, f.deps).set_index("region")
    tb = cur.join(ref, rsuffix="_ref").reset_index()
    tb = tb[tb["n"] >= prep.MIN_VENTES]
    tb["m2"], tb["m2_ref"] = budget1 / tb["prix"], budget0 / tb["prix_ref"]
    tb["nom"] = tb["region"].map(region_name)
    return tb.sort_values("m2")


def _region_bars(f: prep.Filters, tb, alt: str) -> None:
    fig = go.Figure()
    if f.y0 != f.y1:
        fig.add_bar(y=tb["nom"], x=tb["m2_ref"], orientation="h", name=str(f.y0),
                    marker_color=AXIS,
                    hovertemplate="<b>%{y}</b><br>" + str(f.y0) + " : %{x:.0f} m²<extra></extra>")
    fig.add_bar(y=tb["nom"], x=tb["m2"], orientation="h", name=prep.period_label(f.y1),
                marker_color="#2a78d6", text=[f"{v:.0f} m²" for v in tb["m2"]],
                textposition="outside", textfont=dict(color=INK_2), cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>" + str(f.y1) + " : %{x:.0f} m²<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05)
    fig.update_xaxes(title=t("Surface achetable (m²)", "Affordable floor area (m²)"))
    show(_style(fig, 80 + 38 * len(tb)), alt)


def _m2(v: float) -> str:
    """+2,3 m² / −16,9 m² (FR) ou +2.3 m² / −16.9 m² (EN)."""
    return ("+" if v >= 0 else "−") + fmt_num(abs(v), 1) + " m²"


def _rate_input(year: int) -> float:
    default = prep.MORTGAGE_RATES.get(year, prep.MORTGAGE_RATES[max(prep.MORTGAGE_RATES)])
    return keep(f"rate_{year}", st.number_input(
        t(f"Taux du crédit en {year} (%)", f"Mortgage rate in {year} (%)"), 0.0, 10.0,
        remember(f"rate_{year}", default), step=0.05, format="%.2f", key=wkey(f"rate_{year}"),
        help=t("Taux moyen hors assurance (Observatoire Crédit Logement / CSA), arrondi. "
               "Modifiez-le pour tester votre propre offre.",
               "Average rate excluding insurance (Observatoire Crédit Logement / CSA), rounded. "
               "Change it to test your own offer.")))


def _credit(f: prep.Filters) -> None:
    st.markdown(t(
        "Un prix plus bas ne rend pas forcément l'achat plus accessible : si le crédit coûte "
        "plus cher, on emprunte moins avec la même mensualité. Ce simulateur compare ce que "
        "permet **la même mensualité** l'année de référence et l'année étudiée.",
        "A lower price does not necessarily make buying more affordable: if credit costs more, "
        "the same monthly payment lets you borrow less. This simulator compares what **the same "
        "monthly payment** buys in the baseline year and in the year studied.",
    ))
    k = prep.kpis(f.types, f.y0, f.y1, f.deps)
    c_in, c_out = st.columns([1, 2], gap="large")
    with c_in, st.container(border=True):
        monthly = keep("monthly", st.slider(
            t("Mensualité maximale", "Maximum monthly payment"), 400, 4_000,
            remember("monthly", 1_200), step=50, key=wkey("monthly"),
            format="€%d" if is_en() else "%d €",
            help=t("Les banques limitent en général la mensualité à 35 % des revenus "
                   "(assurance comprise).",
                   "French banks usually cap the monthly payment at 35% of income "
                   "(insurance included).")))
        years = keep("loan_years", st.segmented_control(
            t("Durée du prêt", "Loan term"), [15, 20, 25], required=True,
            format_func=lambda y: t(f"{y} ans", f"{y} years"),
            default=remember("loan_years", 25), key=wkey("loan_years")))
        down = keep("down", st.slider(
            t("Apport personnel", "Down payment"), 0, 300_000, remember("down", 20_000),
            step=5_000, key=wkey("down"), format="€%d" if is_en() else "%d €"))
        rate0 = _rate_input(f.y0)
        rate1 = _rate_input(f.y1) if f.y1 != f.y0 else rate0
        notary = keep("notary", st.toggle(
            t("Déduire les frais de notaire (≈ 7,5 %)", "Deduct notary fees (≈ 7.5%)"),
            remember("notary", True), key=wkey("notary")))

    fees = 1 + (prep.NOTARY_FEES if notary else 0)
    b0 = (prep.loan_capacity(monthly, rate0, years) + down) / fees
    b1 = (prep.loan_capacity(monthly, rate1, years) + down) / fees
    p0, p1 = k["prix_m2_ref"], k["prix_m2"]
    s0, s1 = b0 / p0, b1 / p1
    effet_prix, effet_taux = b0 / p1 - s0, s1 - b0 / p1

    with c_out:
        if f.y0 == f.y1:
            st.markdown(t(
                f"#### Avec {fmt_eur(monthly)} par mois sur {years} ans, vous pouvez acheter "
                f"un bien d'environ {fmt_eur(round(b1, -3))}, soit **{s1:.0f} m²** ({f.zone}).",
                f"#### With {fmt_eur(monthly)} a month over {years} years, you can buy a home "
                f"worth about {fmt_eur(round(b1, -3))}, i.e. **{s1:.0f} m²** ({f.zone}).",
            ))
            st.info(t("Choisissez deux années différentes pour comparer.",
                      "Pick two different years to compare."))
        else:
            mieux = s1 >= s0
            st.markdown(t(
                f"#### Avec {fmt_eur(monthly)} par mois sur {years} ans, on achète "
                f"**{s1:.0f} m²** en {f.y1} contre **{s0:.0f} m²** en {f.y0} : l'achat est "
                f"{'plus' if mieux else 'moins'} accessible ({f.zone}).",
                f"#### With {fmt_eur(monthly)} a month over {years} years, you buy "
                f"**{s1:.0f} m²** in {f.y1} versus **{s0:.0f} m²** in {f.y0}: buying is "
                f"{'more' if mieux else 'less'} affordable ({f.zone}).",
            ))
            m1, m2, m3 = st.columns(3)
            m1.metric(t(f"Budget d'achat {f.y0}", f"Purchase budget {f.y0}"),
                      fmt_eur(round(b0, -3)), border=True)
            m2.metric(t(f"Budget d'achat {f.y1}", f"Purchase budget {f.y1}"),
                      fmt_eur(round(b1, -3)), fmt_eur(round(b1 - b0, -3)), border=True)
            m3.metric(t(f"Surface achetable {f.y1}", f"Affordable area {f.y1}"),
                      f"{s1:.0f} m²", f"{s1 - s0:+.0f} m²", border=True)

            st.markdown(t("##### D'où vient l'écart ?", "##### Where does the gap come from?"))
            e1, e2, e3 = st.columns(3)
            e1.metric(t("Effet des prix", "Price effect"), _m2(effet_prix),
                      help=t(f"Surface gagnée ou perdue si seuls les prix avaient changé "
                             f"({fmt_eur(p0, '€/m²')} → {fmt_eur(p1, '€/m²')}), à taux {f.y0}.",
                             f"Area gained or lost if only prices had changed "
                             f"({fmt_eur(p0, '€/m²')} → {fmt_eur(p1, '€/m²')}), at {f.y0} rates."))
            e2.metric(t("Effet des taux", "Rate effect"), _m2(effet_taux),
                      help=t(f"Surface gagnée ou perdue à cause du taux "
                             f"({fmt_num(rate0, 2)} % → {fmt_num(rate1, 2)} %), aux prix {f.y1}.",
                             f"Area gained or lost because of the rate "
                             f"({fmt_num(rate0, 2)}% → {fmt_num(rate1, 2)}%), at {f.y1} prices."))
            e3.metric(t("Total", "Total"), _m2(s1 - s0))
            st.caption(t(
                f"Prix médians de la zone : {fmt_eur(p0, '€/m²')} en {f.y0}, "
                f"{fmt_eur(p1, '€/m²')} en {prep.period_label(f.y1)} (mêmes mois). Les deux "
                "effets s'additionnent exactement.",
                f"Median prices in the area: {fmt_eur(p0, '€/m²')} in {f.y0}, "
                f"{fmt_eur(p1, '€/m²')} in {prep.period_label(f.y1)} (same months). The two "
                "effects add up exactly.",
            ))

    tb = _region_table(f, b0, b1)
    st.session_state["_ai_credit"] = dict(
        monthly=monthly, years=years, down=down, rate0=rate0, rate1=rate1, notary=notary,
        b0=b0, b1=b1, s0=s0, s1=s1, effet_prix=effet_prix, effet_taux=effet_taux,
        regions=tb[["region", "m2_ref", "m2"]].round(0).to_csv(index=False).strip(),
        regions_df=tb[["region", "m2_ref", "m2"]])
    if tb.empty:
        return
    st.markdown(t("##### Surface finançable par région", "##### Affordable area by region"))
    _region_bars(f, tb, t(
        f"barres horizontales de la surface finançable avec {fmt_eur(monthly)} par mois sur "
        f"{years} ans dans chaque région, en {f.y1} (bleu, taux {fmt_num(rate1, 2)} %) et en "
        f"{f.y0} (gris, taux {fmt_num(rate0, 2)} %), pour les {f.type_label}.",
        f"horizontal bars of the area affordable with {fmt_eur(monthly)} a month over {years} "
        f"years in each region, in {f.y1} (blue, {fmt_num(rate1, 2)}% rate) and in {f.y0} "
        f"(grey, {fmt_num(rate0, 2)}% rate), for {f.type_label}.",
    ))
    st.caption(t(
        "Calcul : prêt amortissable à taux fixe, hors assurance. Budget = capital empruntable "
        "+ apport" + (", moins les frais de notaire" if notary else "") + ". Surface = budget "
        "÷ prix médian au m². Les régions sont calculées sur l'année entière, d'où de petits "
        "écarts avec les chiffres ci-dessus quand l'année étudiée est partielle.",
        "Method: fixed-rate amortising loan, excluding insurance. Budget = borrowing capacity "
        "+ down payment" + (", minus notary fees" if notary else "") + ". Area = budget ÷ "
        "median price per m². Regions use the whole year, hence small gaps with the figures "
        "above when the year studied is partial.",
    ))


def _fixed_budget(f: prep.Filters) -> None:
    budget = keep("budget", st.slider(
                       t("Votre budget (hors frais de notaire)", "Your budget (excluding notary fees)"),
                       50_000, 800_000, remember("budget", 250_000), step=10_000, key=wkey("budget"),
                       format="€%d" if is_en() else "%d €",
                       help=t("Surface = budget ÷ prix médian au m². C'est un ordre de grandeur : "
                              "le prix réel dépend du quartier, de l'état, de l'étage…",
                              "Floor area = budget ÷ median price per m². It is a rough guide: "
                              "the actual price depends on the area, condition, floor…")))
    tb = _region_table(f, budget, budget)
    if tb.empty:
        st.info(t("Pas assez de ventes pour cette sélection.", "Not enough sales for this selection."))
        return

    best, worst = tb.iloc[-1], tb.iloc[0]
    st.markdown(t(
        f"#### Avec {fmt_eur(budget)}, on obtient environ {worst['m2']:.0f} m² "
        f"{in_region(worst['region'])}, contre {best['m2']:.0f} m² {in_region(best['region'])}.",
        f"#### With {fmt_eur(budget)}, you get about {worst['m2']:.0f} m² "
        f"{in_region(worst['region'])}, versus {best['m2']:.0f} m² {in_region(best['region'])}.",
    ))
    _region_bars(f, tb, t(
        f"barres horizontales de la surface achetable avec {fmt_eur(budget)} dans chaque région, "
        f"en {f.y1} (bleu) et en {f.y0} (gris), pour les {f.type_label}.",
        f"horizontal bars of the floor area affordable with {fmt_eur(budget)} in each region, "
        f"in {f.y1} (blue) and {f.y0} (grey), for {f.type_label}.",
    ))
    st.caption(t("Limite : ce calcul ne tient compte que des prix, à budget identique. L'onglet "
                 "« Avec un crédit » intègre la hausse des taux, qui a réduit la somme qu'un "
                 "ménage peut emprunter.",
                 "Limitation: this only accounts for prices, with the same budget. The “With a "
                 "mortgage” tab includes the rate rise, which shrank the amount a household can "
                 "borrow."))


def render(f: prep.Filters) -> None:
    tab1, tab2 = st.tabs([t("Avec un crédit", "With a mortgage"),
                          t("À budget fixe", "With a fixed budget")])
    with tab1:
        _credit(f)
    with tab2:
        _fixed_budget(f)
