"""Tests automatiques des fonctions principales d'IndieScope.

Lancer depuis la racine du projet : python tests/test_project.py
(ou, si pytest est installé : python -m pytest tests).
Les tests utilisent un mini dataset inventé dont on connaît tous les résultats.
"""

import os
import sys

import pandas as pd

# Ajoute la racine du projet à sys.path pour pouvoir importer src/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis import find_comparables, has_all_tags, recommend_price  # noqa: E402
from src.cleaning import parse_date, parse_owners, clean_tag_string  # noqa: E402
from src.estimation import add_estimates, estimate_sales, net_revenue  # noqa: E402
from src.simulator import GameConcept, break_even_probability, recommendation  # noqa: E402

TOLERANCE = 0.01  # pour comparer des décimaux sans ==


def make_mini_games():
    """Mini dataset de 6 jeux inventés, aux résultats calculables à la main.

    Revenu moyen (mid) = avis x 40 x prix x 0,9 x 0,75 x 0,7 = avis x prix x 18,9.
    """
    games = [
        {"app_id": 1, "name": "Rogue A", "price": 10.0, "positive": 900, "negative": 100,
         "release_year": 2022, "tags": "Indie,Rogue-like,Action"},   # 1000 avis -> 189 000 $
        {"app_id": 2, "name": "Rogue B", "price": 12.0, "positive": 50, "negative": 50,
         "release_year": 2021, "tags": "Indie,Rogue-like"},          # 100 avis -> 22 680 $
        {"app_id": 3, "name": "Rogue C", "price": 4.0, "positive": 10, "negative": 0,
         "release_year": 2023, "tags": "Indie,Rogue-like,Pixel Graphics"},  # 10 avis -> 756 $
        {"app_id": 4, "name": "Cozy A", "price": 15.0, "positive": 400, "negative": 0,
         "release_year": 2022, "tags": "Indie,Cozy"},                # 400 avis -> 113 400 $
        {"app_id": 5, "name": "Old Rogue", "price": 10.0, "positive": 300, "negative": 0,
         "release_year": 2016, "tags": "Rogue-like"},                # pas Indie
        {"app_id": 6, "name": "Zero", "price": 20.0, "positive": 0, "negative": 0,
         "release_year": 2024, "tags": "Indie,Rogue-like"},          # 0 avis -> 0 $
    ]
    return add_estimates(pd.DataFrame(games))


def test_cleaning_helpers():
    assert parse_date("Aug 1, 2023").year == 2023
    assert parse_date("n'importe quoi") is None
    assert parse_owners("20000 - 50000") == (20000, 50000)
    assert parse_owners(None) == (None, None)
    assert clean_tag_string(" Indie , Action,,") == "Indie,Action"


def test_estimate_sales():
    assert estimate_sales(1000) == 40000
    assert estimate_sales(1000, "low") == 20000
    assert estimate_sales(1000, "high") == 60000
    assert estimate_sales(0) == 0
    try:
        estimate_sales(10, "inconnu")
        assert False, "un scénario inconnu doit lever ValueError"
    except ValueError:
        pass


def test_net_revenue():
    # Check du guide : 40 000 ventes à 10 $, sans remboursements ni promos -> 280 000 $.
    assert abs(net_revenue(40000, 10, refund_rate=0, price_paid_ratio=1) - 280000) < TOLERANCE
    # Avec les hypothèses par défaut : 280 000 x 0,9 x 0,75 = 189 000 $.
    assert abs(net_revenue(40000, 10) - 189000) < TOLERANCE
    assert net_revenue(0, 10) == 0


def test_add_estimates():
    games = make_mini_games()
    rogue_a = games[games["name"] == "Rogue A"].iloc[0]
    assert rogue_a["reviews"] == 1000
    assert rogue_a["sales_mid"] == 40000
    assert abs(rogue_a["revenue_mid"] - 189000) < TOLERANCE


def test_has_all_tags():
    assert has_all_tags("Indie,Rogue-like", ["Indie", "Rogue-like"]) is True
    assert has_all_tags("Indie,Action", ["Indie", "Rogue-like"]) is False   # tag manquant
    assert has_all_tags("Indie,Action", ["indie"]) is True                 # casse différente
    assert has_all_tags("Indie,Rogue-like", ["Roguelike"]) is True         # tiret ignoré
    assert has_all_tags("Indie,Action", []) is True                        # liste vide
    assert has_all_tags(None, ["Indie"]) is False                          # case vide


def test_find_comparables():
    games = make_mini_games()
    assert len(find_comparables(games, ["Indie", "Roguelike"])) == 4
    # Prix 10 $ ± 50 % -> entre 5 et 15 $ : Rogue A (10) et Rogue B (12).
    assert len(find_comparables(games, ["Indie", "Roguelike"], price=10)) == 2
    assert len(find_comparables(games, ["Indie", "Roguelike"], since_year=2022)) == 3
    assert len(find_comparables(games, ["Tag inexistant"])) == 0          # aucun comparable


def test_recommend_price():
    games = make_mini_games()
    roguelikes = find_comparables(games, ["Indie", "Roguelike"])
    # Avec min_games=1, la tranche 5-10$ (Rogue A, 189 000 $) a le meilleur revenu médian.
    assert recommend_price(roguelikes, min_games=1) == "5-10$"
    # Avec le minimum par défaut (10 jeux), aucune tranche n'est assez remplie.
    assert recommend_price(roguelikes) is None


def test_break_even_probability():
    games = make_mini_games()
    roguelikes = find_comparables(games, ["Indie", "Roguelike"])
    # Revenus : 189 000, 22 680, 756, 0 -> 1 jeu sur 4 dépasse 100 000 $.
    assert abs(break_even_probability(roguelikes, 100000) - 0.25) < TOLERANCE
    assert abs(break_even_probability(roguelikes, 500) - 0.75) < TOLERANCE
    assert break_even_probability(roguelikes.iloc[0:0], 1000) == 0.0       # aucun comparable


def test_recommendation():
    assert recommendation(0.9) == "GO"
    assert recommendation(0.5) == "GO"
    assert recommendation(0.3) == "RISKY"
    assert recommendation(0.25) == "RISKY"
    assert recommendation(0.1) == "NO-GO"
    assert recommendation(0.0) == "NO-GO"


def test_game_concept():
    games = make_mini_games()
    result = GameConcept(["indie", "roguelike"], 10, 100000).evaluate(games)
    assert result["n_comparables"] == 2              # Rogue A et Rogue B (prix 5-15 $)
    assert abs(result["probabilities"]["mid"] - 0.5) < TOLERANCE
    assert result["recommendation"] == "RISKY"       # GO plafonné : moins de 30 comparables
    assert result["warning"] is not None
    # Un budget plus gros fait baisser la probabilité.
    bigger = GameConcept(["Indie", "Roguelike"], 10, 500000).evaluate(games)
    assert bigger["probabilities"]["mid"] < result["probabilities"]["mid"]
    # Aucun comparable : pas de plantage.
    empty = GameConcept(["Tag inexistant"], 10, 1000).evaluate(games)
    assert empty["n_comparables"] == 0 and empty["recommendation"] == "NO-GO"


def test_invalid_concepts():
    for tags, price, budget in [([], 10, 1000), (["Indie"], 0, 1000), (["Indie"], 10, 0), (["Indie"], -5, 1000)]:
        try:
            GameConcept(tags, price, budget)
            assert False, f"entrée invalide acceptée : {tags}, {price}, {budget}"
        except ValueError:
            pass


ALL_TESTS = [
    test_cleaning_helpers, test_estimate_sales, test_net_revenue, test_add_estimates,
    test_has_all_tags, test_find_comparables, test_recommend_price,
    test_break_even_probability, test_recommendation, test_game_concept, test_invalid_concepts,
]

if __name__ == "__main__":
    for test in ALL_TESTS:
        test()
        print(f"OK  {test.__name__}")
    print(f"\nTous les tests passent ({len(ALL_TESTS)} tests).")
