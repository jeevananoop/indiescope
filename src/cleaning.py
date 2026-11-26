"""Nettoyage du dataset Steam : games.csv brut -> data/games_clean.csv.

Chaque filtre est une petite fonction. clean_games() les appelle l'une après
l'autre et construit un rapport de qualité (combien de jeux chaque filtre retire).
Lancer `python src/cleaning.py` depuis la racine du projet régénère games_clean.csv.
"""

import os
from datetime import datetime, timedelta

import pandas as pd

# Colonnes du fichier brut à garder, et leur nouveau nom.
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

# Les 10 colonnes du fichier final, dans l'ordre.
CLEAN_COLUMNS = [
    "app_id", "name", "release_date", "release_year", "price",
    "positive", "negative", "owners_min", "owners_max", "tags",
]

# Format des dates dans le fichier brut : "Aug 1, 2023".
DATE_FORMAT = "%b %d, %Y"

# Date de collecte du dataset : les sorties s'arrêtent début mars 2026.
SNAPSHOT_DATE = datetime(2026, 3, 1)

# Un jeu récent n'a pas encore reçu ses avis : on attend 6 mois (183 jours).
MIN_AGE_DAYS = 183

# Avant 2015, Steam publiait moins de 2 500 jeux par an : ce marché ne
# ressemble pas à celui d'aujourd'hui (20 000 sorties par an).
START_YEAR = 2015


def select_and_rename(df):
    """Garde les colonnes utiles et leur donne un nom simple."""
    columns_to_keep = list(RAW_TO_CLEAN.keys())
    df = df[columns_to_keep]
    df = df.rename(columns=RAW_TO_CLEAN)
    return df


def drop_duplicates_and_unnamed(df):
    """Retire les doublons d'AppID et les jeux sans nom.

    On dédoublonne sur app_id (l'identifiant Steam) et pas sur le nom,
    car deux jeux différents peuvent avoir le même nom (ex. "Solitaire").
    """
    df = df.drop_duplicates(subset="app_id")
    df = df[df["name"].notna()]
    df = df[df["name"].str.strip() != ""]
    return df


def restore_full_price(df):
    """Remplace le prix soldé par le prix plein.

    La colonne Price est le prix du jour de la collecte, remise comprise
    (Hollow Knight : 7,49 $ à -50 %, pour un prix plein de 14,99 $).
    Prix plein = prix / (1 - remise / 100).
    - Remise vide : on la lit comme 0 %.
    - Remise de 100 % : le prix plein est impossible à retrouver, on retire le jeu.
    """
    # .copy() : on travaille sur une copie pour ne pas modifier le tableau d'origine.
    df = df.copy()
    df["discount"] = df["discount"].fillna(0)
    df = df[df["discount"] < 100].copy()
    df["price"] = df["price"] / (1 - df["discount"] / 100)
    df["price"] = df["price"].round(2)
    df = df.drop(columns="discount")
    return df


def drop_free_games(df):
    """Retire les jeux gratuits : sans prix, pas de revenu de vente à estimer."""
    return df[df["price"] > 0]


def parse_date(text):
    """Transforme "Aug 1, 2023" en date, ou renvoie None si c'est illisible."""
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT)
    except (ValueError, AttributeError):
        # ValueError : format différent. AttributeError : case vide.
        return None


def add_release_date(df):
    """Convertit release_date en vraie date, ajoute release_year et retire les dates illisibles."""
    df = df.copy()
    df["release_date"] = df["release_date"].apply(parse_date)
    df = df[df["release_date"].notna()].copy()
    df["release_date"] = pd.to_datetime(df["release_date"])
    df["release_year"] = df["release_date"].dt.year
    return df


def parse_owners(text):
    """Transforme "20000 - 50000" en (20000, 50000), ou (None, None) si c'est illisible."""
    try:
        low, high = text.split(" - ")
        return int(low), int(high)
    except (ValueError, AttributeError):
        return None, None


def add_owners_range(df):
    """Découpe owners en deux colonnes, owners_min et owners_max, et retire les cases illisibles."""
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
    """Nettoie une chaîne de tags : " Indie , Action,," -> "Indie,Action".

    Renvoie None si la case est vide ou ne contient aucun tag.
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
    """Nettoie les tags et retire les jeux sans tag (impossibles à comparer à un concept)."""
    df = df.copy()
    df["tags"] = df["tags"].apply(clean_tag_string)
    df = df[df["tags"].notna()]
    return df


def drop_recent_games(df):
    """Retire les jeux sortis moins de 6 mois avant la date de collecte.

    Retire aussi les sorties annoncées (dates dans le futur).
    """
    cutoff = SNAPSHOT_DATE - timedelta(days=MIN_AGE_DAYS)
    return df[df["release_date"] <= cutoff]


def drop_old_games(df):
    """Retire les jeux sortis avant START_YEAR."""
    return df[df["release_year"] >= START_YEAR]


def add_report_line(report_rows, step, df, reason):
    """Ajoute une ligne au rapport de qualité : nom de l'étape, lignes restantes, raison."""
    report_rows.append({"étape": step, "lignes restantes": len(df), "raison": reason})


def clean_games(df):
    """Applique toutes les étapes de nettoyage et mesure ce que chacune retire.

    Renvoie deux DataFrames :
    - df_clean : les jeux nettoyés (les 10 colonnes de CLEAN_COLUMNS) ;
    - report : le rapport de qualité (une ligne par étape).
    L'ordre compte : la date doit être convertie avant les filtres sur l'âge et l'année.
    """
    report_rows = []
    add_report_line(report_rows, "Départ (fichier brut)", df, "")

    df = select_and_rename(df)
    add_report_line(report_rows, "Colonnes du contrat", df, "Garder les colonnes utiles, renommées en snake_case")

    df = drop_duplicates_and_unnamed(df)
    add_report_line(report_rows, "Doublons et sans nom", df, "Un jeu compté deux fois fausse les statistiques")

    df = restore_full_price(df)
    add_report_line(report_rows, "Remise de 100 %", df, "Prix plein impossible à retrouver (le prix soldé est corrigé)")

    df = drop_free_games(df)
    add_report_line(report_rows, "Jeux gratuits", df, "Sans prix, pas de revenu de vente à estimer")

    df = add_release_date(df)
    add_report_line(report_rows, "Dates illisibles", df, "Impossible de situer le jeu dans le temps")

    df = add_owners_range(df)
    add_report_line(report_rows, "Owners illisibles", df, "Impossible de valider l'estimation des ventes")

    df = normalize_tags(df)
    add_report_line(report_rows, "Jeux sans tag", df, "Impossible de les comparer à un concept")

    df = drop_recent_games(df)
    add_report_line(report_rows, "Sortis il y a moins de 6 mois", df, "Leurs avis n'ont pas eu le temps d'arriver")

    df = drop_old_games(df)
    add_report_line(report_rows, "Sortis avant 2015", df, "Le marché d'avant 2015 ne ressemble pas à celui d'aujourd'hui")

    # Pour chaque étape : lignes retirées = lignes restantes avant - lignes restantes après.
    n_raw = report_rows[0]["lignes restantes"]
    rows_before = n_raw
    for row in report_rows:
        row["lignes retirées"] = rows_before - row["lignes restantes"]
        row["% du brut retiré"] = round(100 * row["lignes retirées"] / n_raw, 1)
        rows_before = row["lignes restantes"]

    report = pd.DataFrame(report_rows)
    report = report[["étape", "lignes retirées", "% du brut retiré", "lignes restantes", "raison"]]

    df_clean = df[CLEAN_COLUMNS].reset_index(drop=True)
    return df_clean, report


def load_clean(path):
    """Recharge games_clean.csv en relisant release_date comme une date."""
    return pd.read_csv(path, parse_dates=["release_date"])


if __name__ == "__main__":
    # À lancer depuis la racine du projet : python src/cleaning.py
    from data_loader import load_games

    raw = load_games(os.path.join("data", "games.csv"), usecols=list(RAW_TO_CLEAN.keys()))
    clean, quality = clean_games(raw)
    out_path = os.path.join("data", "games_clean.csv")
    clean.to_csv(out_path, index=False)
    print(quality.to_string(index=False))
    print(f"\n{len(clean)} jeux enregistrés dans {out_path}")
