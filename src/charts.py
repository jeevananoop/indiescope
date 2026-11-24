"""Graphiques Plotly d'IndieScope.

Chaque fonction prend des données et RENVOIE une figure (sans l'afficher),
avec un titre qui énonce la conclusion, pas seulement la mesure.
"""

import math

import plotly.express as px
import plotly.graph_objects as go

from src.analysis import MIN_GAMES_PER_PRICE_BAND, find_comparables, price_table

# Nombre d'années sur lequel on mesure la tendance des sorties d'une niche.
TREND_YEARS = 5

# Une seule couleur neutre par défaut ; une couleur vive seulement pour ce
# qui doit sauter aux yeux (niche choisie, meilleure tranche, budget).
NEUTRAL = "#a3a29b"
HIGHLIGHT = "#2a78d6"
BUDGET_COLOR = "#eb6834"
TEMPLATE = "plotly_white"


def _format_dollars(value):
    """12345.6 -> "12 346 $" (séparateur de milliers à la française)."""
    return f"{value:,.0f} $".replace(",", " ")


def niche_map(niches, highlight=None):
    """Carte des niches : concurrence (x) contre revenu médian (y), un point par tag.

    niches : DataFrame renvoyé par niche_table (index = tag).
    highlight : liste de tags à mettre en avant (ex. la niche du fil rouge).
    Renvoie une plotly.graph_objects.Figure.
    """
    data = niches.reset_index().rename(columns={"index": "tag"})
    highlight = set(highlight or [])
    data["groupe"] = data["tag"].apply(lambda t: "Niche étudiée" if t in highlight else "Autres tags")
    data["part rentable (%)"] = (100 * data["profitable_share"]).round(0)
    fig = px.scatter(
        data, x="n_games", y="median_revenue", color="groupe",
        color_discrete_map={"Autres tags": NEUTRAL, "Niche étudiée": HIGHLIGHT},
        hover_name="tag", hover_data={"groupe": False, "part rentable (%)": True},
        log_x=True, log_y=True, template=TEMPLATE,
        labels={"n_games": "Nombre de jeux sur le tag (concurrence)",
                "median_revenue": "Revenu net médian par jeu ($)", "groupe": ""},
        title="Les niches les plus rentables sont souvent les moins encombrées (en haut à gauche)",
    )
    fig.update_traces(marker={"size": 8, "opacity": 0.8})
    fig.update_xaxes(dtick=1)  # sur un axe log : une graduation par puissance de 10
    fig.update_yaxes(dtick=1)
    for tag in highlight & set(data["tag"]):
        row = data[data["tag"] == tag].iloc[0]
        fig.add_annotation(x=_log10(row["n_games"]), y=_log10(row["median_revenue"]),
                           text=tag, showarrow=True, arrowhead=0, ax=30, ay=-30)
    return fig


def _log10(value):
    """Position d'une annotation sur un axe logarithmique de Plotly."""
    return math.log10(max(value, 1e-9))


def price_chart(prices, niche_name="cette niche"):
    """Revenu net médian par tranche de prix, meilleure tranche en couleur.

    prices : DataFrame renvoyé par price_table (index = tranche de prix).
    niche_name : nom de la niche, pour le titre.
    Renvoie une plotly.graph_objects.Figure.
    """
    data = prices.reset_index()
    data["price_band"] = data["price_band"].astype(str)
    # Même règle que recommend_price : une tranche trop peu remplie ne peut pas gagner.
    eligible = data[data["n_games"] >= MIN_GAMES_PER_PRICE_BAND]
    best = eligible.loc[eligible["median_revenue"].idxmax(), "price_band"] if len(eligible) else None
    colors = [HIGHLIGHT if band == best else NEUTRAL for band in data["price_band"]]
    # Tranches trop peu remplies : hachurées et pâles, pour montrer qu'on les ignore.
    too_few = data["n_games"] < MIN_GAMES_PER_PRICE_BAND
    fig = go.Figure(go.Bar(
        x=data["price_band"], y=data["median_revenue"],
        marker={"color": colors, "opacity": [0.45 if few else 1 for few in too_few],
                "pattern": {"shape": ["/" if few else "" for few in too_few]}},
        text=[f"{n:.0f} jeux" + (" (trop peu)" if few else "") for n, few in zip(data["n_games"], too_few)],
        textposition="outside",
        customdata=data[["n_games"]],
        hovertemplate="%{x}<br>Revenu médian : %{y:,.0f} $<br>%{customdata[0]} jeux<extra></extra>",
    ))
    if best is None:
        title = f"Dans {niche_name}, aucune tranche de prix n'a assez de jeux pour conclure"
    else:
        title = f"Dans {niche_name}, les jeux à {best} rapportent le plus (revenu médian)"
    fig.update_layout(
        template=TEMPLATE,
        title=title,
        xaxis_title="Tranche de prix", yaxis_title="Revenu net médian par jeu ($)",
    )
    return fig


def revenue_distribution(comparables, budget):
    """Distribution du revenu des jeux comparables, avec une ligne au niveau du budget.

    comparables : DataFrame enrichi par add_estimates.
    budget : budget du studio en dollars.
    Renvoie une plotly.graph_objects.Figure.
    """
    share = (comparables["revenue_mid"] >= budget).mean() if len(comparables) else 0
    fig = px.box(
        comparables, y="revenue_mid", points="all", hover_name="name",
        log_y=True, template=TEMPLATE, color_discrete_sequence=[NEUTRAL],
        labels={"revenue_mid": "Revenu net estimé par jeu ($, échelle log)"},
        title=f"{share:.0%} des {len(comparables)} jeux comparables dépassent votre budget",
    )
    # Points posés sur la boîte (pointpos=0), boîte étroite.
    fig.update_traces(marker={"size": 5, "opacity": 0.5}, jitter=0.6, pointpos=0)
    fig.update_layout(boxgap=0.5)
    fig.add_hline(y=budget, line_color=BUDGET_COLOR, line_width=2)
    # Sur un axe log, une annotation se place avec le log10 de la valeur.
    fig.add_annotation(x=1, xref="paper", xanchor="right", y=_log10(budget), yanchor="bottom",
                       text=f"Votre budget : {_format_dollars(budget)}", showarrow=False,
                       font={"color": BUDGET_COLOR})
    fig.update_yaxes(dtick=1)
    return fig


def releases_per_year(df, tags):
    """Nombre de jeux sortis par an dans la niche définie par tags.

    df : DataFrame enrichi (ou propre) avec tags et release_year.
    tags : liste de tags de la niche.
    Renvoie une plotly.graph_objects.Figure.
    """
    niche = find_comparables(df, tags)
    per_year = niche.groupby("release_year").size().reset_index(name="n_games")
    # La dernière année est incomplète (dataset arrêté 6 mois avant mars 2026) : on la retire.
    per_year = per_year[per_year["release_year"] < df["release_year"].max()]
    if len(per_year) > TREND_YEARS:
        # On compare à TREND_YEARS ans plus tôt : la toute première année a souvent
        # 1 ou 2 jeux, ce qui donnerait un ratio spectaculaire mais trompeur.
        first, last = per_year.iloc[-1 - TREND_YEARS], per_year.iloc[-1]
        ratio = last["n_games"] / max(first["n_games"], 1)
        title = (f"Niche {' + '.join(tags)} : {ratio:.1f} fois plus de sorties "
                 f"en {last['release_year']} qu'en {first['release_year']}")
    else:
        title = f"Niche {' + '.join(tags)} : trop peu de jeux pour voir une tendance"
    fig = px.line(per_year, x="release_year", y="n_games", markers=True, template=TEMPLATE,
                  color_discrete_sequence=[HIGHLIGHT], title=title,
                  labels={"release_year": "Année de sortie", "n_games": "Nombre de jeux sortis"})
    fig.update_traces(line_width=2, marker_size=8)
    return fig


def niche_price_chart(df, tags):
    """Raccourci : price_chart sur les comparables d'une liste de tags."""
    return price_chart(price_table(find_comparables(df, tags)), niche_name=" + ".join(tags))
