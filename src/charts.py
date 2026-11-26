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


def format_dollars(value):
    """12345.6 -> "12 346 $" (espace comme séparateur de milliers)."""
    # :,.0f écrit 12345.6 en "12,346" ; on remplace la virgule par une espace.
    return f"{value:,.0f} $".replace(",", " ")


def log10_position(value):
    """Position d'une valeur sur un axe logarithmique de Plotly.

    Sur un axe log, Plotly place les annotations avec le log10 de la valeur.
    max(value, 1e-9) évite le log de 0, qui n'existe pas.
    """
    return math.log10(max(value, 1e-9))


def niche_map(niches, highlight=None):
    """Carte des niches : concurrence (x) contre revenu médian (y), un point par tag.

    niches : DataFrame renvoyé par niche_table (index = tag).
    highlight : liste de tags à mettre en avant (ex. la niche du fil rouge).
    Renvoie une figure Plotly.
    """
    if highlight is None:
        highlight = []
    data = niches.reset_index()  # le tag redevient une colonne normale

    # Chaque tag est soit dans la niche étudiée, soit dans les autres tags.
    groups = []
    for tag in data["tag"]:
        if tag in highlight:
            groups.append("Niche étudiée")
        else:
            groups.append("Autres tags")
    data["groupe"] = groups
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

    # Le nom de chaque niche étudiée est écrit à côté de son point.
    for tag in highlight:
        if tag in list(data["tag"]):
            row = data[data["tag"] == tag].iloc[0]
            fig.add_annotation(x=log10_position(row["n_games"]), y=log10_position(row["median_revenue"]),
                               text=tag, showarrow=True, arrowhead=0, ax=30, ay=-30)
    return fig


def price_chart(prices, niche_name="cette niche"):
    """Revenu net médian par tranche de prix, meilleure tranche en couleur.

    prices : DataFrame renvoyé par price_table (index = tranche de prix).
    niche_name : nom de la niche, pour le titre.
    Renvoie une figure Plotly.
    """
    data = prices.reset_index()
    data["price_band"] = data["price_band"].astype(str)

    # Meilleure tranche : même règle que recommend_price (une tranche trop peu remplie ne peut pas gagner).
    eligible = data[data["n_games"] >= MIN_GAMES_PER_PRICE_BAND]
    best = None
    if len(eligible) > 0:
        best_index = eligible["median_revenue"].idxmax()
        best = eligible.loc[best_index, "price_band"]

    # Apparence de chaque barre. Tranches trop peu remplies : pâles et hachurées.
    colors = []
    opacities = []
    patterns = []
    texts = []
    hover_texts = []
    for index, row in data.iterrows():
        too_few = row["n_games"] < MIN_GAMES_PER_PRICE_BAND
        if row["price_band"] == best:
            colors.append(HIGHLIGHT)
        else:
            colors.append(NEUTRAL)
        if too_few:
            opacities.append(0.45)
            patterns.append("/")
            texts.append(f"{row['n_games']:.0f} jeux (trop peu)")
        else:
            opacities.append(1)
            patterns.append("")
            texts.append(f"{row['n_games']:.0f} jeux")
        hover_texts.append(f"{row['price_band']}<br>Revenu médian : {row['median_revenue']:,.0f} $"
                           f"<br>{row['n_games']:.0f} jeux")

    fig = go.Figure(go.Bar(
        x=data["price_band"], y=data["median_revenue"],
        marker={"color": colors, "opacity": opacities, "pattern": {"shape": patterns}},
        text=texts, textposition="outside",
        hovertext=hover_texts, hoverinfo="text",
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
    Renvoie une figure Plotly.
    """
    # Part des comparables qui dépassent le budget (moyenne de True/False).
    if len(comparables) > 0:
        share = (comparables["revenue_mid"] >= budget).mean()
    else:
        share = 0

    fig = px.box(
        comparables, y="revenue_mid", points="all", hover_name="name",
        log_y=True, template=TEMPLATE, color_discrete_sequence=[NEUTRAL],
        labels={"revenue_mid": "Revenu net estimé par jeu ($, échelle log)"},
        title=f"{share:.0%} des {len(comparables)} jeux comparables dépassent votre budget",
    )
    # Points posés sur la boîte (pointpos=0) et un peu écartés (jitter) pour ne pas se cacher.
    fig.update_traces(marker={"size": 5, "opacity": 0.5}, jitter=0.6, pointpos=0)
    fig.update_layout(boxgap=0.5)  # boîte plus étroite

    # Ligne horizontale au niveau du budget, et son étiquette à droite.
    fig.add_hline(y=budget, line_color=BUDGET_COLOR, line_width=2)
    fig.add_annotation(x=1, xref="paper", xanchor="right", y=log10_position(budget), yanchor="bottom",
                       text=f"Votre budget : {format_dollars(budget)}", showarrow=False,
                       font={"color": BUDGET_COLOR})
    fig.update_yaxes(dtick=1)
    return fig


def releases_per_year(df, tags):
    """Nombre de jeux sortis par an dans la niche définie par tags.

    df : DataFrame enrichi (ou propre) avec tags et release_year.
    tags : liste de tags de la niche.
    Renvoie une figure Plotly.
    """
    niche = find_comparables(df, tags)
    per_year = niche["release_year"].value_counts().sort_index().reset_index()
    per_year.columns = ["release_year", "n_games"]

    # La dernière année est incomplète (dataset arrêté 6 mois avant mars 2026) : on la retire.
    last_year = df["release_year"].max()
    per_year = per_year[per_year["release_year"] < last_year]

    niche_name = " + ".join(tags)
    if len(per_year) > TREND_YEARS:
        # On compare à TREND_YEARS ans plus tôt : la toute première année a souvent
        # 1 ou 2 jeux, ce qui donnerait un ratio spectaculaire mais trompeur.
        first = per_year.iloc[-1 - TREND_YEARS]
        last = per_year.iloc[-1]
        ratio = last["n_games"] / max(first["n_games"], 1)
        title = (f"Niche {niche_name} : {ratio:.1f} fois plus de sorties "
                 f"en {last['release_year']} qu'en {first['release_year']}")
    else:
        title = f"Niche {niche_name} : trop peu de jeux pour voir une tendance"

    fig = px.line(per_year, x="release_year", y="n_games", markers=True, template=TEMPLATE,
                  color_discrete_sequence=[HIGHLIGHT], title=title,
                  labels={"release_year": "Année de sortie", "n_games": "Nombre de jeux sortis"})
    fig.update_traces(line_width=2, marker_size=8)
    return fig


def niche_price_chart(df, tags):
    """Raccourci : price_chart sur les comparables d'une liste de tags."""
    comparables = find_comparables(df, tags)
    return price_chart(price_table(comparables), niche_name=" + ".join(tags))
