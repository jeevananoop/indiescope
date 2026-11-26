"""Estimate the sales and net revenue of each game, in 3 scenarios.

Steam does not publish sales: we estimate them from the number of reviews
(Boxleiter method). Each assumption is a constant with a comment below.
"""

# Sales per review (Boxleiter method): a game gets on average 1 review
# for 20 to 60 sales (industry rule of thumb). 40 is the middle value.
# Validation (notebook 03_estimation): our sales are mostly below the
# SteamSpy range (a prudent estimate), and the official sales of Valheim,
# Balatro and Hollow Knight fall between the low and mid scenarios.
SALES_PER_REVIEW = {"low": 20, "mid": 40, "high": 60}

# Share of the price kept by Steam: 30 % (standard rate below $10M of revenue).
STEAM_SHARE = 0.30

# Share of sales refunded: Steam refunds on request (less than 2 h of
# play, less than 14 days). We use an order of magnitude of 10 %.
REFUND_RATE = 0.10

# Average price actually paid / listed price: a large share of sales
# happens during Steam sales. We assume an average discount of 25 %.
PRICE_PAID_RATIO = 0.75

# The 3 scenarios, from the most prudent to the most optimistic.
SCENARIOS = ["low", "mid", "high"]


def estimate_sales(n_reviews, scenario="mid"):
    """Estimate the number of sales from the number of reviews.

    n_reviews: int or pandas.Series, total number of reviews (positive + negative).
    scenario: "low", "mid" or "high" (key of SALES_PER_REVIEW).
    Returns the estimated number of sales (same type as n_reviews).
    """
    if scenario not in SALES_PER_REVIEW:
        raise ValueError(f"Unknown scenario: {scenario}. Choose from {SCENARIOS}.")
    return n_reviews * SALES_PER_REVIEW[scenario]


def net_revenue(sales, price, refund_rate=REFUND_RATE, price_paid_ratio=PRICE_PAID_RATIO):
    """Compute the studio's net revenue (after Steam's share, refunds and discounts).

    sales: int/float or Series, number of sales.
    price: float or Series, listed price in dollars.
    refund_rate: share of sales refunded (0 to ignore it).
    price_paid_ratio: average price paid / listed price (1 to ignore it).
    Returns the net revenue in dollars.
    """
    kept_sales = sales * (1 - refund_rate)
    price_paid = price * price_paid_ratio
    return kept_sales * price_paid * (1 - STEAM_SHARE)


def add_estimates(df, refund_rate=REFUND_RATE, price_paid_ratio=PRICE_PAID_RATIO):
    """Add the number of reviews, the sales and the net revenue in the 3 scenarios.

    df: clean DataFrame (data contract: columns positive, negative, price).
    Returns a copy of df with the columns reviews, sales_low/mid/high
    and revenue_low/mid/high.
    """
    df = df.copy()
    df["reviews"] = df["positive"] + df["negative"]
    for scenario in SCENARIOS:
        sales = estimate_sales(df["reviews"], scenario)
        df[f"sales_{scenario}"] = sales
        df[f"revenue_{scenario}"] = net_revenue(sales, df["price"], refund_rate, price_paid_ratio)
    return df
