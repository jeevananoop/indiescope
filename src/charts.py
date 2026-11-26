"""IndieScope Plotly charts.

Each function takes data and RETURNS a figure (without showing it),
with a title that states the conclusion, not just the measure.
"""

import math

import plotly.express as px
import plotly.graph_objects as go

from src.analysis import MIN_GAMES_PER_PRICE_BAND, find_comparables, price_table

# Number of years over which the release trend of a niche is measured.
TREND_YEARS = 5

# One neutral colour by default; a bright colour only for what must stand
# out (chosen niche, best price band, budget).
NEUTRAL = "#a3a29b"
HIGHLIGHT = "#2a78d6"
BUDGET_COLOR = "#eb6834"
TEMPLATE = "plotly_white"


def format_dollars(value):
    """12345.6 -> "$12,346"."""
    return f"${value:,.0f}"


def log10_position(value):
    """Position of a value on a Plotly logarithmic axis.

    On a log axis, Plotly places annotations using the log10 of the value.
    max(value, 1e-9) avoids the log of 0, which does not exist.
    """
    return math.log10(max(value, 1e-9))


def niche_map(niches, highlight=None):
    """Niche map: competition (x) against median revenue (y), one point per tag.

    niches: DataFrame returned by niche_table (index = tag).
    highlight: list of tags to highlight (e.g. the niches of the running example).
    Returns a Plotly figure.
    """
    if highlight is None:
        highlight = []
    data = niches.reset_index()

    groups = []
    for tag in data["tag"]:
        if tag in highlight:
            groups.append("Studied niche")
        else:
            groups.append("Other tags")
    data["group"] = groups
    data["profitable share (%)"] = (100 * data["profitable_share"]).round(0)

    fig = px.scatter(
        data, x="n_games", y="median_revenue", color="group",
        color_discrete_map={"Other tags": NEUTRAL, "Studied niche": HIGHLIGHT},
        hover_name="tag", hover_data={"group": False, "profitable share (%)": True},
        log_x=True, log_y=True, template=TEMPLATE,
        labels={"n_games": "Number of games with the tag (competition)",
                "median_revenue": "Median net revenue per game ($)", "group": ""},
        title="The most profitable niches are often the least crowded (top left)",
    )
    fig.update_traces(marker={"size": 8, "opacity": 0.8})
    fig.update_xaxes(dtick=1)  # on a log axis: one tick per power of 10
    fig.update_yaxes(dtick=1)

    for tag in highlight:
        if tag in list(data["tag"]):
            row = data[data["tag"] == tag].iloc[0]
            fig.add_annotation(x=log10_position(row["n_games"]), y=log10_position(row["median_revenue"]),
                               text=tag, showarrow=True, arrowhead=0, ax=30, ay=-30)
    return fig


def price_chart(prices, niche_name="this niche"):
    """Median net revenue by price band, with the best band in colour.

    prices: DataFrame returned by price_table (index = price band).
    niche_name: name of the niche, for the title.
    Returns a Plotly figure.
    """
    data = prices.reset_index()
    data["price_band"] = data["price_band"].astype(str)

    # Best band: same rule as recommend_price (a band with too few games cannot win).
    eligible = data[data["n_games"] >= MIN_GAMES_PER_PRICE_BAND]
    best = None
    if len(eligible) > 0:
        best_index = eligible["median_revenue"].idxmax()
        best = eligible.loc[best_index, "price_band"]

    # Bands with too few games are pale and hatched, so they are not read as reliable.
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
            texts.append(f"{row['n_games']:.0f} games (too few)")
        else:
            opacities.append(1)
            patterns.append("")
            texts.append(f"{row['n_games']:.0f} games")
        hover_texts.append(f"{row['price_band']}<br>Median revenue: {format_dollars(row['median_revenue'])}"
                           f"<br>{row['n_games']:.0f} games")

    fig = go.Figure(go.Bar(
        x=data["price_band"], y=data["median_revenue"],
        marker={"color": colors, "opacity": opacities, "pattern": {"shape": patterns}},
        text=texts, textposition="outside",
        hovertext=hover_texts, hoverinfo="text",
    ))
    if best is None:
        title = f"{niche_name}: no price band has enough games to conclude"
    else:
        title = f"{niche_name}: games at {best} earn the most"
    fig.update_layout(
        template=TEMPLATE,
        title=title,
        xaxis_title="Price band", yaxis_title="Median net revenue per game ($)",
    )
    return fig


def revenue_distribution(comparables, budget):
    """Revenue distribution of the comparable games, with a line at the budget level.

    comparables: DataFrame enriched by add_estimates.
    budget: studio budget in dollars.
    Returns a Plotly figure.
    """
    if len(comparables) > 0:
        share = (comparables["revenue_mid"] >= budget).mean()
    else:
        share = 0

    fig = px.box(
        comparables, y="revenue_mid", points="all", hover_name="name",
        log_y=True, template=TEMPLATE, color_discrete_sequence=[NEUTRAL],
        labels={"revenue_mid": "Estimated net revenue per game ($, log scale)"},
        title=f"{share:.0%} of the {len(comparables)} comparable games exceed your budget",
    )
    # Points drawn on the box (pointpos=0) and spread out (jitter) so they do not hide each other.
    fig.update_traces(marker={"size": 5, "opacity": 0.5}, jitter=0.6, pointpos=0)
    fig.update_layout(boxgap=0.5)

    fig.add_hline(y=budget, line_color=BUDGET_COLOR, line_width=2)
    fig.add_annotation(x=1, xref="paper", xanchor="right", y=log10_position(budget), yanchor="bottom",
                       text=f"Your budget: {format_dollars(budget)}", showarrow=False,
                       font={"color": BUDGET_COLOR})
    fig.update_yaxes(dtick=1)
    return fig


def releases_per_year(df, tags):
    """Number of games released per year in the niche defined by tags.

    df: enriched (or clean) DataFrame with tags and release_year.
    tags: list of tags of the niche.
    Returns a Plotly figure.
    """
    niche = find_comparables(df, tags)
    per_year = niche["release_year"].value_counts().sort_index().reset_index()
    per_year.columns = ["release_year", "n_games"]

    # The last year is incomplete (dataset stops 6 months before March 2026): drop it.
    last_year = df["release_year"].max()
    per_year = per_year[per_year["release_year"] < last_year]

    niche_name = " + ".join(tags)
    if len(per_year) > TREND_YEARS:
        # Compare with TREND_YEARS years earlier: the very first year often has
        # 1 or 2 games, which would give a spectacular but misleading ratio.
        first = per_year.iloc[-1 - TREND_YEARS]
        last = per_year.iloc[-1]
        ratio = last["n_games"] / max(first["n_games"], 1)
        title = (f"{niche_name} niche: {ratio:.1f} times more releases "
                 f"in {last['release_year']} than in {first['release_year']}")
    else:
        title = f"{niche_name} niche: too few games to see a trend"

    fig = px.line(per_year, x="release_year", y="n_games", markers=True, template=TEMPLATE,
                  color_discrete_sequence=[HIGHLIGHT], title=title,
                  labels={"release_year": "Release year", "n_games": "Number of games released"})
    fig.update_traces(line_width=2, marker_size=8)
    return fig

