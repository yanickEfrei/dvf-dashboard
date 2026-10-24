"""Lecture automatique des résultats : des règles transforment les chiffres de la page en texte.

Aucune IA ni service externe : chaque phrase est calculée à partir des mêmes données que les
graphiques, avec des seuils fixes (ex. « nette » baisse au-delà de 3 %, « forte » au-delà de 8 %).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import prep
from utils.i18n import in_region, month_label, month_name, t, type_plural
from utils.viz import QUADRANTS, fmt_eur, fmt_num, fmt_pct, quadrant_of


def _move(v: float, fem: bool = True) -> tuple[str, str]:
    """Qualifie une évolution en % : (« légère hausse », « slight rise »)…"""
    a = abs(v)
    if a < 1:
        return t("quasi-stabilité", "near stability"), "stable"
    size_fr = "légère" if a < 3 else "nette" if a < 8 else "forte"
    size_en = "slight" if a < 3 else "clear" if a < 8 else "sharp"
    return (t(f"{size_fr} {'hausse' if v > 0 else 'baisse'}",
              f"{size_en} {'rise' if v > 0 else 'fall'}"), "up" if v > 0 else "down")


def _signed(v: float, unit: str = " m²") -> str:
    return ("+" if v >= 0 else "−") + fmt_num(abs(v), 1) + unit


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


# ---------------------------------------------------------------- Quand ?
def _when(f: prep.Filters) -> list[str]:
    out = []
    k = prep.kpis(f.types, f.y0, f.y1, f.deps)
    ep, en = prep.pct(k["prix_m2"], k["prix_m2_ref"]), prep.pct(k["n"], k["n_ref"])
    if f.y0 != f.y1 and ep == ep and en == en:
        mp, _ = _move(ep)
        mn, _ = _move(en)
        out.append(t(
            f"**Prix** : {mp} du prix médian au m² ({fmt_pct(ep)}) entre {f.y0} et {f.y1}. "
            f"**Ventes** : {mn} ({fmt_pct(en)}).",
            f"**Prices**: {mp} in the median price per m² ({fmt_pct(ep)}) between {f.y0} and "
            f"{f.y1}. **Sales**: {mn} ({fmt_pct(en)})."))
        if en < -10 and abs(ep) < 5:
            out.append(t(
                "**Diagnostic** : le marché s'ajuste par les volumes, pas par les prix. On vend "
                "beaucoup moins, mais à peu près au même prix : les vendeurs préfèrent attendre "
                "plutôt que baisser, et les acheteurs, freinés par le crédit, renoncent.",
                "**Diagnosis**: the market adjusts through volumes, not prices. Far fewer homes "
                "are sold, at roughly the same price: sellers would rather wait than cut, and "
                "buyers, held back by credit, give up."))
        elif ep <= -5:
            out.append(t("**Diagnostic** : les prix corrigent réellement, au-delà d'un simple "
                         "ralentissement du marché.",
                         "**Diagnosis**: prices are genuinely correcting, beyond a mere "
                         "slowdown of the market."))
        elif ep < 0 and en > 5:
            out.append(t("**Diagnostic** : la baisse des prix fait revenir les acheteurs.",
                         "**Diagnosis**: lower prices are bringing buyers back."))
        elif ep >= 5 and en >= 0:
            out.append(t("**Diagnostic** : marché dynamique, les prix et les ventes progressent.",
                         "**Diagnosis**: a buoyant market, with prices and sales both rising."))

    m = prep.monthly(f.types, f.y0, f.y1, f.deps)
    for typ in f.types:
        g = m[m["type"] == typ].sort_values("mois")
        if len(g) < 6:
            continue
        pk, last = g.loc[g["prix_m2_median"].idxmax()], g.iloc[-1]
        if pk["mois"] == last["mois"]:
            out.append(t(f"Pour les {type_plural(typ)}, le prix médian mensuel est à son plus "
                         f"haut au dernier mois disponible ({month_label(last['mois'])}).",
                         f"For {type_plural(typ)}, the monthly median price is at its highest in "
                         f"the latest month available ({month_label(last['mois'])})."))
        else:
            ch = fmt_pct(prep.pct(last["prix_m2_median"], pk["prix_m2_median"]))
            out.append(t(
                f"Pour les {type_plural(typ)}, le prix médian mensuel a culminé en "
                f"{month_label(pk['mois'])} ({fmt_eur(pk['prix_m2_median'], '€/m²')}) ; en "
                f"{month_label(last['mois'])}, il est à {fmt_eur(last['prix_m2_median'], '€/m²')} "
                f"({ch} par rapport à ce pic).",
                f"For {type_plural(typ)}, the monthly median price peaked in "
                f"{month_label(pk['mois'])} ({fmt_eur(pk['prix_m2_median'], '€/m²')}); in "
                f"{month_label(last['mois'])}, it stands at "
                f"{fmt_eur(last['prix_m2_median'], '€/m²')} ({ch} vs that peak)."))

    full = [y for y in range(f.y0, f.y1 + 1) if not prep.is_partial(y)]
    if full:
        s = m[m["mois"].dt.year.isin(full)].groupby(m["mois"].dt.month)["n_ventes"].sum()
        if len(s) == 12:
            out.append(t(
                f"**Saisonnalité** : les ventes sont au plus haut en {month_name(int(s.idxmax()))} "
                f"et au plus bas en {month_name(int(s.idxmin()))} : comparer deux mois différents "
                "sans en tenir compte fausse la lecture.",
                f"**Seasonality**: sales are highest in {month_name(int(s.idxmax()))} and lowest "
                f"in {month_name(int(s.idxmin()))}: comparing two different months without "
                "accounting for this is misleading."))
    if f.y0 != f.y1 and ep == ep:
        out.append(t(
            "**Pour un acheteur** : "
            + ("les prix ont un peu reculé, " if ep < 0 else "les prix n'ont pas baissé, ")
            + "mais le coût du crédit compte autant que le prix : voir la page *Pouvoir d'achat*.",
            "**For a buyer**: "
            + ("prices have eased a little, " if ep < 0 else "prices have not fallen, ")
            + "but the cost of credit matters as much as the price: see the *Affordability* page."))
    return out


# ---------------------------------------------------------------- Où ?
def _where(f: prep.Filters) -> list[str]:
    out = []
    d = prep.by_dep(f.types, f.y0, f.y1, f.deps)
    v = d.dropna(subset=["evol_prix", "evol_n"])
    if len(v) >= 4:
        nb = int((v["evol_prix"] < 0).sum())
        out.append(t(
            f"Les prix baissent dans **{nb} départements sur {len(v)}** ; l'évolution médiane d'un "
            f"département est de {fmt_pct(v['evol_prix'].median())}. Plus forte baisse : "
            f"{v.loc[v['evol_prix'].idxmin(), 'label']} ({fmt_pct(v['evol_prix'].min())}) ; plus "
            f"forte hausse : {v.loc[v['evol_prix'].idxmax(), 'label']} "
            f"({fmt_pct(v['evol_prix'].max())}).",
            f"Prices fall in **{nb} départements out of {len(v)}**; the median département "
            f"change is {fmt_pct(v['evol_prix'].median())}. Biggest fall: "
            f"{v.loc[v['evol_prix'].idxmin(), 'label']} ({fmt_pct(v['evol_prix'].min())}); "
            f"biggest rise: {v.loc[v['evol_prix'].idxmax(), 'label']} "
            f"({fmt_pct(v['evol_prix'].max())})."))

        r = v["prix_ref"].rank().corr(v["evol_prix"].rank())
        if r < -0.3:
            out.append(t(
                "Les départements **les plus chers sont plutôt ceux où les prix ont le plus "
                "reculé** : les écarts de prix se resserrent un peu.",
                "The **most expensive départements tend to be those where prices fell the "
                "most**: price gaps are narrowing slightly."))
        elif r > 0.3:
            out.append(t("Les départements les plus chers sont plutôt ceux où les prix ont le "
                         "plus monté : les écarts se creusent.",
                         "The most expensive départements tend to be those where prices rose "
                         "the most: gaps are widening."))
        else:
            out.append(t("Pas de lien net entre le niveau des prix et leur évolution : chers "
                         "ou bon marché, les départements ont évolué de façon dispersée.",
                         "No clear link between price levels and price changes: expensive or "
                         "cheap, départements moved in scattered ways."))

        reg = v.groupby("region")["evol_prix"].agg(["mean", "size"])
        reg = reg[reg["size"] >= 2]
        if len(reg) >= 2:
            lo = reg["mean"].idxmin()
            out.append(t(
                f"Par région, la baisse est la plus marquée {in_region(lo)} "
                f"({fmt_pct(reg.loc[lo, 'mean'])} en moyenne par département).",
                f"By region, the fall is steepest {in_region(lo)} "
                f"({fmt_pct(reg.loc[lo, 'mean'])} on average per département)."))

        counts = pd.Series([quadrant_of(p, n) for p, n in zip(v["evol_prix"], v["evol_n"])]
                           ).value_counts()
        q = counts.idxmax()
        name_fr, name_en = QUADRANTS[q][1], QUADRANTS[q][2]
        out.append(t(
            f"Croisement prix × ventes : le cas le plus fréquent est « {name_fr} » "
            f"({counts[q]} départements).",
            f"Prices × sales: the most common case is “{name_en}” ({counts[q]} départements)."))

    p = d.dropna(subset=["prix"])
    if len(p) >= 2:
        hi, lo = p.loc[p["prix"].idxmax()], p.loc[p["prix"].idxmin()]
        out.append(t(
            f"Un m² coûte **{fmt_num(hi['prix'] / lo['prix'], 1)} fois plus cher** dans "
            f"{hi['label']} que dans {lo['label']} : la géographie pèse bien plus que "
            "l'évolution récente des prix.",
            f"One m² costs **{fmt_num(hi['prix'] / lo['prix'], 1)} times more** in {hi['label']} "
            f"than in {lo['label']}: location matters far more than recent price changes."))
    return out


# ---------------------------------------------------------------- Pouvoir d'achat
def _rate_for(target: float, monthly: float, years: int) -> float | None:
    """Taux (%) auquel la mensualité permet d'emprunter `target` (None si impossible)."""
    if prep.loan_capacity(monthly, 0, years) < target:
        return None
    lo, hi = 0.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if prep.loan_capacity(monthly, mid, years) > target else (lo, mid)
    return lo


def _budget(f: prep.Filters) -> list[str]:
    c = st.session_state.get("_ai_credit")
    if not c or f.y0 == f.y1:
        return []
    out = []
    s0, s1, ep, et = c["s0"], c["s1"], c["effet_prix"], c["effet_taux"]
    out.append(t(
        f"Avec la même mensualité, la surface finançable passe de **{fmt_num(s0)} m²** à "
        f"**{fmt_num(s1)} m²** ({fmt_pct(prep.pct(s1, s0))}).",
        f"With the same monthly payment, the affordable area goes from **{fmt_num(s0)} m²** to "
        f"**{fmt_num(s1)} m²** ({fmt_pct(prep.pct(s1, s0))})."))
    if abs(et) > abs(ep):
        out.append(t(
            f"**C'est surtout le crédit qui a changé la donne** : l'effet des taux "
            f"({_signed(et)}) pèse plus que l'effet des prix ({_signed(ep)}).",
            f"**Credit is what changed the picture**: the rate effect ({_signed(et)}) "
            f"outweighs the price effect ({_signed(ep)})."))
    else:
        out.append(t(
            f"**Ce sont surtout les prix qui ont changé la donne** : l'effet des prix "
            f"({_signed(ep)}) pèse plus que l'effet des taux ({_signed(et)}).",
            f"**Prices are what changed the picture**: the price effect ({_signed(ep)}) "
            f"outweighs the rate effect ({_signed(et)})."))

    if s1 < s0:
        fees = 1 + (prep.NOTARY_FEES if c["notary"] else 0)
        p1 = c["b1"] / s1
        need = s0 * p1 * fees - c["down"]
        r = _rate_for(need, c["monthly"], c["years"])
        drop = prep.pct(c["b1"] / s0, p1)
        if r is not None:
            out.append(t(
                f"Pour retrouver les {fmt_num(s0)} m² de {f.y0} aux prix actuels, il faudrait un "
                f"taux d'environ **{fmt_num(r, 2)} %** (contre {fmt_num(c['rate1'], 2)} % "
                f"retenu), ou bien une baisse des prix d'environ **{fmt_num(abs(drop))} %**.",
                f"To get back the {fmt_num(s0)} m² of {f.y0} at today's prices, you would need a "
                f"rate of about **{fmt_num(r, 2)}%** (vs {fmt_num(c['rate1'], 2)}% used here), "
                f"or prices about **{fmt_num(abs(drop))}%** lower."))
        else:
            out.append(t(
                f"Même à taux zéro, on ne retrouverait pas les {fmt_num(s0)} m² de {f.y0} : il "
                f"faudrait une baisse des prix d'environ **{fmt_num(abs(drop))} %**.",
                f"Even at a zero rate, you would not get back the {fmt_num(s0)} m² of {f.y0}: "
                f"prices would need to be about **{fmt_num(abs(drop))}%** lower."))

    reg = c.get("regions_df")
    if reg is not None and len(reg) >= 2:
        ch = (reg["m2"] / reg["m2_ref"] - 1) * 100
        gain = reg.loc[ch > 0, "region"].tolist()
        worst = reg.loc[ch.idxmin(), "region"]
        if not gain:
            out.append(t(
                f"**Aucune région n'y gagne** ; la perte relative est la plus forte "
                f"{in_region(worst)} ({fmt_pct(ch.min())}).",
                f"**No region comes out ahead**; the relative loss is largest {in_region(worst)} "
                f"({fmt_pct(ch.min())})."))
        else:
            out.append(t(
                f"Régions où l'on achète plus grand qu'en {f.y0} : {', '.join(gain)}.",
                f"Regions where you can buy more space than in {f.y0}: {', '.join(gain)}."))
    out.append(t("Rappel : le calcul suppose un taux fixe hors assurance et la même mensualité ; "
                 "il ne tient pas compte de l'évolution des salaires.",
                 "Reminder: the calculation assumes a fixed rate excluding insurance and the same "
                 "monthly payment; it ignores changes in wages."))
    return out


# ---------------------------------------------------------------- Zoom département
def _dep(f: prep.Filters) -> list[str]:
    dep = st.session_state.get("_focus_dep", "75")
    out = []
    for typ in f.types:
        kd = prep.kpis((typ,), f.y0, f.y1, (dep,))
        if kd["n"] < prep.MIN_VENTES or kd["n_ref"] < prep.MIN_VENTES:
            continue
        kn = prep.kpis((typ,), f.y0, f.y1, None)
        ratio = kd["prix_m2"] / kn["prix_m2"]
        if ratio >= 2:
            pos_fr = f"soit {fmt_num(ratio, 1)} fois la médiane nationale"
            pos_en = f"i.e. {fmt_num(ratio, 1)} times the national median"
        else:
            gap = (ratio - 1) * 100
            pos_fr = (f"soit {fmt_num(abs(gap))} % {'au-dessus' if gap >= 0 else 'en dessous'} "
                      "de la médiane nationale")
            pos_en = f"i.e. {fmt_num(abs(gap))}% {'above' if gap >= 0 else 'below'} the national median"
        line = t(
            f"**{_cap(type_plural(typ))}** : {fmt_eur(kd['prix_m2'], '€/m²')} en {f.y1}, {pos_fr}.",
            f"**{_cap(type_plural(typ))}**: {fmt_eur(kd['prix_m2'], '€/m²')} in {f.y1}, {pos_en}.")
        if f.y0 != f.y1:
            ed = prep.pct(kd["prix_m2"], kd["prix_m2_ref"])
            en = prep.pct(kn["prix_m2"], kn["prix_m2_ref"])
            better = ed < en
            line += t(
                f" Depuis {f.y0} : {fmt_pct(ed)}, contre {fmt_pct(en)} en France, donc une "
                f"évolution {'plus favorable' if better else 'moins favorable'} aux acheteurs "
                "que la moyenne.",
                f" Since {f.y0}: {fmt_pct(ed)}, vs {fmt_pct(en)} in France, so a trend "
                f"{'more' if better else 'less'} favourable to buyers than average.")
        out.append(line)

    y = prep.dep_yearly(dep, prep.TYPES)
    last = y[(y["annee"] == f.y1) & (y["n"] >= prep.MIN_VENTES) & y["type"].isin(f.types)]
    for _, row in last.iterrows():
        spread = (row["q3"] - row["q1"]) / row["median"] * 100
        if spread > 50:
            out.append(t(
                f"Les prix des {type_plural(row['type'])} sont très dispersés : la moitié "
                f"centrale des ventes va de {fmt_eur(row['q1'], '€/m²')} à "
                f"{fmt_eur(row['q3'], '€/m²')}. La commune et l'état du bien comptent beaucoup.",
                f"{_cap(type_plural(row['type']))} prices are widely spread: the middle half of "
                f"sales ranges from {fmt_eur(row['q1'], '€/m²')} to {fmt_eur(row['q3'], '€/m²')}. "
                "The town and the condition of the home matter a lot."))

    typ = f.type_choice if f.type_choice in prep.TYPES else "Appartement"
    c = prep.communes(dep, typ, f.y0, f.y1)
    if len(c) >= 3:
        top, bot = c.iloc[0], c.iloc[-1]
        out.append(t(
            f"Entre communes ({type_plural(typ)}), le prix médian va de "
            f"{fmt_eur(bot['prix_m2_median'], '€/m²')} ({bot['commune']}) à "
            f"{fmt_eur(top['prix_m2_median'], '€/m²')} ({top['commune']}), soit "
            f"{fmt_num(top['prix_m2_median'] / bot['prix_m2_median'], 1)} fois plus.",
            f"Across towns ({type_plural(typ)}), the median price ranges from "
            f"{fmt_eur(bot['prix_m2_median'], '€/m²')} ({bot['commune']}) to "
            f"{fmt_eur(top['prix_m2_median'], '€/m²')} ({top['commune']}), i.e. "
            f"{fmt_num(top['prix_m2_median'] / bot['prix_m2_median'], 1)} times more."))
        e = c.dropna(subset=["evol"])
        if len(e) >= 3 and f.y0 != f.y1:
            w = e.loc[e["evol"].idxmin()]
            out.append(t(f"Plus forte baisse parmi les communes suivies : {w['commune']} "
                         f"({fmt_pct(w['evol'])} depuis {f.y0}).",
                         f"Biggest fall among the towns tracked: {w['commune']} "
                         f"({fmt_pct(w['evol'])} since {f.y0})."))
    return out


BUILDERS = {"quand": _when, "ou": _where, "pouvoir-achat": _budget, "departement": _dep}


def render(page: str, f: prep.Filters) -> None:
    bullets = BUILDERS[page](f)
    if not bullets:
        return
    st.divider()
    with st.container(border=True):
        st.markdown(t("#### :material/insights: Lecture automatique des résultats",
                      "#### :material/insights: Automatic reading of the results"))
        st.caption(t(
            "⚠️ Interprétation générée automatiquement à partir des chiffres de cette page, par "
            "des règles fixes (pas d'IA). Elle simplifie la réalité et peut passer à côté de "
            "nuances : à prendre avec recul, et à vérifier sur les graphiques.",
            "⚠️ Interpretation generated automatically from the figures on this page, using "
            "fixed rules (no AI). It simplifies reality and can miss nuances: take it with a "
            "pinch of salt and check it against the charts.",
        ))
        st.markdown("\n".join(f"- {b}" for b in bullets))
