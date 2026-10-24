"""Interprétation des résultats par une IA (Claude, API Anthropic).

L'IA ne reçoit que les chiffres affichés sur la page (filtres compris) et doit s'y tenir.
Sans clé API (ANTHROPIC_API_KEY dans .streamlit/secrets.toml ou dans l'environnement),
le panneau n'est pas affiché et aucun appel n'est fait (la lecture automatique de
utils/insights.py reste disponible).
"""
from __future__ import annotations

import hashlib
import os

import pandas as pd
import streamlit as st

from utils import prep
from utils.i18n import is_en, t, type_name
from utils.viz import QUADRANTS, quadrant_of

MODEL = "claude-opus-5-5"
MAX_QUESTIONS = 15  # par session, pour limiter le coût d'une appli publique

SYSTEM = """Tu es un analyste du marché immobilier intégré à un tableau de bord étudiant \
(EFREI Paris) sur les ventes immobilières françaises (DVF, 2022 à juin 2026). On te donne les \
chiffres affichés sur la page que consulte l'utilisateur, avec les filtres choisis.

Règles :
- Appuie-toi uniquement sur les chiffres fournis et cite-les. Si une information manque pour \
répondre, dis-le au lieu de l'inventer.
- Dis aussi ce que les chiffres ne montrent pas : ce sont des médianes de ventes d'un seul \
logement dans l'ancien ; l'Alsace, la Moselle et Mayotte ne sont pas couvertes ; une année \
partielle est comparée aux mêmes mois de l'année de référence. Distingue corrélation et causalité.
- Pas de conseil financier personnalisé, pas de prédiction de prix.
- Réponse courte (120 à 220 mots), en markdown simple, sans titre ; quelques puces au plus.
- Réponds dans la langue indiquée dans le message.
- Si la question sort du sujet du tableau de bord, recentre poliment."""


# ---------------------------------------------------------------- Contexte par page
def _csv(df: pd.DataFrame, decimals: int = 1) -> str:
    return df.round(decimals).to_csv(index=False).strip()


def _filters(f: prep.Filters) -> str:
    return (f"Filtres : type = {f.type_label} ; zone = {f.zone} ; année de référence = {f.y0} ; "
            f"année étudiée = {prep.period_label(f.y1)}"
            + (" (comparée aux mêmes mois de la référence)" if prep.is_partial(f.y1) else ""))


def _kpis(f: prep.Filters) -> str:
    k = prep.kpis(f.types, f.y0, f.y1, f.deps)
    return (f"Indicateurs de la zone : prix médian {k['prix_m2_ref']:.0f} €/m² en {f.y0} → "
            f"{k['prix_m2']:.0f} €/m² en {f.y1} ({prep.pct(k['prix_m2'], k['prix_m2_ref']):+.1f} %) ; "
            f"ventes retenues {k['n_ref']} → {k['n']} ({prep.pct(k['n'], k['n_ref']):+.1f} %) ; "
            f"prix médian d'un bien {k['valeur_ref']:.0f} € → {k['valeur']:.0f} €.")


def _ctx_when(f: prep.Filters) -> str:
    m = prep.monthly(f.types, f.y0, f.y1, f.deps)
    y = (m.assign(annee=m["mois"].dt.year, type=m["type"].map(str))
          .groupby(["annee", "type"]).agg(prix_m2_median_mensuel_moyen=("prix_m2_median", "mean"),
                                           ventes=("n_ventes", "sum")).reset_index())
    return (f"Page « Quand ? » : prix au m² et nombre de ventes mois par mois.\n{_kpis(f)}\n"
            "Repères : 1re hausse des taux BCE en juillet 2022, 1re baisse en juin 2024.\n"
            f"Résumé annuel (moyenne des médianes mensuelles, total des ventes) :\n{_csv(y, 0)}")


def _ctx_where(f: prep.Filters) -> str:
    d = prep.by_dep(f.types, f.y0, f.y1, f.deps)
    cols = ["label", "prix_ref", "prix", "evol_prix", "n_ref", "n", "evol_n"]
    v = d.dropna(subset=["evol_prix", "evol_n"])
    counts = {QUADRANTS[q][1]: 0 for q in QUADRANTS}
    for p, n in zip(v["evol_prix"], v["evol_n"]):
        counts[QUADRANTS[quadrant_of(p, n)][1]] += 1
    p = d.dropna(subset=["prix"])
    return (f"Page « Où ? » : comparaison des départements.\n{_kpis(f)}\n"
            f"Départements comparables : {len(v)} ; prix en baisse dans "
            f"{int((v['evol_prix'] < 0).sum())}.\n"
            "Répartition prix × ventes : " + " ; ".join(f"{k} = {n}" for k, n in counts.items())
            + f"\n\n12 plus fortes baisses de prix :\n{_csv(v.nsmallest(12, 'evol_prix')[cols])}"
            f"\n\n8 plus fortes hausses de prix :\n{_csv(v.nlargest(8, 'evol_prix')[cols])}"
            f"\n\n5 plus chers en {f.y1} :\n{_csv(p.nlargest(5, 'prix')[['label', 'prix', 'n']], 0)}"
            f"\n\n5 moins chers en {f.y1} :\n{_csv(p.nsmallest(5, 'prix')[['label', 'prix', 'n']], 0)}")


def _ctx_budget(f: prep.Filters) -> str:
    c = st.session_state.get("_ai_credit")
    if not c:
        return f"Page « Pouvoir d'achat ».\n{_kpis(f)}"
    return (f"Page « Pouvoir d'achat » : simulateur de crédit.\n{_kpis(f)}\n"
            f"Hypothèses : mensualité {c['monthly']} € sur {c['years']} ans, apport {c['down']} €, "
            f"taux {c['rate0']:.2f} % en {f.y0} et {c['rate1']:.2f} % en {f.y1} (hors assurance), "
            f"frais de notaire {'déduits' if c['notary'] else 'non déduits'}.\n"
            f"Résultats : budget d'achat {c['b0']:.0f} € en {f.y0} → {c['b1']:.0f} € en {f.y1} ; "
            f"surface {c['s0']:.1f} m² → {c['s1']:.1f} m² ; effet des prix {c['effet_prix']:+.1f} m², "
            f"effet des taux {c['effet_taux']:+.1f} m².\n"
            f"Surface finançable par région (m², {f.y0} puis {f.y1}) :\n{c['regions']}")


def _ctx_dep(f: prep.Filters) -> str:
    dep = st.session_state.get("_focus_dep", "75")
    y = prep.dep_yearly(dep, prep.TYPES)
    y = y[y["n"] >= prep.MIN_VENTES].assign(type=lambda x: x["type"].map(str))
    txt = (f"Page « Zoom département » : {prep.dep_label(dep)}.\n{_filters(f)}\n"
           "Prix au m² par année (* = année partielle) :\n"
           f"{_csv(y[['periode', 'type', 'median', 'q1', 'q3', 'n']], 0)}")
    typ = f.type_choice if f.type_choice in prep.TYPES else "Appartement"
    c = prep.communes(dep, typ, f.y0, f.y1)
    if not c.empty:
        txt += (f"\n\nCommunes les plus chères ({type_name(typ)}, {f.y1}, évolution vs {f.y0}) :\n"
                f"{_csv(c[['commune', 'prix_m2_median', 'evol', 'n_ventes']].head(10))}")
    return txt


CONTEXTS = {"quand": _ctx_when, "ou": _ctx_where, "pouvoir-achat": _ctx_budget,
            "departement": _ctx_dep}


# ---------------------------------------------------------------- Appel à l'API
def _api_key() -> str | None:
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:  # pas de fichier secrets.toml
        key = None
    return key or os.environ.get("ANTHROPIC_API_KEY")


@st.cache_resource(show_spinner=False)
def _client(key: str):
    import anthropic
    return anthropic.Anthropic(api_key=key)


def _answer(key: str, messages: list[dict]) -> str | None:
    """Affiche la réponse au fil de l'eau et la renvoie (None en cas d'erreur)."""
    import anthropic
    try:
        with st.spinner(t("L'IA analyse les chiffres…", "The AI is analysing the figures…")), \
                _client(key).beta.messages.stream(
                    model=MODEL, max_tokens=16000, system=SYSTEM, messages=messages,
                    output_config={"effort": "medium"},
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default") as stream:
            text = st.write_stream(stream.text_stream)
            final = stream.get_final_message()
    except anthropic.AuthenticationError:
        st.error(t("Clé API invalide.", "Invalid API key."))
        return None
    except anthropic.RateLimitError:
        st.error(t("Trop de demandes en ce moment, réessayez dans une minute.",
                   "Too many requests right now, try again in a minute."))
        return None
    except anthropic.APIStatusError as e:
        st.error(t(f"Erreur du service d'IA ({e.status_code}).", f"AI service error ({e.status_code})."))
        return None
    except anthropic.APIConnectionError:
        st.error(t("Impossible de joindre le service d'IA (connexion).",
                   "Could not reach the AI service (connection)."))
        return None
    if final.stop_reason == "refusal":
        st.warning(t("L'IA a refusé de répondre à cette demande.", "The AI declined this request."))
        return None
    return text if isinstance(text, str) else "".join(text)


# ---------------------------------------------------------------- Panneau
def render(page: str, f: prep.Filters) -> None:
    """Panneau Claude : affiché seulement si une clé API est configurée."""
    key = _api_key()
    if not key:
        return
    st.divider()
    with st.container(border=True):
        st.markdown(t("#### :material/smart_toy: Interprétation par l'IA",
                      "#### :material/smart_toy: AI interpretation"))
        st.caption(t(
            "⚠️ Texte généré automatiquement par une IA (Claude, d'Anthropic) à partir des "
            "chiffres de cette page. Elle peut se tromper ou mal interpréter les données : "
            "à lire avec prudence, et à vérifier sur les graphiques.",
            "⚠️ Text generated automatically by an AI (Claude, by Anthropic) from the figures on "
            "this page. It can make mistakes or misread the data: read it with caution and "
            "check it against the charts.",
        ))

        context = f"{_filters(f)}\n\n{CONTEXTS[page](f)}"
        lang = "anglais" if is_en() else "français"
        conv_id = hashlib.md5(f"{page}|{lang}|{context}".encode()).hexdigest()
        convs = st.session_state.setdefault("_ai_convs", {})
        hist = convs.setdefault(conv_id, [])
        used = st.session_state.setdefault("_ai_used", 0)

        box = st.container()
        with box:
            for msg in hist:
                if msg.get("shown", True):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        pending = None
        if not hist:
            if st.button(t("Interpréter ces résultats", "Interpret these results"),
                         icon=":material/auto_awesome:", key=f"ai_go_{page}"):
                pending = (t("Interprète les résultats de cette page pour un jeune actif qui "
                             "envisage d'acheter : que faut-il en retenir ?",
                             "Interpret the results on this page for a young professional "
                             "thinking of buying: what are the key takeaways?"), False)
        if used >= MAX_QUESTIONS:
            st.caption(t(f"Limite de {MAX_QUESTIONS} questions atteinte pour cette session.",
                         f"Limit of {MAX_QUESTIONS} questions reached for this session."))
        else:
            q = st.chat_input(t("Poser une question sur ces résultats…",
                                "Ask a question about these results…"), key=f"ai_q_{page}")
            if q:
                pending = (q, True)
        if not pending:
            return

        question, shown = pending
        first = not hist
        content = (f"Langue de réponse : {lang}.\n\nDonnées de la page :\n{context}\n\n"
                   f"Question : {question}") if first else question
        api_msgs = [{"role": m["role"], "content": m["api"]} for m in hist]
        api_msgs.append({"role": "user", "content": content})
        with box:
            if shown:
                with st.chat_message("user"):
                    st.markdown(question)
            with st.chat_message("assistant"):
                answer = _answer(key, api_msgs)
        if answer is None:
            return
        st.session_state["_ai_used"] = used + 1
        hist.append({"role": "user", "content": question, "api": content, "shown": shown})
        hist.append({"role": "assistant", "content": answer, "api": answer})
