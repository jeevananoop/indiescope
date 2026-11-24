"""Nettoyage du dataset Steam : games.csv brut -> data/games_clean.csv.

Chaque filtre est une petite fonction ; clean_games() les enchaîne et
renvoie aussi un rapport de qualité (combien de jeux chaque filtre retire).
Lancer `python src/cleaning.py` depuis la racine régénère games_clean.csv.
"""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd

# Colonnes du fichier brut à garder -> leur nom en snake_case (contrat de données).
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

# Les 10 colonnes du contrat de données, dans l'ordre du fichier final.
CLEAN_COLUMNS = [
    "app_id", "name", "release_date", "release_year", "price",
    "positive", "negative", "owners_min", "owners_max", "tags",
]

# Format des dates dans le fichier brut : "Aug 1, 2023".
DATE_FORMAT = "%b %d, %Y"

# Date de collecte du dataset : les sorties s'arrêtent début mars 2026
# (seuls 3 jeux ont une date plus tardive : ce sont des sorties annoncées).
SNAPSHOT_DATE = datetime(2026, 3, 1)

# Un jeu récent n'a pas encore reçu ses avis : on attend 6 mois (~183 jours).
MIN_AGE_DAYS = 183

# Année de début : avant 2015, Steam était un catalogue filtré (Greenlight
# naissant, moins de 2 500 sorties par an) ; le marché ne ressemble pas à
# celui d'aujourd'hui, où sortent 20 000 jeux par an.
START_YEAR = 2015

# Séparateur unique des tags dans le fichier propre.
TAG_SEPARATOR = ","


def select_and_rename(df):
    """Garde les colonnes utiles et les renomme en snake_case.

    df : DataFrame brut renvoyé par load_games.
    Renvoie un nouveau DataFrame avec les colonnes de RAW_TO_CLEAN.
    """
    return df[list(RAW_TO_CLEAN)].rename(columns=RAW_TO_CLEAN)


def drop_duplicates_and_unnamed(df):
    """Retire les doublons d'AppID et les jeux sans nom.

    On dédoublonne sur app_id, l'identifiant unique de Steam : deux jeux
    différents peuvent porter le même nom (par exemple "Solitaire").
    """
    df = df.drop_duplicates(subset="app_id")
    has_name = df["name"].notna() & (df["name"].str.strip() != "")
    return df[has_name]


def restore_full_price(df):
    """Remplace le prix soldé par le prix plein, et retire les prix impossibles à retrouver.

    Piège n°2 du dataset : la colonne Price est le prix affiché le jour de
    la collecte, remise comprise (Hollow Knight : 7,49 $ avec -50 %, pour
    un prix plein de 14,99 $). Prix plein = prix / (1 - remise / 100).
    Avec une remise de 100 %, le prix plein est impossible à retrouver.
    """
    df = df[df["discount"] < 100].copy()
    df["price"] = (df["price"] / (1 - df["discount"] / 100)).round(2)
    return df.drop(columns="discount")


def drop_free_games(df):
    """Retire les jeux gratuits : sans prix, pas de revenu de vente à estimer."""
    return df[df["price"] > 0]


def parse_date(text):
    """Transforme "Aug 1, 2023" en datetime, ou renvoie None si illisible.

    text : str (ou valeur manquante).
    Renvoie un datetime.datetime, ou None.
    """
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT)
    except (ValueError, AttributeError):
        # ValueError : format différent ; AttributeError : case vide (NaN).
        return None


def add_release_date(df):
    """Convertit release_date en vraie date, crée release_year, retire les dates illisibles."""
    df = df.copy()
    df["release_date"] = pd.to_datetime(df["release_date"].apply(parse_date))
    df = df[df["release_date"].notna()].copy()
    df["release_year"] = df["release_date"].dt.year
    return df


def parse_owners(text):
    """Transforme "20000 - 50000" en tuple (20000, 50000), ou (None, None) si vide.

    text : str (ou valeur manquante).
    Renvoie un tuple de deux int, ou (None, None).
    """
    try:
        low, high = text.split(" - ")
        return int(low), int(high)
    except (ValueError, AttributeError):
        return None, None


def add_owners_range(df):
    """Découpe owners en owners_min et owners_max (entiers) et retire les cases illisibles."""
    df = df.copy()
    pairs = df["owners"].apply(parse_owners)
    df["owners_min"] = pairs.str[0]
    df["owners_max"] = pairs.str[1]
    df = df[df["owners_min"].notna()].copy()
    df["owners_min"] = df["owners_min"].astype(int)
    df["owners_max"] = df["owners_max"].astype(int)
    return df.drop(columns="owners")


def clean_tag_string(text):
    """Rend une chaîne de tags homogène : "Indie , Action" -> "Indie,Action".

    Renvoie None si la case est vide ou ne contient aucun tag.
    """
    if not isinstance(text, str):
        return None
    tags = [tag.strip() for tag in text.split(TAG_SEPARATOR) if tag.strip()]
    if not tags:
        return None
    return TAG_SEPARATOR.join(tags)


def normalize_tags(df):
    """Homogénéise les tags et retire les jeux sans tag.

    Un jeu sans tag ne peut être comparé à aucun concept : il est inutile au simulateur.
    """
    df = df.copy()
    df["tags"] = df["tags"].apply(clean_tag_string)
    return df[df["tags"].notna()]


def drop_recent_games(df, snapshot_date=SNAPSHOT_DATE, min_age_days=MIN_AGE_DAYS):
    """Retire les jeux sortis moins de min_age_days avant la date de collecte.

    Retire aussi, au passage, les sorties annoncées (dates dans le futur).
    """
    cutoff = snapshot_date - timedelta(days=min_age_days)
    return df[df["release_date"] <= cutoff]


def drop_old_games(df, start_year=START_YEAR):
    """Retire les jeux sortis avant start_year (voir la constante START_YEAR)."""
    return df[df["release_year"] >= start_year]


# Chaque étape : (nom, fonction, raison). L'ordre compte : la date doit être
# convertie avant les filtres sur l'âge et l'année.
CLEANING_STEPS = [
    ("Colonnes du contrat", select_and_rename, "Garder les colonnes utiles, renommées en snake_case"),
    ("Doublons et sans nom", drop_duplicates_and_unnamed, "Un jeu compté deux fois fausse les statistiques"),
    ("Remise de 100 %", restore_full_price, "Prix plein impossible à retrouver (le prix soldé est corrigé)"),
    ("Jeux gratuits", drop_free_games, "Sans prix, pas de revenu de vente à estimer"),
    ("Dates illisibles", add_release_date, "Impossible de situer le jeu dans le temps"),
    ("Owners illisibles", add_owners_range, "Impossible de valider l'estimation des ventes"),
    ("Jeux sans tag", normalize_tags, "Impossible de les comparer à un concept"),
    ("Sortis il y a moins de 6 mois", drop_recent_games, "Leurs avis n'ont pas eu le temps d'arriver"),
    (f"Sortis avant {START_YEAR}", drop_old_games, "Le marché d'avant 2015 ne ressemble pas à celui d'aujourd'hui"),
]


def clean_games(df):
    """Enchaîne toutes les étapes de nettoyage et mesure ce que chacune retire.

    df : DataFrame brut renvoyé par load_games.
    Renvoie un tuple (df_clean, report) :
    - df_clean : DataFrame conforme au contrat (10 colonnes de CLEAN_COLUMNS) ;
    - report : DataFrame du rapport de qualité (étape, lignes retirées,
      lignes restantes, raison).
    """
    rows_left = {"Départ (fichier brut)": len(df)}
    reasons = {"Départ (fichier brut)": ""}
    for name, step, reason in CLEANING_STEPS:
        df = step(df)
        rows_left[name] = len(df)
        reasons[name] = reason

    report = pd.DataFrame({"étape": list(rows_left), "lignes restantes": list(rows_left.values())})
    report["lignes retirées"] = (-report["lignes restantes"].diff()).fillna(0).astype(int)
    report["raison"] = report["étape"].map(reasons)
    report = report[["étape", "lignes retirées", "lignes restantes", "raison"]]

    df_clean = df[CLEAN_COLUMNS].reset_index(drop=True)
    return df_clean, report


def load_clean(path):
    """Recharge games_clean.csv avec les bons types (la date redevient une date)."""
    return pd.read_csv(path, parse_dates=["release_date"])


if __name__ == "__main__":
    # Permet de lancer "python src/cleaning.py" depuis la racine du projet.
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_dir)
    from src.data_loader import load_games

    raw = load_games(os.path.join(project_dir, "data", "games.csv"), usecols=list(RAW_TO_CLEAN))
    clean, quality = clean_games(raw)
    out_path = os.path.join(project_dir, "data", "games_clean.csv")
    clean.to_csv(out_path, index=False)
    print(quality.to_string(index=False))
    print(f"\n{len(clean)} jeux enregistrés dans {out_path}")
