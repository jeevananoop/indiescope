"""IndieScope : interface Gradio (Carte du marché, Simulateur, Méthode).

Lancer depuis la racine du projet : python app.py
Prérequis : data/games_clean.csv (le créer avec : python src/cleaning.py).
"""

import os

import gradio as gr

from src.analysis import (MIN_GAMES_PER_NICHE, PRICE_TOLERANCE, explode_tags, niche_table,
                          price_table, promising_niches)
from src.assistant import explain_result
from src.charts import niche_map, price_chart, revenue_distribution
from src.cleaning import load_clean
from src.estimation import add_estimates
from src.simulator import GameConcept

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_PATH = os.path.join(PROJECT_DIR, "data", "games_clean.csv")

# Nombre de tags proposés à cocher : les plus fréquents suffisent.
N_TAGS_OFFERED = 40

# Fil rouge, pré-rempli pour que la démo commence en un clic.
DEFAULT_TAGS = ["Indie", "Cozy"]
DEFAULT_PRICE = 15
DEFAULT_BUDGET = 60000
# Les deux niches du fil rouge, mises en avant sur la carte du marché.
HIGHLIGHTED_NICHES = ["Cozy", "Rogue-like"]

VERDICT_STYLE = {"GO": "🟢 GO", "RISKY": "🟠 RISKY", "NO-GO": "🔴 NO-GO"}
SCENARIO_NAMES = {"low": "Bas (20 ventes/avis)", "mid": "Moyen (40 ventes/avis)",
                  "high": "Haut (60 ventes/avis)"}

# Chargement et estimations UNE SEULE FOIS, au démarrage : chaque clic réutilise
# ces données au lieu de relire 70 000 jeux.
if not os.path.exists(CLEAN_PATH):
    raise SystemExit("data/games_clean.csv introuvable : lancez d'abord  python src/cleaning.py")
GAMES = add_estimates(load_clean(CLEAN_PATH))
TAG_CHOICES = sorted(set(explode_tags(GAMES)["tag"].value_counts().head(N_TAGS_OFFERED).index)
                     | set(DEFAULT_TAGS) | {"Rogue-like"})


def dollars(value):
    """12345.6 -> "12 346 $"."""
    return f"{value:,.0f} $".replace(",", " ")


def evaluate_concept(tags, price, budget):
    """Fonction du bouton « Évaluer » : renvoie (verdict, détails, figure revenus, figure prix)."""
    try:
        concept = GameConcept(tags, price, budget)
    except ValueError as error:
        gr.Warning(str(error))
        return f"## ⚠️ {error}", "", None, None

    result = concept.evaluate(GAMES)
    if result["n_comparables"] == 0:
        return ("## 🔴 Aucun jeu comparable",
                "Aucun jeu ne combine tous ces tags à ce prix. Retirez un tag ou changez le prix.",
                None, None)

    verdict = (f"## {VERDICT_STYLE[result['recommendation']]} : "
               f"{result['probabilities']['mid']:.0%} des jeux comparables ont remboursé {dollars(budget)}")

    p25, median, p75 = result["revenue_range"]
    lines = [
        f"**{result['n_comparables']} jeux comparables** (tags : {', '.join(tags)} ; prix entre "
        f"{price * (1 - PRICE_TOLERANCE):.2f} $ et {price * (1 + PRICE_TOLERANCE):.2f} $).",
        "",
        f"**Fourchette de revenu net** (scénario moyen) : {dollars(p25)} à {dollars(p75)}, "
        f"médiane {dollars(median)}.",
        "",
        f"**Prix conseillé** : {result['recommended_price'] or 'non déterminé (trop peu de jeux)'}",
        "",
        "| Scénario | Probabilité de rembourser le budget | Verdict |",
        "|---|---|---|",
    ]
    for scenario, name in SCENARIO_NAMES.items():
        lines.append(f"| {name} | {result['probabilities'][scenario]:.0%} | "
                     f"{result['recommendations'][scenario]} |")
    if result["warning"]:
        lines += ["", f"⚠️ **{result['warning']}**"]

    return (verdict, "\n".join(lines),
            revenue_distribution(concept.comparables, budget),
            price_chart(price_table(concept.niche), niche_name=" + ".join(tags)))


def explain_concept(tags, price, budget):
    """Fonction du bouton « Expliquer » : avis rédigé par l'IA (bonus), ou message si indisponible."""
    try:
        concept = GameConcept(tags, price, budget)
    except ValueError as error:
        return f"⚠️ {error}"
    return explain_result(concept.evaluate(GAMES))


def market_map(min_games):
    """Fonction du bouton « Afficher » : renvoie (carte des niches, tableau des niches prometteuses)."""
    niches = niche_table(GAMES, min_games=int(min_games))
    table = promising_niches(niches).reset_index()
    table = table[["tag", "n_games", "median_revenue", "profitable_share", "growth"]]
    table["median_revenue"] = table["median_revenue"].round(0)
    table["profitable_share"] = (100 * table["profitable_share"]).round(0)
    table["growth"] = (100 * table["growth"]).round(0)
    table.columns = ["Tag", "Nombre de jeux", "Revenu médian ($)", "Jeux rentables (%)",
                     "Évolution des sorties (%)"]
    return niche_map(niches, highlight=HIGHLIGHTED_NICHES), table


METHOD_TEXT = """
## D'où viennent les données ?
- **Steam Games Dataset** (FronkonGames, Kaggle, licence MIT) : environ 126 000 jeux, collectés en mars 2026.
- Après nettoyage : **71 352 jeux** payants, tagués, sortis entre 2015 et août 2025.
- Deux pièges corrigés : un décalage d'une colonne dans le fichier, et des prix enregistrés en promotion (on retrouve le prix plein).

## Comment on estime le revenu d'un jeu
Steam ne publie pas les ventes. On les estime à partir du nombre d'avis :
- **1 avis ≈ 20 / 40 / 60 ventes** (scénarios bas / moyen / haut, méthode Boxleiter) ;
- Steam garde **30 %** du prix ; **10 %** des ventes sont remboursées ; le prix moyen payé est **75 %** du prix plein (soldes).

**Revenu net = avis × 40 × prix × 0,9 × 0,75 × 0,7**

Validation : notre estimation est plutôt sous la fourchette d'owners SteamSpy (prudente), et les ventes officielles de Valheim, Balatro et Hollow Knight tombent entre nos scénarios bas et moyen.

## Comment on décide
- **Jeux comparables** : ceux qui ont tous vos tags, un prix à ± 50 % du vôtre, sortis depuis 2020 (ou toutes années s'il y en a moins de 30).
- **Probabilité** = part des comparables dont le revenu net dépasse votre budget. On utilise la médiane, pas la moyenne : quelques succès à plusieurs millions fausseraient tout.
- **Verdict** : GO à partir de 50 %, RISKY de 25 à 50 %, NO-GO en dessous. Moins de 30 comparables : jamais GO.

## Ce que l'outil ne voit pas
- Ni le marketing, ni la qualité du jeu : deux jeux identiques sur le papier peuvent avoir des destins opposés.
- Les owners ne sont pas des ventes (clés offertes, bundles) ; le ratio avis / ventes varie selon le genre.
- Biais du survivant : les jeux retirés de Steam ne sont pas dans les données, donc les chances sont un peu optimistes.
- Les jeux free-to-play sont exclus.
"""


with gr.Blocks(title="IndieScope") as demo:
    gr.Markdown("# 🎮 IndieScope\nMon jeu indé peut-il rembourser son budget sur Steam ?")

    with gr.Tab("Simulateur"):
        with gr.Row():
            with gr.Column(scale=1):
                tags_input = gr.CheckboxGroup(TAG_CHOICES, value=DEFAULT_TAGS, label="Tags de votre jeu")
                price_input = gr.Number(value=DEFAULT_PRICE, label="Prix de vente ($)", minimum=0)
                budget_input = gr.Number(value=DEFAULT_BUDGET, label="Budget du studio ($)", minimum=0)
                evaluate_button = gr.Button("Évaluer", variant="primary")
            with gr.Column(scale=2):
                verdict_output = gr.Markdown()
                details_output = gr.Markdown()
        with gr.Row():
            distribution_plot = gr.Plot(label="Revenus des jeux comparables")
            price_plot = gr.Plot(label="Revenu par tranche de prix")
        evaluate_button.click(fn=evaluate_concept, inputs=[tags_input, price_input, budget_input],
                              outputs=[verdict_output, details_output, distribution_plot, price_plot])
        explain_button = gr.Button("Expliquer (avis rédigé par l'IA)")
        explanation_output = gr.Markdown()
        explain_button.click(fn=explain_concept, inputs=[tags_input, price_input, budget_input],
                             outputs=explanation_output)

    with gr.Tab("Carte du marché"):
        min_games_input = gr.Slider(20, 500, value=MIN_GAMES_PER_NICHE, step=10,
                                    label="Nombre minimum de jeux par niche")
        map_button = gr.Button("Afficher", variant="primary")
        map_plot = gr.Plot(label="Carte des niches")
        gr.Markdown("### Niches prometteuses\nPeu de concurrence, au moins 30 % de jeux rentables "
                    "(> 100 000 $), sorties qui n'ont pas doublé en 2 ans.")
        niches_output = gr.DataFrame()
        map_button.click(fn=market_map, inputs=min_games_input, outputs=[map_plot, niches_output])

    with gr.Tab("Méthode"):
        gr.Markdown(METHOD_TEXT)

    # Remplit les deux premiers onglets dès l'ouverture : la démo commence tout de suite.
    demo.load(fn=evaluate_concept, inputs=[tags_input, price_input, budget_input],
              outputs=[verdict_output, details_output, distribution_plot, price_plot])
    demo.load(fn=market_map, inputs=min_games_input, outputs=[map_plot, niches_output])


if __name__ == "__main__":
    demo.launch()
