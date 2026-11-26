"""Clean the Steam dataset: raw games.csv -> data/games_clean.csv.

Each filter is a small function. clean_games() calls them one after the other
and builds a quality report (how many games each filter removes).
Run `python src/cleaning.py` from the project root to rebuild games_clean.csv.
"""

import os
from datetime import datetime, timedelta

import pandas as pd

# Columns of the raw file to keep, and their new name.
RAW_TO_CLEAN = {
    "AppID": "app_id",
    "Name": "name",
    "Release date": "release_date",
    "Price": "price",
    "Discount": "discount",
    "Positive": "positive",
    "Negative": "negative",
    "Estimated owners": "owners",
    "Tags": "tags",
}

# The 10 columns of the final file, in order.
CLEAN_COLUMNS = [
    "app_id", "name", "release_date", "release_year", "price",
    "positive", "negative", "owners_min", "owners_max", "tags",
]

# Date format in the raw file: "Aug 1, 2023".
DATE_FORMAT = "%b %d, %Y"

# Collection date of the dataset: releases stop in early March 2026.
SNAPSHOT_DATE = datetime(2026, 3, 1)

# A recent game has not received its reviews yet: we wait 6 months (183 days).
MIN_AGE_DAYS = 183

# Before 2015, Steam released fewer than 2,500 games a year: that market
# does not look like today's (20,000 releases a year).
START_YEAR = 2015


def select_and_rename(df):
    """Keep the useful columns and give them a simple name."""
    columns_to_keep = list(RAW_TO_CLEAN.keys())
    df = df[columns_to_keep]
    df = df.rename(columns=RAW_TO_CLEAN)
    return df


def drop_duplicates_and_unnamed(df):
    """Remove duplicate AppIDs and games without a name.

    We remove duplicates on app_id (the Steam identifier) and not on the name,
    because two different games can share a name (e.g. "Solitaire").
    """
    df = df.drop_duplicates(subset="app_id")
    df = df[df["name"].notna()]
    df = df[df["name"].str.strip() != ""]
    return df


def restore_full_price(df):
    """Replace the discounted price with the full price.

    The Price column is the price on the day of collection, discount included
    (Hollow Knight: $7.49 at -50 %, for a full price of $14.99).
    Full price = price / (1 - discount / 100).
    - Empty discount: read as 0 %.
    - 100 % discount: the full price cannot be recovered, so the game is removed.
    """
    df = df.copy()
    df["discount"] = df["discount"].fillna(0)
    df = df[df["discount"] < 100].copy()
    df["price"] = df["price"] / (1 - df["discount"] / 100)
    df["price"] = df["price"].round(2)
    df = df.drop(columns="discount")
    return df


def drop_free_games(df):
    """Remove free games: without a price, there is no sales revenue to estimate."""
    return df[df["price"] > 0]


def parse_date(text):
    """Turn "Aug 1, 2023" into a date, or return None if it cannot be read."""
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT)
    except (ValueError, AttributeError):
        # ValueError: another format. AttributeError: empty cell.
        return None


def add_release_date(df):
    """Convert release_date to a real date, add release_year and remove unreadable dates."""
    df = df.copy()
    df["release_date"] = df["release_date"].apply(parse_date)
    df = df[df["release_date"].notna()].copy()
    df["release_date"] = pd.to_datetime(df["release_date"])
    df["release_year"] = df["release_date"].dt.year
    return df


def parse_owners(text):
    """Turn "20000 - 50000" into (20000, 50000), or (None, None) if it cannot be read."""
    try:
        low, high = text.split(" - ")
        return int(low), int(high)
    except (ValueError, AttributeError):
        return None, None


def add_owners_range(df):
    """Split owners into two columns, owners_min and owners_max, and remove unreadable cells."""
    owners_min = []
    owners_max = []
    for text in df["owners"]:
        low, high = parse_owners(text)
        owners_min.append(low)
        owners_max.append(high)

    df = df.copy()
    df["owners_min"] = owners_min
    df["owners_max"] = owners_max
    df = df[df["owners_min"].notna()].copy()
    df["owners_min"] = df["owners_min"].astype(int)
    df["owners_max"] = df["owners_max"].astype(int)
    df = df.drop(columns="owners")
    return df


def clean_tag_string(text):
    """Clean a tag string: " Indie , Action,," -> "Indie,Action".

    Returns None if the cell is empty or contains no tag.
    """
    if not isinstance(text, str):
        return None
    tags = []
    for tag in text.split(","):
        tag = tag.strip()
        if tag != "":
            tags.append(tag)
    if len(tags) == 0:
        return None
    return ",".join(tags)


def normalize_tags(df):
    """Clean the tags and remove games without a tag (they cannot be compared to a concept)."""
    df = df.copy()
    df["tags"] = df["tags"].apply(clean_tag_string)
    df = df[df["tags"].notna()]
    return df


def drop_recent_games(df):
    """Remove games released less than 6 months before the collection date.

    This also removes announced releases (dates in the future).
    """
    cutoff = SNAPSHOT_DATE - timedelta(days=MIN_AGE_DAYS)
    return df[df["release_date"] <= cutoff]


def drop_old_games(df):
    """Remove games released before START_YEAR."""
    return df[df["release_year"] >= START_YEAR]


def add_report_line(report_rows, step, df, reason):
    """Add a line to the quality report: step name, rows left, reason."""
    report_rows.append({"step": step, "rows left": len(df), "reason": reason})


def clean_games(df):
    """Apply every cleaning step and measure what each one removes.

    Returns two DataFrames:
    - df_clean: the cleaned games (the 10 columns of CLEAN_COLUMNS);
    - report: the quality report (one line per step).
    Order matters: the date must be converted before the age and year filters.
    """
    report_rows = []
    add_report_line(report_rows, "Start (raw file)", df, "")

    df = select_and_rename(df)
    add_report_line(report_rows, "Contract columns", df, "Keep the useful columns, renamed in snake_case")

    df = drop_duplicates_and_unnamed(df)
    add_report_line(report_rows, "Duplicates and unnamed", df, "A game counted twice distorts the statistics")

    df = restore_full_price(df)
    add_report_line(report_rows, "100 % discount", df, "Full price cannot be recovered (other discounted prices are fixed)")

    df = drop_free_games(df)
    add_report_line(report_rows, "Free games", df, "No price, so no sales revenue to estimate")

    df = add_release_date(df)
    add_report_line(report_rows, "Unreadable dates", df, "The game cannot be placed in time")

    df = add_owners_range(df)
    add_report_line(report_rows, "Unreadable owners", df, "The sales estimate cannot be checked")

    df = normalize_tags(df)
    add_report_line(report_rows, "Games without tags", df, "They cannot be compared to a concept")

    df = drop_recent_games(df)
    add_report_line(report_rows, "Released less than 6 months ago", df, "Their reviews have not had time to come in")

    df = drop_old_games(df)
    add_report_line(report_rows, "Released before 2015", df, "The pre-2015 market does not look like today's")

    n_raw = report_rows[0]["rows left"]
    rows_before = n_raw
    for row in report_rows:
        row["rows removed"] = rows_before - row["rows left"]
        row["% of raw removed"] = round(100 * row["rows removed"] / n_raw, 1)
        rows_before = row["rows left"]

    report = pd.DataFrame(report_rows)
    report = report[["step", "rows removed", "% of raw removed", "rows left", "reason"]]

    df_clean = df[CLEAN_COLUMNS].reset_index(drop=True)
    return df_clean, report


def load_clean(path):
    """Reload games_clean.csv, reading release_date back as a date."""
    return pd.read_csv(path, parse_dates=["release_date"])


if __name__ == "__main__":
    # Run from the project root: python src/cleaning.py
    from data_loader import load_games

    raw = load_games(os.path.join("data", "games.csv"), usecols=list(RAW_TO_CLEAN.keys()))
    clean, quality = clean_games(raw)
    out_path = os.path.join("data", "games_clean.csv")
    clean.to_csv(out_path, index=False)
    print(quality.to_string(index=False))
    print(f"\n{len(clean)} games saved to {out_path}")
