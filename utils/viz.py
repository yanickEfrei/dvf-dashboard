"""Fonctions graphiques : un seul style pour toute l'appli (couleurs, axes, survol).

Palette validée daltonisme (bleu / orange pour les deux types de bien,
rampe bleue séquentielle, divergente bleu <-> rouge avec milieu gris).
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.i18n import is_en, month_label, t, type_name

# ---- Couleurs -------------------------------------------------------------
TYPE_COLORS = {"Appartement": "#2a78d6", "Maison": "#eb6834"}
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = [[0, "#1c5cab"], [0.25, "#86b6ef"], [0.5, "#f0efec"],
             [0.75, "#f0a08a"], [1, "#b8322f"]]
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

CONFIG = {"displaylogo": False,
          "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def fmt_num(x: float, decimals: int = 0) -> str:
    """1 234,5 (FR) ou 1,234.5 (EN)."""
    if x is None or pd.isna(x):
        return "–"
    txt = f"{x:,.{decimals}f}"
    if is_en():
        return txt
    return txt.replace(",", "\u202f").replace(".", ",")


def fmt_int(x: float) -> str:
    return fmt_num(x, 0)


def fmt_eur(x: float, unit: str = "€") -> str:
    """250 000 € / 3 250 €/m² (FR) ou €250,000 / €3,250/m² (EN)."""
    if x is None or pd.isna(x):
        return "–"
    if is_en() and unit.startswith("€"):
        return "€" + fmt_num(x) + unit[1:]
    return fmt_num(x) + "\u00a0" + unit


def fmt_pct(x: float) -> str:
    if x is None or pd.isna(x):
        return "–"
    sign = "+" if x >= 0 else "−"
    return f"{sign}{fmt_num(abs(x), 1)}" + ("%" if is_en() else "\u00a0%")


def _type_colors() -> dict:
    return {type_name(k): v for k, v in TYPE_COLORS.items()}


def _style(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, template="plotly_white",
        font=dict(family=FONT, color=INK_2, size=13),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=INK)),
        separators=".," if is_en() else ", ",
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False,
                     title_font=dict(color=INK_2), tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False,
                     title_font=dict(color=INK_2), tickfont=dict(color=MUTED))
    return fig


def show(fig: go.Figure, alt: str) -> None:
    """Affiche le graphique + un texte alternatif lisible (accessibilité)."""
    import hashlib
    key = "chart-" + hashlib.md5(alt.encode()).hexdigest()[:10]
    st.plotly_chart(fig, config=CONFIG, theme=None, width="stretch", key=key)
    st.caption(t("Description du graphique : ", "Chart description: ") + alt)


# ---- Graphiques -----------------------------------------------------------
def line_chart(df: pd.DataFrame, x: str, y: str, color: str, y_title: str,
               events=(), height: int = 380, hover_fmt: str = ",.0f",
               y_unit: str = "") -> go.Figure:
    df = df.assign(**{color: df[color].map(type_name)})
    fig = px.line(df, x=x, y=y, color=color, color_discrete_map=_type_colors(),
                  markers=True, labels={x: "", y: y_title, color: ""})
    fig.update_traces(line=dict(width=2), marker=dict(size=6),
                      hovertemplate=f"<b>%{{y:{hover_fmt}}}{y_unit}</b>")
    ticks = pd.date_range(df[x].min(), df[x].max(), freq="MS")
    ticks = [t for t in ticks if t.month in (1, 7)]
    fig.update_xaxes(tickvals=ticks, ticktext=[month_label(d) for d in ticks],
                     hoverformat="%m/%Y")
    fig.update_yaxes(title=y_title, rangemode="tozero" if y_unit.strip() not in ("€/m²",) else "normal")
    fig.update_layout(hovermode="x unified")
    for date, label in events:
        if df[x].min() <= pd.Timestamp(date) <= df[x].max():
            fig.add_vline(x=pd.Timestamp(date).timestamp() * 1000, line_dash="dot",
                          line_color=MUTED, line_width=1)
            fig.add_annotation(x=date, y=1, yref="paper", text=label, showarrow=False,
                               xanchor="left", yanchor="top", xshift=4,
                               font=dict(size=11, color=INK_2), bgcolor=SURFACE)
    return _style(fig, height)


def bar_h(df: pd.DataFrame, x: str, y: str, x_title: str, color: str = "#2a78d6",
          text_fmt=fmt_eur, height: int = 380, hover_extra: str = "",
          diverging: bool = False) -> go.Figure:
    d = df.sort_values(x)
    colors = color
    if diverging:
        colors = ["#b8322f" if v > 0 else "#1c5cab" for v in d[x]]
    fig = go.Figure(go.Bar(
        x=d[x], y=d[y], orientation="h", marker_color=colors,
        marker_line_width=0, text=[text_fmt(v) for v in d[x]],
        textposition="outside", textfont=dict(color=INK_2, size=12), cliponaxis=False,
        customdata=d[["hover"]] if "hover" in d else None,
        hovertemplate="<b>%{y}</b><br>" + x_title + t(" : ", ": ") + "%{x:,.1f}" +
                      ("<br>%{customdata[0]}" if "hover" in d else "") + "<extra></extra>",
    ))
    lo, hi = min(d[x].min(), 0), max(d[x].max(), 0)
    pad = (hi - lo) * 0.28 or 1
    fig.update_xaxes(title=x_title, showgrid=True,
                     range=[lo - (pad if lo < 0 else 0), hi + (pad if hi > 0 else 0)])
    fig.update_yaxes(title=None)
    fig.update_layout(bargap=0.25)
    return _style(fig, height, legend=False)


def _interp(scale: list, pos: float) -> str:
    """Couleur à la position pos (0–1) d'une échelle [[pos, '#hex'], ...]."""
    for (p0, c0), (p1, c1) in zip(scale, scale[1:]):
        if pos <= p1:
            w = (pos - p0) / (p1 - p0) if p1 > p0 else 0
            a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
            b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
            return "#" + "".join(f"{round(x + (y - x) * w):02x}" for x, y in zip(a, b))
    return scale[-1][1]


@st.cache_data(show_spinner=False)
def _dep_shapes(geojson_text: str) -> dict:
    """Contours projetés (x = lon·cos 46,5°, y = lat), un tracé par département."""
    import json
    import math
    k = math.cos(math.radians(46.5))
    shapes = {}
    for feat in json.loads(geojson_text)["features"]:
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        xs, ys = [], []
        for poly in polys:
            ring = poly[0]  # contour extérieur (les départements n'ont pas de trous utiles)
            xs += [p[0] * k for p in ring] + [None]
            ys += [p[1] for p in ring] + [None]
        shapes[feat["properties"]["code"]] = (xs, ys, feat["properties"]["nom"])
    return shapes


def choropleth(df: pd.DataFrame, geojson_text: str, value: str, title: str,
               diverging: bool = False, unit: str = "") -> go.Figure:
    """Carte des départements de métropole, dessinée en polygones (aucun fond de carte requis)."""
    d = df.set_index("dep")
    vals = d[value].dropna()
    if diverging:
        lim = max(abs(vals.quantile(0.02)), abs(vals.quantile(0.98)), 1)
        scale, lo, hi = DIVERGING, -lim, lim
    else:
        scale = [[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)]
        lo, hi = vals.quantile(0.02), vals.quantile(0.98)

    fig = go.Figure()
    for code, (xs, ys, nom) in _dep_shapes(geojson_text).items():
        v = d[value].get(code) if code in d.index else None
        if v is None or pd.isna(v):
            color = "#f0efec"
            txt = f"<b>{code} – {nom}</b><br>" + t("Données insuffisantes ou non couvertes par DVF",
                                                   "Not enough data, or not covered by DVF")
        else:
            pos = min(max((v - lo) / (hi - lo), 0), 1) if hi > lo else 0.5
            color = _interp(scale, pos)
            r = d.loc[code]
            shown = fmt_pct(v) if diverging else fmt_eur(v, "€/m²")
            sep = t(" : ", ": ")
            txt = (f"<b>{code} – {nom}</b><br>{title}{sep}{shown}"
                   f"<br>{t('Prix médian', 'Median price')}{sep}{fmt_eur(r['prix'], '€/m²')}"
                   f"<br>{t('Ventes retenues', 'Sales kept')}{sep}{fmt_int(r['n'])}")
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself", fillcolor=color,
            line=dict(color="white", width=0.7), hoveron="fills", hoverinfo="text",
            text=txt, showlegend=False))
    # Trace invisible qui porte la légende de couleur
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
        marker=dict(colorscale=scale, cmin=lo, cmax=hi, color=[lo], showscale=True,
                    colorbar=dict(title=dict(text=title, side="right"), thickness=12,
                                  len=0.75, ticksuffix=unit.strip() if diverging else ""))))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig = _style(fig, 600, legend=False)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), dragmode=False,
                      hoverlabel=dict(bgcolor="white"))
    return fig


def yearly_ranges(df: pd.DataFrame) -> go.Figure:
    """Petits multiples : un panneau par type de bien, médiane + intervalle Q1–Q3."""
    df = df.assign(e_plus=df["q3"] - df["median"], e_minus=df["median"] - df["q1"],
                   type=df["type"].map(type_name))
    fig = px.scatter(df, x="periode", y="median", facet_col="type", color="type",
                     color_discrete_map=_type_colors(),
                     error_y="e_plus", error_y_minus="e_minus",
                     custom_data=["q1", "q3", "n"],
                     labels={"periode": "", "median": t("Prix au m² (€)", "Price per m² (€)"),
                             "type": ""})
    fig.update_traces(marker=dict(size=10), error_y=dict(thickness=1.5, width=6),
                      hovertemplate=t(
                          "%{x}<br><b>Médiane : %{y:,.0f} €/m²</b>"
                          "<br>50 % des ventes entre %{customdata[0]:,.0f} et "
                          "%{customdata[1]:,.0f} €/m²<br>%{customdata[2]:,.0f} ventes",
                          "%{x}<br><b>Median: €%{y:,.0f}/m²</b>"
                          "<br>Middle 50% of sales between €%{customdata[0]:,.0f} and "
                          "€%{customdata[1]:,.0f}/m²<br>%{customdata[2]:,.0f} sales")
                      + "<extra></extra>")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1],
                                               font=dict(color=INK, size=13)))
    fig.update_yaxes(matches=None, showticklabels=True)
    return _style(fig, 380, legend=False)


def histogram(df: pd.DataFrame, bin_width: int) -> go.Figure:
    fig = go.Figure()
    for typ, g in df.groupby("type", observed=True):
        name = type_name(typ)
        fig.add_bar(x=g["bin"] + bin_width / 2, y=g["n"], width=bin_width * 0.92, name=name,
                    marker_color=TYPE_COLORS[typ], opacity=0.85,
                    hovertemplate=f"<b>{name}</b><br>%{{x:,.0f}} €/m² (±{bin_width // 2})"
                                  "<br>%{y:,.0f} " + t("ventes", "sales") + "<extra></extra>")
    fig.update_layout(barmode="overlay", bargap=0)
    fig.update_xaxes(title=t("Prix au m² (€)", "Price per m² (€)"))
    fig.update_yaxes(title=t("Nombre de ventes", "Number of sales"))
    return _style(fig, 340)


def funnel(stages: pd.DataFrame) -> go.Figure:
    d = stages.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=d["lignes"], y=d["etape"], orientation="h", marker_color="#3987e5",
        text=[fmt_int(v) for v in d["lignes"]],
        textposition="outside", textfont=dict(color=INK_2), cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} " + t("lignes", "rows") + "<extra></extra>",
    ))
    fig.update_xaxes(title=t("Nombre de lignes (toutes années)", "Number of rows (all years)"))
    fig.update_yaxes(title=None)
    return _style(fig, 340, legend=False)


def change_bars(d: pd.DataFrame, types: list[str], height: int) -> go.Figure:
    """Barres horizontales de part et d'autre de zéro, une couleur par type de bien."""
    pct = t(" %", "%")
    fig = go.Figure()
    for typ in types:
        name = type_name(typ)
        fig.add_bar(y=d["label"], x=d[typ], orientation="h", name=name,
                    marker_color=TYPE_COLORS[typ], marker_line_width=0,
                    hovertemplate=f"<b>%{{y}}</b><br>{name}{t(' : ', ': ')}%{{x:+.1f}}{pct}"
                                  "<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05)
    fig = _style(fig, height, legend=len(types) > 1)
    fig.update_xaxes(title=t("Évolution du prix médian au m² (%)", "Change in median price per m² (%)"),
                     zeroline=True, zerolinecolor=INK_2, zerolinewidth=1, ticksuffix=pct)
    fig.update_yaxes(title=None, autorange="reversed", gridcolor="rgba(0,0,0,0)")
    return fig


# Quadrants du nuage prix / ventes : (prix en hausse ?, ventes en hausse ?) -> couleur, libellés
QUADRANTS = {
    (False, True): ("#2a78d6", "Correction : prix en baisse, ventes en hausse",
                    "Correction: prices down, sales up"),
    (False, False): ("#86b6ef", "Repli : prix et ventes en baisse", "Slowdown: prices and sales down"),
    (True, False): ("#eb6834", "Blocage : ventes en baisse, prix qui tiennent",
                    "Standstill: sales down, prices holding"),
    (True, True): ("#b8322f", "Dynamique : prix et ventes en hausse", "Buoyant: prices and sales up"),
}


def quadrant_of(evol_prix: float, evol_n: float) -> tuple[bool, bool]:
    return (evol_prix >= 0, evol_n >= 0)


def price_volume_scatter(d: pd.DataFrame, ref: tuple[float, float] | None,
                         ref_name: str, labels: list[str]) -> go.Figure:
    """Un point par département : évolution des ventes (x), du prix au m² (y), taille = ventes."""
    sep, pct = t(" : ", ": "), t(" %", "%")
    d = d.assign(q=[quadrant_of(p, n) for p, n in zip(d["evol_prix"], d["evol_n"])])
    sizeref = 2 * d["n"].max() / 38 ** 2
    fig = go.Figure()
    for q, (color, fr, en) in QUADRANTS.items():
        g = d[d["q"] == q]
        if g.empty:
            continue
        fig.add_scatter(
            x=g["evol_n"], y=g["evol_prix"], mode="markers", name=f"{t(fr, en)} ({len(g)})",
            marker=dict(size=g["n"], sizemode="area", sizeref=sizeref, sizemin=4, color=color,
                        opacity=0.8, line=dict(color="white", width=1)),
            text=g["label"], customdata=g[["prix", "n"]],
            hovertemplate="<b>%{text}</b><br>" + t("Évol. prix", "Price change") + sep +
                          f"%{{y:+.1f}}{pct}<br>" + t("Évol. ventes", "Sales change") + sep +
                          f"%{{x:+.1f}}{pct}<br>" + t("Prix médian", "Median price") + sep +
                          "%{customdata[0]:,.0f} €/m²<br>%{customdata[1]:,.0f} " +
                          t("ventes", "sales") + "<extra></extra>")
    lab = d[d["dep"].isin(labels)]
    fig.add_scatter(x=lab["evol_n"], y=lab["evol_prix"], mode="text", text=lab["nom"],
                    textposition="top center", textfont=dict(size=11, color=INK_2),
                    hoverinfo="skip", showlegend=False)
    if ref is not None:
        fig.add_scatter(x=[ref[1]], y=[ref[0]], mode="markers+text", text=[ref_name],
                        textposition="middle right", textfont=dict(size=12, color=INK),
                        marker=dict(symbol="diamond", size=13, color=INK,
                                    line=dict(color="white", width=1.5)),
                        name=ref_name, showlegend=False,
                        hovertemplate=f"<b>{ref_name}</b><br>" + t("Évol. prix", "Price change") +
                                      sep + f"%{{y:+.1f}}{pct}<br>" +
                                      t("Évol. ventes", "Sales change") + sep +
                                      f"%{{x:+.1f}}{pct}<extra></extra>")

    def _range(s):
        lo, hi = min(s.min(), 0), max(s.max(), 0)
        pad = (hi - lo) * 0.08 or 1
        return [lo - pad, hi + pad]

    xr, yr = _range(d["evol_n"]), _range(d["evol_prix"])
    fig.add_hline(y=0, line_color=INK_2, line_width=1)
    fig.add_vline(x=0, line_color=INK_2, line_width=1)
    fig = _style(fig, 560)
    fig.update_xaxes(title=t("Évolution du nombre de ventes (%)", "Change in number of sales (%)"),
                     range=xr, ticksuffix=pct)
    fig.update_yaxes(title=t("Évolution du prix médian au m² (%)", "Change in median price per m² (%)"),
                     range=yr, ticksuffix=pct)
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.14, x=0))
    return fig
