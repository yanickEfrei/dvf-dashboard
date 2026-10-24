"""Comparaisons géographiques, simulateur de budget et zoom sur un département (« Où ? », « Quoi ? »)."""
import plotly.graph_objects as go
import streamlit as st

from utils import prep
from utils.i18n import is_en, keep, region_name, remember, t, type_plural, wkey
from utils.io import load_geojson
from utils.viz import (QUADRANTS, bar_h, change_bars, choropleth, fmt_eur, fmt_int, fmt_pct,
                       histogram, price_volume_scatter, quadrant_of, show, yearly_ranges)

# Indicateurs de la carte : clé interne -> colonne, format, libellés FR / EN
METRICS = {
    "prix": dict(div=False, unit=" €/m²", fr="Prix médian au m²", en="Median price per m²",
                 short_fr="€/m²", short_en="€/m²"),
    "evol_prix": dict(div=True, unit=" %", fr="Évolution du prix au m²",
                      en="Change in price per m²", short_fr="Évol. prix (%)",
                      short_en="Price change (%)"),
    "evol_n": dict(div=True, unit=" %", fr="Évolution du nombre de ventes",
                   en="Change in number of sales", short_fr="Évol. ventes (%)",
                   short_en="Sales change (%)"),
}


def metric_name(key: str) -> str:
    return METRICS[key]["en" if is_en() else "fr"]


def _fmt(key: str):
    return fmt_pct if METRICS[key]["div"] else (lambda v: fmt_eur(v, "€/m²"))


def pick_map_metric() -> str:
    """Sélecteur de variable de la carte (affiché dans la barre latérale sur la page Où ?)."""
    metrics = list(METRICS)
    return keep("map_metric", st.selectbox(
        t("Indicateur de la carte", "Map indicator"), metrics, format_func=metric_name,
        index=metrics.index(remember("map_metric", "evol_prix")), key=wkey("map_metric"),
        help=t("Variable utilisée pour colorer la carte des départements.",
               "Variable used to colour the département map.")))


def _map(f: prep.Filters, d) -> None:
    st.subheader(t("La carte : où les prix bougent-ils ?", "The map: where are prices moving?"))
    col = remember("map_metric", "evol_prix")
    spec, name = METRICS[col], metric_name(col)

    valid = d.dropna(subset=["evol_prix"])
    if f.y0 != f.y1 and len(valid):
        nb = int((valid["evol_prix"] < 0).sum())
        st.markdown(t(
            f"#### Entre {f.y0} et {f.y1}, les prix des {f.type_label} ont baissé dans "
            f"{nb} département{'s' if nb > 1 else ''} sur {len(valid)}.",
            f"#### Between {f.y0} and {f.y1}, {f.type_label} prices fell in {nb} "
            f"département{'s' if nb != 1 else ''} out of {len(valid)}.",
        ))
    st.caption(t(
        f"Indicateur affiché : **{name}** (modifiable dans la barre latérale). "
        f"Année étudiée : {prep.period_label(f.y1)}, référence : {f.y0}. "
        f"Les départements avec moins de {prep.MIN_VENTES} ventes ne sont pas colorés.",
        f"Indicator shown: **{name}** (change it in the sidebar). "
        f"Year studied: {prep.period_label(f.y1)}, baseline: {f.y0}. "
        f"Départements with fewer than {prep.MIN_VENTES} sales are left grey.",
    ))

    title = spec["short_en" if is_en() else "short_fr"]
    if d[col].notna().sum() == 0:
        st.info(t("Pas assez de données pour cet indicateur. Choisissez deux années différentes.",
                  "Not enough data for this indicator. Pick two different years."))
    else:
        fig = choropleth(d, load_geojson(), col, title, diverging=spec["div"], unit=spec["unit"])
        show(fig, t(
            f"carte des départements de métropole colorés selon « {name} » ({f.type_label}). "
            + ("Les tons bleus indiquent une baisse, les rouges une hausse, le gris une "
               "quasi-stabilité." if spec["div"] else
               "Plus le bleu est foncé, plus le prix est élevé."),
            f"map of mainland French départements coloured by “{name}” ({f.type_label}). "
            + ("Blue means a decrease, red an increase, grey almost no change."
               if spec["div"] else "The darker the blue, the higher the price."),
        ))
        st.caption(t("La carte ne montre que la métropole ; les départements d'outre-mer "
                     "figurent dans les classements et le tableau.",
                     "The map only shows mainland France; overseas départements appear in the "
                     "rankings and the table."))



def _biggest_changes(f: prep.Filters, d) -> None:
    """A. Classement des départements où le prix au m² a le plus baissé (ou monté)."""
    st.subheader(t("Où les prix ont-ils le plus baissé ?", "Where did prices fall the most?"))
    valid = d.dropna(subset=["evol_prix"])
    if len(valid) < 4:
        st.info(t("Choisissez deux années différentes pour comparer les prix.",
                  "Pick two different years to compare prices."))
        return
    way = keep("rank_way", st.segmented_control(
        t("Afficher", "Show"), ["baisse", "hausse"], required=True,
        format_func=lambda k: t("Les plus fortes baisses", "Biggest falls") if k == "baisse"
        else t("Les plus fortes hausses", "Biggest rises"),
        default=remember("rank_way", "baisse"), key=wkey("rank_way")))
    n = min(12, len(valid))
    sel = valid.nsmallest(n, "evol_prix") if way == "baisse" else valid.nlargest(n, "evol_prix")

    by_type = prep.evol_by_type(f.y0, f.y1, f.deps)
    sel = sel.join(by_type, on="dep")
    sel["label"] = sel["nom"] + "  " + sel["evol_prix"].map(fmt_pct)
    types = list(f.types)
    first = sel.iloc[0]
    st.markdown(t(
        f"#### {'Plus forte baisse' if way == 'baisse' else 'Plus forte hausse'} : "
        f"{first['nom']} ({fmt_pct(first['evol_prix'])}, de "
        f"{fmt_eur(first['prix_ref'], '€/m²')} à {fmt_eur(first['prix'], '€/m²')}).",
        f"#### {'Biggest fall' if way == 'baisse' else 'Biggest rise'}: "
        f"{first['nom']} ({fmt_pct(first['evol_prix'])}, from "
        f"{fmt_eur(first['prix_ref'], '€/m²')} to {fmt_eur(first['prix'], '€/m²')}).",
    ))
    show(change_bars(sel, types, height=90 + (34 if len(types) > 1 else 26) * n), t(
        f"barres horizontales des {n} départements où le prix médian au m² des {f.type_label} a "
        f"le plus {'baissé' if way == 'baisse' else 'augmenté'} entre {f.y0} et {f.y1}, de "
        f"{first['label']} à {sel['label'].iloc[-1]}"
        + (", avec une barre bleue pour les appartements et une orange pour les maisons."
           if len(types) > 1 else "."),
        f"horizontal bars of the {n} départements where the median price per m² of "
        f"{f.type_label} {'fell' if way == 'baisse' else 'rose'} the most between {f.y0} and "
        f"{f.y1}, from {first['label']} to {sel['label'].iloc[-1]}"
        + (", with a blue bar for apartments and an orange one for houses."
           if len(types) > 1 else "."),
    ))
    st.caption(t(
        f"Le classement suit l'évolution de l'ensemble des {f.type_label} (chiffre à côté du nom). "
        "Les barres détaillent chaque type de bien : il manque quand il y a moins de "
        f"{prep.MIN_VENTES} ventes.",
        f"Ranked by the change for all {f.type_label} (figure next to the name). The bars show "
        f"each property type; a bar is missing when there are fewer than {prep.MIN_VENTES} sales.",
    ))


def _price_vs_volume(f: prep.Filters, d) -> None:
    """B. Prix et volumes : le marché ralentit-il, ou les prix baissent-ils vraiment ?"""
    st.subheader(t("Les prix baissent-ils vraiment, ou le marché ralentit-il seulement ?",
                   "Are prices really falling, or is the market just slowing down?"))
    v = d.dropna(subset=["evol_prix", "evol_n"])
    if len(v) < 4:
        st.info(t("Choisissez deux années différentes pour comparer.",
                  "Pick two different years to compare."))
        return
    k = prep.kpis(f.types, f.y0, f.y1, f.deps)
    ref = (prep.pct(k["prix_m2"], k["prix_m2_ref"]), prep.pct(k["n"], k["n_ref"]))
    ref_name = t("France", "France") if not f.regions else f.zone

    labels = set()
    for c in ("evol_prix", "evol_n"):
        labels |= set(v.nsmallest(3, c)["dep"]) | set(v.nlargest(3, c)["dep"])
    labels |= set(v.nlargest(3, "n")["dep"])

    counts = {q: 0 for q in QUADRANTS}
    for p, n in zip(v["evol_prix"], v["evol_n"]):
        counts[quadrant_of(p, n)] += 1
    q_max = max(counts, key=counts.get)
    st.markdown(t(
        f"#### {counts[q_max]} départements sur {len(v)} sont dans le cas « "
        f"{QUADRANTS[q_max][1].split(' :')[0]} » : {QUADRANTS[q_max][1].split(': ')[1]}.",
        f"#### {counts[q_max]} départements out of {len(v)} are in the “"
        f"{QUADRANTS[q_max][2].split(':')[0]}” case: {QUADRANTS[q_max][2].split(': ')[1]}.",
    ))
    show(price_volume_scatter(v, ref, ref_name, sorted(labels)), t(
        f"nuage de points des départements entre {f.y0} et {f.y1} ({f.type_label}) : en abscisse "
        "l'évolution du nombre de ventes, en ordonnée l'évolution du prix médian au m², taille "
        "du point proportionnelle au nombre de ventes. Les axes à zéro découpent quatre "
        f"situations. Le losange noir représente {ref_name}.",
        f"scatter plot of départements between {f.y0} and {f.y1} ({f.type_label}): x axis is "
        "the change in number of sales, y axis the change in median price per m², dot size is "
        "proportional to the number of sales. Zero lines split four situations. The black "
        f"diamond stands for {ref_name}.",
    ))
    st.caption(t(
        "Comment lire : en bas, les prix ont baissé. À gauche, on vend moins. Un département "
        "en haut à gauche est « bloqué » : les ventes chutent mais les vendeurs ne baissent pas "
        "leurs prix. En bas à droite, la baisse des prix fait revenir les acheteurs.",
        "How to read it: at the bottom, prices fell. On the left, fewer homes are sold. A "
        "département in the top-left is “stuck”: sales drop but sellers do not cut prices. In "
        "the bottom-right, lower prices bring buyers back.",
    ))


def _price_rankings(f: prep.Filters, d) -> None:
    st.subheader(t("Les départements les plus chers et les moins chers",
                   "The most and least expensive départements"))
    col, name, fmt = "prix", metric_name("prix"), _fmt("prix")
    r = d.dropna(subset=[col]).copy()
    r["hover"] = (t("Prix médian : ", "Median price: ") + r["prix"].map(lambda v: fmt_eur(v, "€/m²"))
                  + " · " + r["n"].map(fmt_int) + t(" ventes", " sales"))
    if len(r) >= 4:
        n = min(10, len(r) // 2)
        c1, c2 = st.columns(2, gap="large")
        top, bottom = r.nlargest(n, col), r.nsmallest(n, col)
        with c1:
            st.markdown(t(f"##### Les {n} plus chers ({prep.period_label(f.y1)})",
                          f"##### Top {n} most expensive ({prep.period_label(f.y1)})"))
            show(bar_h(top, col, "label", name, text_fmt=fmt, height=60 + 34 * n),
                 t(f"barres horizontales des {n} départements les plus chers au m², de "
                   f"{top['label'].iloc[0]} ({fmt(top[col].iloc[0])}) à "
                   f"{top['label'].iloc[-1]}.",
                   f"horizontal bars of the {n} most expensive départements per m², from "
                   f"{top['label'].iloc[0]} ({fmt(top[col].iloc[0])}) to "
                   f"{top['label'].iloc[-1]}."))
        with c2:
            st.markdown(t(f"##### Les {n} moins chers ({prep.period_label(f.y1)})",
                          f"##### Top {n} cheapest ({prep.period_label(f.y1)})"))
            show(bar_h(bottom, col, "label", name, text_fmt=fmt, color="#86b6ef",
                       height=60 + 34 * n),
                 t(f"barres horizontales des {n} départements les moins chers au m², de "
                   f"{bottom['label'].iloc[0]} ({fmt(bottom[col].iloc[0])}) à "
                   f"{bottom['label'].iloc[-1]}.",
                   f"horizontal bars of the {n} cheapest départements per m², from "
                   f"{bottom['label'].iloc[0]} ({fmt(bottom[col].iloc[0])}) to "
                   f"{bottom['label'].iloc[-1]}."))

    with st.expander(t("Voir le tableau complet par département", "Show the full table by département")):
        tbl = d.assign(region=d["region"].map(region_name))
        st.dataframe(
            tbl[["label", "region", "prix", "prix_ref", "evol_prix", "n", "n_ref", "evol_n"]]
            .sort_values("prix", ascending=False),
            hide_index=True, width="stretch",
            column_config={
                "label": t("Département", "Département"), "region": t("Région", "Region"),
                "prix": st.column_config.NumberColumn(t(f"Prix {f.y1} (€/m²)", f"Price {f.y1} (€/m²)"), format="%.0f"),
                "prix_ref": st.column_config.NumberColumn(t(f"Prix {f.y0} (€/m²)", f"Price {f.y0} (€/m²)"), format="%.0f"),
                "evol_prix": st.column_config.NumberColumn(t("Évol. prix (%)", "Price change (%)"), format="%+.1f"),
                "n": st.column_config.NumberColumn(t(f"Ventes {f.y1}", f"Sales {f.y1}"), format="%d"),
                "n_ref": st.column_config.NumberColumn(t(f"Ventes {f.y0}", f"Sales {f.y0}"), format="%d"),
                "evol_n": st.column_config.NumberColumn(t("Évol. ventes (%)", "Sales change (%)"), format="%+.1f"),
            })


def _pick_dep(f: prep.Filters) -> str:
    deps_choice = list(f.deps or prep.DEP_NAMES)
    saved = remember("focus_dep", "75")
    if saved not in deps_choice:
        saved = "75" if "75" in deps_choice else deps_choice[0]
    return keep("focus_dep", st.selectbox(
        t("Département à explorer", "Département to explore"), deps_choice,
        index=deps_choice.index(saved), format_func=prep.dep_label,
        key=wkey("focus_dep") + "_" + "-".join(sorted(f.regions))))


def _focus_dep(f: prep.Filters) -> None:
    c1, _ = st.columns([1, 2])
    with c1:
        dep = _pick_dep(f)
    st.subheader(prep.dep_label(dep))
    y = prep.dep_yearly(dep, prep.TYPES)
    if y.empty:
        st.info(t("Pas de ventes pour ce département dans la source (Alsace-Moselle et Mayotte "
                  "ne sont pas couverts par DVF).",
                  "No sales for this département in the source (Alsace-Moselle and Mayotte are "
                  "not covered by DVF)."))
        return

    app = y[(y["type"] == "Appartement") & (y["n"] >= prep.MIN_VENTES)]
    mai = y[(y["type"] == "Maison") & (y["n"] >= prep.MIN_VENTES)]
    msgs = []
    for typ, s in [("Appartement", app), ("Maison", mai)]:
        if len(s) >= 2:
            pk, last = s.loc[s["median"].idxmax()], s.iloc[-1]
            ch = fmt_pct(prep.pct(last["median"], pk["median"]))
            msgs.append(t(
                f"les {type_plural(typ)} valent {fmt_eur(last['median'], '€/m²')} en "
                f"{last['periode']} ({ch} par rapport au pic de {int(pk['annee'])})",
                f"{type_plural(typ)} are worth {fmt_eur(last['median'], '€/m²')} in "
                f"{last['periode']} ({ch} vs the {int(pk['annee'])} peak)"))
    if msgs:
        st.markdown(t("#### Dans ce département, ", "#### In this département, ")
                    + t(" ; ", "; ").join(msgs) + ".")

    show(yearly_ranges(y[y["n"] >= prep.MIN_VENTES]), t(
        f"deux panneaux côte à côte (appartements, maisons) pour {prep.dep_label(dep)} : pour "
        "chaque année, un point pour le prix médian au m² et une barre verticale qui va du 1er "
        "quartile au 3e quartile (la moitié centrale des ventes).",
        f"two side-by-side panels (apartments, houses) for {prep.dep_label(dep)}: for each year, "
        "a dot for the median price per m² and a vertical bar from the 1st to the 3rd quartile "
        "(the middle half of sales).",
    ))
    partial = [str(a) for a in y["annee"].unique() if prep.is_partial(int(a))]
    st.caption(t("Le point est la médiane ; la barre couvre la moitié centrale des ventes "
                 "(du 1er au 3e quartile). Une barre longue = des prix très dispersés.",
                 "The dot is the median; the bar covers the middle half of sales (1st to 3rd "
                 "quartile). A long bar means widely spread prices.")
               + (t(" * {} : année partielle ({}).", " * {}: partial year ({}).").format(
                   ", ".join(partial), prep.period_label(int(partial[0]))) if partial else ""))

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown(t(f"##### Répartition des prix au m² en {prep.period_label(f.y1)}",
                      f"##### Distribution of prices per m² in {prep.period_label(f.y1)}"))
        h = prep.dep_hist(dep, f.y1, f.types)
        if h.empty:
            st.info(t("Pas de ventes pour cette année.", "No sales for this year."))
        else:
            tot = h.groupby("bin")["n"].sum()
            cut = tot[tot.cumsum() <= tot.sum() * 0.995].index.max()
            show(histogram(h[h["bin"] <= cut], prep.BIN_WIDTH), t(
                f"histogramme du nombre de ventes par tranche de {prep.BIN_WIDTH} €/m² en {f.y1} "
                f"dans {prep.dep_label(dep)}, pour les {f.type_label}.",
                f"histogram of the number of sales per €{prep.BIN_WIDTH}/m² bracket in {f.y1} "
                f"in {prep.dep_label(dep)}, for {f.type_label}.",
            ))
    with c2:
        typ = f.type_choice if f.type_choice in prep.TYPES else (
            "Appartement" if len(app) and (len(mai) == 0 or app["n"].sum() > mai["n"].sum())
            else "Maison")
        st.markdown(t(f"##### Communes les plus chères ({type_plural(typ)}, {f.y1})",
                      f"##### Most expensive towns ({type_plural(typ)}, {f.y1})"))
        c = prep.communes(dep, typ, f.y0, f.y1)
        if c.empty:
            st.info(t(f"Aucune commune avec au moins {prep.MIN_VENTES_COMMUNE} ventes.",
                      f"No town with at least {prep.MIN_VENTES_COMMUNE} sales."))
        else:
            st.dataframe(
                c[["commune", "prix_m2_median", "evol", "n_ventes"]].head(15),
                hide_index=True, width="stretch",
                column_config={
                    "commune": t("Commune", "Town"),
                    "prix_m2_median": st.column_config.NumberColumn("€/m²", format="%.0f"),
                    "evol": st.column_config.NumberColumn(f"vs {f.y0} (%)", format="%+.1f"),
                    "n_ventes": st.column_config.NumberColumn(t("Ventes", "Sales"), format="%d"),
                })
            st.caption(t(f"Communes avec au moins {prep.MIN_VENTES_COMMUNE} ventes "
                         "(fiabilité des médianes et confidentialité).",
                         f"Towns with at least {prep.MIN_VENTES_COMMUNE} sales (reliable medians "
                         "and privacy)."))


def render_where(f: prep.Filters) -> None:
    """Page « Où ? » : carte, plus fortes baisses, prix vs volumes, classements."""
    d = prep.by_dep(f.types, f.y0, f.y1, f.deps)
    _map(f, d)
    st.divider()
    _biggest_changes(f, d)
    st.divider()
    _price_vs_volume(f, d)
    st.divider()
    _price_rankings(f, d)


def render_focus(f: prep.Filters) -> None:
    """Page « Zoom département »."""
    _focus_dep(f)
