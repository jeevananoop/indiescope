"""Market analysis: niches (tags), comparable games and revenue by price band.

All functions take a DataFrame enriched by add_estimates()
(columns tags, price, release_year, revenue_low/mid/high).
"""

import pandas as pd

# A game is "profitable" above $100,000 of net revenue: enough to pay
# about one year of work for a small indie team.
PROFITABLE_THRESHOLD = 100000

# Below 50 games, the median of a tag varies too much from one game to the next.
MIN_GAMES_PER_NICHE = 50

# Momentum: we compare the releases of the last 2 complete years
# (2023-2024) with the 2 previous ones (2021-2022). 2025 is incomplete
# (the dataset stops 6 months before March 2026).
RECENT_YEARS = [2023, 2024]
PREVIOUS_YEARS = [2021, 2022]

# A comparable game must have a price within ± 50 % of the concept's price.
PRICE_TOLERANCE = 0.5

# Below 30 comparable games, percentages are no longer reliable
# (a single game weighs more than 3 points): the tool shows a warning.
MIN_COMPARABLES = 30

# Price bands (in dollars) and their names.
PRICE_BINS = [0, 5, 10, 15, 20, 30, float("inf")]
PRICE_LABELS = ["<5$", "5-10$", "10-15$", "15-20$", "20-30$", "30$+"]

# A price band needs at least 10 games to be recommended.
MIN_GAMES_PER_PRICE_BAND = 10

# Tags that describe funding, a licence or past success (given AFTER the
# success), not a concept a studio can choose.
META_TAGS = ["Games Workshop", "Kickstarter", "Crowdfunded", "Mod", "Moddable", "Cult Classic",
             "Great Soundtrack", "Classic", "Remake", "Sequel", "Epic", "Masterpiece",
             "Mature", "Hentai", "NSFW", "Sexual Content", "Nudity", "Dwarf"]

# Criteria of a promising niche: limited competition, at least 30 % of
# profitable games, and releases that have not doubled in 2 years.
PROMISING_MAX_GAMES = 1000
PROMISING_MIN_PROFITABLE_SHARE = 0.30
PROMISING_MAX_GROWTH = 1.0


def split_tags(tag_string):
    """Split "Indie,Action" into the list ["Indie", "Action"] (empty list if the cell is empty)."""
    if not isinstance(tag_string, str):
        return []
    return tag_string.split(",")


def count_tags_loop(df):
    """Count the number of games per tag with a loop and a dictionary.

    Hand-written version (course 4, problem 1), used to check the pandas version.
    Returns a dict {tag: number of games}.
    """
    counts = {}
    for tag_string in df["tags"]:
        for tag in split_tags(tag_string):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def explode_tags(df):
    """Return a DataFrame with one row per (game, tag) pair, in the tag column.

    A game with 3 tags becomes 3 rows, one per tag.
    """
    exploded = df.copy()
    exploded["tag"] = exploded["tags"].str.split(",")
    exploded = exploded.explode("tag")
    return exploded


def niche_table(df, min_games=MIN_GAMES_PER_NICHE, threshold=PROFITABLE_THRESHOLD):
    """Summarise each niche (tag): competition, median revenue, share of profitable games, momentum.

    df: DataFrame enriched by add_estimates.
    min_games: minimum number of games to keep a tag.
    threshold: net revenue (mid scenario) above which a game is profitable.
    Returns a DataFrame indexed by tag, sorted by decreasing median revenue.
    """
    games = explode_tags(df)
    games["profitable"] = games["revenue_mid"] >= threshold
    games["recent"] = games["release_year"].isin(RECENT_YEARS)
    games["previous"] = games["release_year"].isin(PREVIOUS_YEARS)

    groups = games.groupby("tag")
    table = pd.DataFrame()
    table["n_games"] = groups["app_id"].count()
    table["median_revenue"] = groups["revenue_mid"].median()
    table["mean_revenue"] = groups["revenue_mid"].mean()
    table["profitable_share"] = groups["profitable"].mean()  # mean of True/False = share of True
    table["recent_releases"] = groups["recent"].sum()
    table["previous_releases"] = groups["previous"].sum()

    table = table[table["n_games"] >= min_games].copy()

    # Release growth: 0.5 = 50 % more games over the last 2 years.
    # 0 is replaced by 1 in the denominator to avoid dividing by zero.
    previous = table["previous_releases"].replace(0, 1)
    table["growth"] = table["recent_releases"] / previous - 1
    return table.sort_values("median_revenue", ascending=False)


def promising_niches(niches):
    """Filter a niche_table result to keep only the promising niches.

    Removes the META_TAGS, then keeps the tags that are not crowded, often
    profitable and not filling up too fast. Returns a DataFrame sorted by median revenue.
    """
    meta_tags_present = []
    for tag in META_TAGS:
        if tag in niches.index:
            meta_tags_present.append(tag)
    genres = niches.drop(index=meta_tags_present)

    genres = genres[genres["n_games"] <= PROMISING_MAX_GAMES]
    genres = genres[genres["profitable_share"] >= PROMISING_MIN_PROFITABLE_SHARE]
    genres = genres[genres["growth"] < PROMISING_MAX_GROWTH]
    return genres


def tag_pair_table(df, min_games=MIN_GAMES_PER_NICHE, threshold=PROFITABLE_THRESHOLD,
                   top_tags=60):
    """Same analysis as niche_table, but on pairs of tags (e.g. Roguelike + Deckbuilding).

    To limit the computation, only the top_tags most frequent tags are combined.
    Returns a DataFrame indexed by the pair "Tag A + Tag B".
    """
    tag_counts = pd.Series(count_tags_loop(df))
    frequent = list(tag_counts.nlargest(top_tags).index)

    rows = []
    for index, game in df.iterrows():
        # Sorted, so that "A + B" and "B + A" are counted as the same pair.
        game_tags = []
        for tag in split_tags(game["tags"]):
            if tag in frequent and tag not in game_tags:
                game_tags.append(tag)
        game_tags.sort()

        for i in range(len(game_tags)):
            for j in range(i + 1, len(game_tags)):
                pair = f"{game_tags[i]} + {game_tags[j]}"
                rows.append({"pair": pair, "revenue_mid": game["revenue_mid"]})

    pairs = pd.DataFrame(rows, columns=["pair", "revenue_mid"])
    pairs["profitable"] = pairs["revenue_mid"] >= threshold

    groups = pairs.groupby("pair")
    table = pd.DataFrame()
    table["n_games"] = groups["revenue_mid"].count()
    table["median_revenue"] = groups["revenue_mid"].median()
    table["profitable_share"] = groups["profitable"].mean()

    table = table[table["n_games"] >= min_games]
    return table.sort_values("median_revenue", ascending=False)


def normalize_tag(tag):
    """Put a tag in a comparable form: "Rogue-like " -> "roguelike".

    Steam writes "Rogue-like" while a user will type "Roguelike":
    so we ignore case, surrounding spaces and hyphens.
    """
    return tag.strip().lower().replace("-", "")


def has_all_tags(game_tags, wanted_tags):
    """Return True if the game has every wanted tag (ignoring case and hyphens).

    game_tags: str "Indie,Action" or list of the game's tags.
    wanted_tags: list of wanted tags. An empty list returns True.
    """
    if isinstance(game_tags, str) or game_tags is None:
        game_tags = split_tags(game_tags)

    normalized_game_tags = []
    for tag in game_tags:
        normalized_game_tags.append(normalize_tag(tag))

    for tag in wanted_tags:
        if normalize_tag(tag) not in normalized_game_tags:
            return False
    return True


def find_comparables(df, tags, price=None, since_year=None, price_tolerance=PRICE_TOLERANCE):
    """Find the games comparable to a concept.

    df: DataFrame enriched by add_estimates.
    tags: list of tags that a comparable game must all have.
    price: price of the concept; if given, keep the games within ± price_tolerance.
    since_year: if given, keep the games released that year or later.
    Returns the matching subset of df.
    """
    result = df
    if price is not None:
        low = price * (1 - price_tolerance)
        high = price * (1 + price_tolerance)
        result = result[result["price"] >= low]
        result = result[result["price"] <= high]
    if since_year is not None:
        result = result[result["release_year"] >= since_year]

    # The tag filter comes last because it is the slowest (a Python loop).
    keep = []
    for game_tags in result["tags"]:
        keep.append(has_all_tags(game_tags, tags))
    return result[keep]


def add_price_band(df):
    """Add the price_band column to a copy of df.

    pd.cut puts each price in its PRICE_BINS band (e.g. $12 -> "10-15$").
    """
    df = df.copy()
    df["price_band"] = pd.cut(df["price"], bins=PRICE_BINS, labels=PRICE_LABELS)
    return df


def price_table(comparables, threshold=PROFITABLE_THRESHOLD):
    """By price band: number of games, median revenue and share of profitable games.

    comparables: DataFrame (usually from find_comparables, without a price filter).
    Returns a DataFrame of 6 rows, one per band of PRICE_LABELS.
    """
    games = add_price_band(comparables)
    games["profitable"] = games["revenue_mid"] >= threshold

    # observed=False keeps the empty bands too, so there are always 6 rows.
    groups = games.groupby("price_band", observed=False)
    table = pd.DataFrame()
    table["n_games"] = groups["revenue_mid"].count()
    table["median_revenue"] = groups["revenue_mid"].median()
    table["profitable_share"] = groups["profitable"].mean()
    return table.fillna(0)


def recommend_price(comparables, min_games=MIN_GAMES_PER_PRICE_BAND):
    """Return the price band with the highest median revenue.

    Bands with fewer than min_games games are ignored.
    Returns the band name (str), or None if no band has enough games.
    """
    table = price_table(comparables)
    table = table[table["n_games"] >= min_games]
    if table.empty:
        return None
    return table["median_revenue"].idxmax()
