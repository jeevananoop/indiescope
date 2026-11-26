"""Load the raw games.csv file (Steam Games Dataset, FronkonGames).

This module fixes the column shift in the source file and returns a pandas
DataFrame in which every column name matches its content.
"""

import pandas as pd

# The 40 real column names. The file header only has 39, because "Discount"
# and "DLC count" are glued together as "DiscountDLC count".
COLUMN_NAMES = [
    "AppID", "Name", "Release date", "Estimated owners", "Peak CCU",
    "Required age", "Price", "Discount", "DLC count", "About the game",
    "Supported languages", "Full audio languages", "Reviews", "Header image",
    "Website", "Support url", "Support email", "Windows", "Mac", "Linux",
    "Metacritic score", "Metacritic url", "User score", "Positive", "Negative",
    "Score rank", "Achievements", "Recommendations", "Notes",
    "Average playtime forever", "Average playtime two weeks",
    "Median playtime forever", "Median playtime two weeks", "Developers",
    "Publishers", "Categories", "Genres", "Tags", "Screenshots", "Movies",
]


def load_games(path, usecols=None):
    """Load games.csv and fix the column shift.

    The problem: the header has 39 names, but every row has 40 values
    ("Discount" and "DLC count" are merged into one name). With a plain
    pd.read_csv, pandas then uses the 1st value (AppID) as the index, and
    every name ends up above the next column: "Name" holds the date,
    "Price" holds the discount, and so on.
    The fix: skip the file header (header=0 + names=...) and pass the
    40 names ourselves, with no index column.

    path: path to games.csv.
    usecols: list of columns to keep (None = all). Loading fewer columns
    saves a lot of memory on a 400 MB file.
    Returns a DataFrame: one row per game, with correctly named columns.
    """
    return pd.read_csv(
        path,
        header=0,             # the 1st line is the wrong header: skip it
        names=COLUMN_NAMES,   # and replace it with the 40 correct names
        index_col=False,      # no column must be used as the index
        usecols=usecols,
    )
