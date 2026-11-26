"""Go / no-go simulator: a game concept -> probability of covering its budget.

The GameConcept class holds the data of a concept (tags, price, budget);
all the logic stays in the functions of the estimation and analysis modules.
"""

from src.analysis import MIN_COMPARABLES, find_comparables, recommend_price
from src.estimation import SCENARIOS

# Recommendation thresholds, from highest to lowest.
# GO: at least 1 comparable game in 2 covered this budget (a favourable coin toss).
# RISKY: between 1 in 4 and 1 in 2: doable, but a failure is likely.
# NO-GO: fewer than 1 game in 4: the budget is too high for this niche.
GO_THRESHOLD = 0.50
RISKY_THRESHOLD = 0.25

# Comparable games must be released after this year (recent market),
# unless this filter leaves fewer than MIN_COMPARABLES games.
RECENT_SINCE_YEAR = 2020


def break_even_probability(comparables, budget, scenario="mid"):
    """Share of comparable games whose net revenue is above the budget.

    comparables: DataFrame enriched by add_estimates.
    budget: float, studio budget in dollars.
    scenario: "low", "mid" or "high".
    Returns a float between 0 and 1 (0.0 if there is no comparable game).
    """
    if len(comparables) == 0:
        return 0.0
    return float((comparables[f"revenue_{scenario}"] >= budget).mean())


def recommendation(probability):
    """Turn a probability into a "GO", "RISKY" or "NO-GO" verdict.

    The thresholds are tested from highest to lowest: otherwise everything
    would fall into the first condition.
    """
    if probability >= GO_THRESHOLD:
        return "GO"
    elif probability >= RISKY_THRESHOLD:
        return "RISKY"
    else:
        return "NO-GO"


def revenue_range(comparables, scenario="mid"):
    """Revenue range: 25th percentile, median, 75th percentile.

    Returns a tuple of 3 floats, or (0.0, 0.0, 0.0) without comparable games.
    """
    if len(comparables) == 0:
        return (0.0, 0.0, 0.0)
    revenues = comparables[f"revenue_{scenario}"]
    p25 = float(revenues.quantile(0.25))     # pessimistic case: 1 game in 4 earns less
    median = float(revenues.quantile(0.50))  # typical case
    p75 = float(revenues.quantile(0.75))     # optimistic case: 1 game in 4 earns more
    return (p25, median, p75)


class GameConcept:
    """A game concept to evaluate: its tags, its price and the studio's budget."""

    def __init__(self, tags, price, budget):
        """Check and store the concept.

        tags: non-empty list of Steam tags (str).
        price: planned selling price in dollars (> 0).
        budget: studio budget in dollars (> 0).
        Raises ValueError if an input is invalid.
        """
        if not tags:
            raise ValueError("Choose at least one tag.")
        if price is None or price <= 0:
            raise ValueError("The price must be strictly positive.")
        if budget is None or budget <= 0:
            raise ValueError("The budget must be strictly positive.")
        self.tags = list(tags)
        self.price = float(price)
        self.budget = float(budget)
        self.result = None
        self.niche = None         # games with the same tags, filled by evaluate
        self.comparables = None   # niche filtered by price and year, filled by evaluate

    def find_comparables(self, df):
        """Recent comparable games (same tags, price ± 50 %), or all years if too few recent games."""
        recent = find_comparables(df, self.tags, price=self.price, since_year=RECENT_SINCE_YEAR)
        if len(recent) >= MIN_COMPARABLES:
            return recent
        return find_comparables(df, self.tags, price=self.price)

    def evaluate(self, df):
        """Evaluate the concept on the market df (DataFrame enriched by add_estimates).

        Returns a dictionary: tags, price, budget, n_comparables,
        revenue_range (p25, median, p75 in the mid scenario), probabilities
        (one per scenario), recommendation (mid scenario), recommendations
        (one per scenario), recommended_price, warning (str or None).
        """
        # The niche (same tags, any price) is used for the recommended price; the
        # comparable games are searched inside the niche, to avoid scanning the whole market again.
        niche = find_comparables(df, self.tags)
        comparables = self.find_comparables(niche)
        self.niche = niche
        self.comparables = comparables

        probabilities = {}
        recommendations = {}
        for scenario in SCENARIOS:
            probabilities[scenario] = break_even_probability(comparables, self.budget, scenario)
            recommendations[scenario] = recommendation(probabilities[scenario])

        warning = None
        if len(comparables) == 0:
            warning = "No comparable game: this concept cannot be evaluated."
        elif len(comparables) < MIN_COMPARABLES:
            warning = (f"Only {len(comparables)} comparable games (recommended minimum: "
                       f"{MIN_COMPARABLES}): the result is not reliable.")

        verdict = recommendation(probabilities["mid"])
        # Without enough evidence, we never advise GO: 1 success out of 1 game
        # proves nothing. The verdict is capped at RISKY.
        if len(comparables) < MIN_COMPARABLES and verdict == "GO":
            verdict = "RISKY"

        self.result = {
            "tags": self.tags,
            "price": self.price,
            "budget": self.budget,
            "n_comparables": len(comparables),
            "revenue_range": revenue_range(comparables),
            "probabilities": probabilities,
            "recommendation": verdict,
            "recommendations": recommendations,
            "recommended_price": recommend_price(niche),
            "warning": warning,
        }
        return self.result

    def summary(self):
        """Return a readable sentence summarising the last evaluation."""
        if self.result is None:
            return "Concept not evaluated yet: call evaluate(df) first."
        r = self.result
        budget = f"{r['budget']:,.0f}"
        probability = f"{r['probabilities']['mid']:.0%}"
        price = r["recommended_price"]
        if price is None:
            price = "not determined"
        text = (f"{r['n_comparables']} comparable games, {probability} covered "
                f"${budget}: {r['recommendation']}. Recommended price: {price}.")
        if r["warning"] is not None:
            text += f" Warning: {r['warning']}"
        return text
