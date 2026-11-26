"""Automated tests of IndieScope's main functions.

Run from the project root: python tests/test_project.py
(or, if pytest is installed: python -m pytest tests).
The tests use a small made-up dataset whose results are all known.
"""

import sys

import pandas as pd

# Lets the tests import the src/ folder (they are run from the project root).
sys.path.append(".")

from src.analysis import (find_comparables, has_all_tags, niche_table,
                          promising_niches, recommend_price)
from src.cleaning import parse_date, parse_owners, clean_tag_string, clean_games
from src.estimation import add_estimates, estimate_sales, net_revenue
from src.simulator import GameConcept, break_even_probability, recommendation

TOLERANCE = 0.01  # to compare decimals without ==


def make_mini_games():
    """Mini dataset of 6 made-up games, whose results can be computed by hand.

    Mid revenue = reviews x 40 x price x 0.9 x 0.75 x 0.7 = reviews x price x 18.9.
    """
    games = [
        {"app_id": 1, "name": "Rogue A", "price": 10.0, "positive": 900, "negative": 100,
         "release_year": 2022, "tags": "Indie,Rogue-like,Action"},   # 1000 reviews -> $189,000
        {"app_id": 2, "name": "Rogue B", "price": 12.0, "positive": 50, "negative": 50,
         "release_year": 2021, "tags": "Indie,Rogue-like"},          # 100 reviews -> $22,680
        {"app_id": 3, "name": "Rogue C", "price": 4.0, "positive": 10, "negative": 0,
         "release_year": 2023, "tags": "Indie,Rogue-like,Pixel Graphics"},  # 10 reviews -> $756
        {"app_id": 4, "name": "Cozy A", "price": 15.0, "positive": 400, "negative": 0,
         "release_year": 2022, "tags": "Indie,Cozy"},                # 400 reviews -> $113,400
        {"app_id": 5, "name": "Old Rogue", "price": 10.0, "positive": 300, "negative": 0,
         "release_year": 2016, "tags": "Rogue-like"},                # not Indie
        {"app_id": 6, "name": "Zero", "price": 20.0, "positive": 0, "negative": 0,
         "release_year": 2024, "tags": "Indie,Rogue-like"},          # 0 reviews -> $0
    ]
    return add_estimates(pd.DataFrame(games))


def test_cleaning_helpers():
    assert parse_date("Aug 1, 2023").year == 2023
    assert parse_date("not a date") is None
    assert parse_owners("20000 - 50000") == (20000, 50000)
    assert parse_owners(None) == (None, None)
    assert clean_tag_string(" Indie , Action,,") == "Indie,Action"


def raw_game(app_id, name, date, price, discount, owners, tags):
    """One row of the raw file (same column names as games.csv)."""
    return {"AppID": app_id, "Name": name, "Release date": date, "Price": price,
            "Discount": discount, "Positive": 10, "Negative": 0,
            "Estimated owners": owners, "Tags": tags}


def make_mini_raw():
    """Mini raw file of 7 games, one trap per game."""
    games = [
        raw_game(1, "Good game", "Aug 1, 2020", 5.0, 50, "20000 - 50000", "Indie , Action"),  # kept
        raw_game(1, "Good game", "Aug 1, 2020", 5.0, 50, "20000 - 50000", "Indie , Action"),  # duplicate
        raw_game(2, "Free", "Aug 1, 2020", 0.0, 0, "0 - 20000", "Indie"),                     # free
        raw_game(3, "No discount", "Mar 3, 2019", 9.99, None, "0 - 20000", "Cozy"),           # empty discount: kept
        raw_game(4, "Too recent", "Jan 10, 2026", 9.99, 0, "0 - 20000", "Indie"),             # < 6 months
        raw_game(5, "Too old", "May 5, 2010", 9.99, 0, "0 - 20000", "Indie"),                 # before 2015
        raw_game(6, "No tag", "May 5, 2018", 9.99, 0, "0 - 20000", None),                     # no tag
    ]
    return pd.DataFrame(games)


def test_clean_games():
    clean, report = clean_games(make_mini_raw())
    assert list(clean["name"]) == ["Good game", "No discount"]
    assert len(clean.columns) == 10                          # data contract
    good_game = clean.iloc[0]
    assert abs(good_game["price"] - 10.0) < TOLERANCE        # $5 at -50 % -> full price $10
    assert good_game["tags"] == "Indie,Action"               # spaces removed
    assert good_game["owners_max"] == 50000
    # The report starts at 7 rows and ends at 2: 5 rows removed in total.
    assert report["rows left"].iloc[0] == 7
    assert report["rows left"].iloc[-1] == 2
    assert report["rows removed"].sum() == 5


def test_estimate_sales():
    assert estimate_sales(1000) == 40000
    assert estimate_sales(1000, "low") == 20000
    assert estimate_sales(1000, "high") == 60000
    assert estimate_sales(0) == 0
    try:
        estimate_sales(10, "unknown")
        assert False, "an unknown scenario must raise ValueError"
    except ValueError:
        pass


def test_net_revenue():
    # 40,000 sales at $10, without refunds or discounts -> $280,000.
    assert abs(net_revenue(40000, 10, refund_rate=0, price_paid_ratio=1) - 280000) < TOLERANCE
    # With the default assumptions: 280,000 x 0.9 x 0.75 = $189,000.
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
    assert has_all_tags("Indie,Action", ["Indie", "Rogue-like"]) is False   # missing tag
    assert has_all_tags("Indie,Action", ["indie"]) is True                 # different case
    assert has_all_tags("Indie,Rogue-like", ["Roguelike"]) is True         # hyphen ignored
    assert has_all_tags("Indie,Action", []) is True                        # empty list
    assert has_all_tags(None, ["Indie"]) is False                          # empty cell


def test_find_comparables():
    games = make_mini_games()
    assert len(find_comparables(games, ["Indie", "Roguelike"])) == 4
    # Price $10 ± 50 % -> between $5 and $15: Rogue A (10) and Rogue B (12).
    assert len(find_comparables(games, ["Indie", "Roguelike"], price=10)) == 2
    assert len(find_comparables(games, ["Indie", "Roguelike"], since_year=2022)) == 3
    assert len(find_comparables(games, ["Missing tag"])) == 0              # no comparable game


def test_niche_table():
    games = make_mini_games()
    niches = niche_table(games, min_games=1)
    # Rogue-like: 5 games (Rogue A, B, C, Old Rogue, Zero), 1 of them profitable (Rogue A).
    assert niches.loc["Rogue-like", "n_games"] == 5
    assert abs(niches.loc["Rogue-like", "profitable_share"] - 0.2) < TOLERANCE
    # Cozy: a single game, profitable ($113,400).
    assert niches.loc["Cozy", "profitable_share"] == 1.0
    # With the default minimum (50 games), no niche of the mini dataset is kept.
    assert niche_table(games).empty


def test_promising_niches():
    games = make_mini_games()
    promising = promising_niches(niche_table(games, min_games=1))
    # Cozy: 1 profitable game out of 1, released in 2022, none in 2023-2024 -> promising.
    assert "Cozy" in promising.index
    # Rogue-like: only 20 % of profitable games (< 30 %) -> not promising.
    assert "Rogue-like" not in promising.index


def test_recommend_price():
    games = make_mini_games()
    roguelikes = find_comparables(games, ["Indie", "Roguelike"])
    # With min_games=1, the 5-10$ band (Rogue A, $189,000) has the best median revenue.
    assert recommend_price(roguelikes, min_games=1) == "5-10$"
    # With the default minimum (10 games), no band has enough games.
    assert recommend_price(roguelikes) is None


def test_break_even_probability():
    games = make_mini_games()
    roguelikes = find_comparables(games, ["Indie", "Roguelike"])
    # Revenues: 189,000, 22,680, 756, 0 -> 1 game in 4 exceeds $100,000.
    assert abs(break_even_probability(roguelikes, 100000) - 0.25) < TOLERANCE
    assert abs(break_even_probability(roguelikes, 500) - 0.75) < TOLERANCE
    assert break_even_probability(roguelikes.iloc[0:0], 1000) == 0.0       # no comparable game


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
    assert result["n_comparables"] == 2              # Rogue A and Rogue B (price $5-15)
    assert abs(result["probabilities"]["mid"] - 0.5) < TOLERANCE
    assert result["recommendation"] == "RISKY"       # GO capped: fewer than 30 comparable games
    assert result["warning"] is not None
    # A bigger budget lowers the probability.
    bigger = GameConcept(["Indie", "Roguelike"], 10, 500000).evaluate(games)
    assert bigger["probabilities"]["mid"] < result["probabilities"]["mid"]
    # No comparable game: no crash.
    empty = GameConcept(["Missing tag"], 10, 1000).evaluate(games)
    assert empty["n_comparables"] == 0
    assert empty["recommendation"] == "NO-GO"


def test_invalid_concepts():
    for tags, price, budget in [([], 10, 1000), (["Indie"], 0, 1000), (["Indie"], 10, 0), (["Indie"], -5, 1000)]:
        try:
            GameConcept(tags, price, budget)
            assert False, f"invalid input accepted: {tags}, {price}, {budget}"
        except ValueError:
            pass


ALL_TESTS = [
    test_cleaning_helpers, test_clean_games, test_estimate_sales, test_net_revenue, test_add_estimates,
    test_has_all_tags, test_find_comparables, test_niche_table, test_promising_niches,
    test_recommend_price, test_break_even_probability, test_recommendation, test_game_concept,
    test_invalid_concepts,
]

if __name__ == "__main__":
    for test in ALL_TESTS:
        test()
        print(f"OK  {test.__name__}")
    print(f"\nAll tests pass ({len(ALL_TESTS)} tests).")
