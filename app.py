"""IndieScope: Gradio interface (Simulator, Market map, Method).

Run from the project root: python app.py
Requires data/games_clean.csv (create it with: python src/cleaning.py).
"""

import os

import gradio as gr

from src.analysis import (MIN_GAMES_PER_NICHE, PRICE_TOLERANCE, explode_tags, niche_table,
                          price_table, promising_niches)
from src.assistant import explain_result
from src.charts import format_dollars, niche_map, price_chart, revenue_distribution
from src.cleaning import load_clean
from src.estimation import add_estimates
from src.simulator import GameConcept

CLEAN_PATH = os.path.join("data", "games_clean.csv")

# Number of tags offered as checkboxes: the most frequent ones are enough.
N_TAGS_OFFERED = 40

# Running example, pre-filled so the demo starts in one click.
DEFAULT_TAGS = ["Indie", "Cozy"]
DEFAULT_PRICE = 15
DEFAULT_BUDGET = 60000
# The two niches of the running example, highlighted on the market map.
HIGHLIGHTED_NICHES = ["Cozy", "Rogue-like"]

VERDICT_STYLE = {"GO": "🟢 GO", "RISKY": "🟠 RISKY", "NO-GO": "🔴 NO-GO"}
SCENARIO_NAMES = {"low": "Low (20 sales/review)", "mid": "Mid (40 sales/review)",
                  "high": "High (60 sales/review)"}

# Load the data and compute the estimates ONCE, at start-up: every click reuses
# them instead of reading 70,000 games again.
if not os.path.exists(CLEAN_PATH):
    raise SystemExit("data/games_clean.csv not found: run  python src/cleaning.py  first")
GAMES = add_estimates(load_clean(CLEAN_PATH))

# Tags offered: the most frequent ones, plus those of the running example, in alphabetical order.
TAG_CHOICES = list(explode_tags(GAMES)["tag"].value_counts().head(N_TAGS_OFFERED).index)
for tag in DEFAULT_TAGS + HIGHLIGHTED_NICHES:
    if tag not in TAG_CHOICES:
        TAG_CHOICES.append(tag)
TAG_CHOICES.sort()


def evaluate_concept(tags, price, budget):
    """Callback of the "Evaluate" button: returns (verdict, details, revenue figure, price figure)."""
    try:
        concept = GameConcept(tags, price, budget)
    except ValueError as error:
        gr.Warning(str(error))
        return f"## ⚠️ {error}", "", None, None

    result = concept.evaluate(GAMES)
    if result["n_comparables"] == 0:
        return ("## 🔴 No comparable game",
                "No game combines all these tags at this price. Remove a tag or change the price.",
                None, None)

    verdict = (f"## {VERDICT_STYLE[result['recommendation']]}: "
               f"{result['probabilities']['mid']:.0%} of comparable games covered {format_dollars(budget)}")

    p25, median, p75 = result["revenue_range"]
    recommended_price = result["recommended_price"]
    if recommended_price is None:
        recommended_price = "not determined (too few games)"
    low_price = price * (1 - PRICE_TOLERANCE)
    high_price = price * (1 + PRICE_TOLERANCE)

    lines = [
        f"**{result['n_comparables']} comparable games** (tags: {', '.join(tags)}; price between "
        f"${low_price:.2f} and ${high_price:.2f}).",
        "",
        f"**Net revenue range** (mid scenario): {format_dollars(p25)} to {format_dollars(p75)}, "
        f"median {format_dollars(median)}.",
        "",
        f"**Recommended price**: {recommended_price}",
        "",
        "| Scenario | Probability of covering the budget | Verdict |",
        "|---|---|---|",
    ]
    for scenario, name in SCENARIO_NAMES.items():
        lines.append(f"| {name} | {result['probabilities'][scenario]:.0%} | "
                     f"{result['recommendations'][scenario]} |")
    if result["warning"] is not None:
        lines.append("")
        lines.append(f"⚠️ **{result['warning']}**")

    details = "\n".join(lines)
    distribution_figure = revenue_distribution(concept.comparables, budget)
    price_figure = price_chart(price_table(concept.niche), niche_name=" + ".join(tags))
    return verdict, details, distribution_figure, price_figure


def explain_concept(tags, price, budget):
    """Callback of the "Explain" button: advice written by the AI (bonus), or a message if it is unavailable."""
    try:
        concept = GameConcept(tags, price, budget)
    except ValueError as error:
        return f"⚠️ {error}"
    return explain_result(concept.evaluate(GAMES))


def market_map(min_games):
    """Callback of the "Show" button: returns (niche map, table of promising niches)."""
    niches = niche_table(GAMES, min_games=int(min_games))
    table = promising_niches(niches).reset_index()
    table = table[["tag", "n_games", "median_revenue", "profitable_share", "growth"]]
    table["median_revenue"] = table["median_revenue"].round(0)
    table["profitable_share"] = (100 * table["profitable_share"]).round(0)
    table["growth"] = (100 * table["growth"]).round(0)
    table.columns = ["Tag", "Number of games", "Median revenue ($)", "Profitable games (%)",
                     "Change in releases (%)"]
    return niche_map(niches, highlight=HIGHLIGHTED_NICHES), table


METHOD_TEXT = """
## Where does the data come from?
- **Steam Games Dataset** (FronkonGames, Kaggle, MIT licence): about 126,000 games, collected in March 2026.
- After cleaning: **71,352 paid, tagged games** released between 2015 and August 2025.
- Two traps fixed: a one-column shift in the file, and prices recorded during a sale (we recover the full price).

## How we estimate a game's revenue
Steam does not publish sales. We estimate them from the number of reviews:
- **1 review ≈ 20 / 40 / 60 sales** (low / mid / high scenarios, Boxleiter method);
- Steam keeps **30 %** of the price; **10 %** of sales are refunded; the average price paid is **75 %** of the full price (sales).

**Net revenue = reviews × 40 × price × 0.9 × 0.75 × 0.7**

Validation: our estimate is mostly below the SteamSpy owners range (prudent), and the official sales of Valheim, Balatro and Hollow Knight fall between our low and mid scenarios.

## How we decide
- **Comparable games**: those that have all your tags, a price within ± 50 % of yours, released since 2020 (or any year if there are fewer than 30).
- **Probability** = share of comparable games whose net revenue exceeds your budget. We use the median, not the mean: a few multi-million hits would distort everything.
- **Verdict**: GO from 50 %, RISKY from 25 to 50 %, NO-GO below. Fewer than 30 comparable games: never GO.

## What the tool cannot see
- Neither marketing nor game quality: two games that look identical on paper can have opposite fates.
- Owners are not sales (gifted keys, bundles); the reviews / sales ratio varies by genre.
- Survivorship bias: games removed from Steam are not in the data, so the odds are slightly optimistic.
- Free-to-play games are excluded.
"""


with gr.Blocks(title="IndieScope") as demo:
    gr.Markdown("# 🎮 IndieScope\nCan my indie game cover its budget on Steam?")

    with gr.Tab("Simulator"):
        with gr.Row():
            with gr.Column(scale=1):
                tags_input = gr.CheckboxGroup(TAG_CHOICES, value=DEFAULT_TAGS, label="Your game's tags")
                price_input = gr.Number(value=DEFAULT_PRICE, label="Selling price ($)", minimum=0)
                budget_input = gr.Number(value=DEFAULT_BUDGET, label="Studio budget ($)", minimum=0)
                evaluate_button = gr.Button("Evaluate", variant="primary")
            with gr.Column(scale=2):
                verdict_output = gr.Markdown()
                details_output = gr.Markdown()
        with gr.Row():
            distribution_plot = gr.Plot(label="Revenue of comparable games")
            price_plot = gr.Plot(label="Revenue by price band")
        evaluate_button.click(fn=evaluate_concept, inputs=[tags_input, price_input, budget_input],
                              outputs=[verdict_output, details_output, distribution_plot, price_plot])
        explain_button = gr.Button("Explain (advice written by AI)")
        explanation_output = gr.Markdown()
        explain_button.click(fn=explain_concept, inputs=[tags_input, price_input, budget_input],
                             outputs=explanation_output)

    with gr.Tab("Market map"):
        min_games_input = gr.Slider(20, 500, value=MIN_GAMES_PER_NICHE, step=10,
                                    label="Minimum number of games per niche")
        map_button = gr.Button("Show", variant="primary")
        map_plot = gr.Plot(label="Niche map")
        gr.Markdown("### Promising niches\nLittle competition, at least 30 % of profitable games "
                    "(> $100,000), releases that have not doubled in 2 years.")
        niches_output = gr.DataFrame()
        map_button.click(fn=market_map, inputs=min_games_input, outputs=[map_plot, niches_output])

    with gr.Tab("Method"):
        gr.Markdown(METHOD_TEXT)

    # Fill the first two tabs on opening, so the demo starts right away.
    demo.load(fn=evaluate_concept, inputs=[tags_input, price_input, budget_input],
              outputs=[verdict_output, details_output, distribution_plot, price_plot])
    demo.load(fn=market_map, inputs=min_games_input, outputs=[map_plot, niches_output])


if __name__ == "__main__":
    demo.launch()
