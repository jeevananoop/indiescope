"""Analyse du marché : niches (tags), jeux comparables et revenu par tranche de prix.

Toutes les fonctions prennent un DataFrame enrichi par add_estimates()
(colonnes tags, price, release_year, revenue_low/mid/high).
"""

from itertools import combinations

import pandas as pd

# Un jeu est « rentable » au-delà de 100 000 $ de revenu net : de quoi payer
# environ un an de travail pour une petite équipe indé.
PROFITABLE_THRESHOLD = 100_000

# En dessous de 50 jeux, la médiane d'un tag varie trop d'un jeu à l'autre.
MIN_GAMES_PER_NICHE = 50

# Dynamique : on compare les sorties des 2 dernières années complètes
# (2023-2024) aux 2 précédentes (2021-2022). 2025 est incomplète
# (le dataset s'arrête 6 mois avant mars 2026).
RECENT_YEARS = [2023, 2024]
PREVIOUS_YEARS = [2021, 2022]

# Un comparable doit avoir un prix à ± 50 % du prix du concept.
PRICE_TOLERANCE = 0.5

# En dessous de 30 comparables, les pourcentages ne sont plus fiables
# (un seul jeu pèse plus de 3 points) : l'outil affiche un avertissement.
MIN_COMPARABLES = 30

# Tranches de prix (en dollars) et leurs noms.
PRICE_BINS = [0, 5, 10, 15, 20, 30, float("inf")]
PRICE_LABELS = ["<5$", "5-10$", "10-15$", "15-20$", "20-30$", "30$+"]

# Une tranche de prix doit contenir au moins 10 jeux pour être recommandée.
MIN_GAMES_PER_PRICE_BAND = 10

# Tags qui décrivent un financement, une licence ou un succès passé (donnés
# APRÈS le succès), pas un concept qu'un studio peut choisir.
META_TAGS = ["Games Workshop", "Kickstarter", "Crowdfunded", "Mod", "Moddable", "Cult Classic",
             "Great Soundtrack", "Classic", "Remake", "Sequel", "Epic", "Masterpiece",
             "Mature", "Hentai", "NSFW", "Sexual Content", "Nudity", "Dwarf"]

# Critères d'une niche prometteuse : concurrence limitée, au moins 30 % de
# jeux rentables, et des sorties qui n'ont pas doublé en 2 ans.
PROMISING_MAX_GAMES = 1000
PROMISING_MIN_PROFITABLE_SHARE = 0.30
PROMISING_MAX_GROWTH = 1.0


def split_tags(tag_string):
    """Découpe "Indie,Action" en liste ["Indie", "Action"] (liste vide si case vide)."""
    if not isinstance(tag_string, str):
        return []
    return tag_string.split(",")


def count_tags_loop(df):
    """Compte le nombre de jeux par tag avec une boucle et un dictionnaire.

    Version « à la main » (cours 4, problem 1), pour vérifier la version pandas.
    Renvoie un dict {tag: nombre de jeux}.
    """
    counts = {}
    for tag_string in df["tags"]:
        for tag in split_tags(tag_string):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def explode_tags(df):
    """Renvoie un DataFrame avec une ligne par couple (jeu, tag), dans la colonne tag."""
    exploded = df.assign(tag=df["tags"].str.split(",")).explode("tag")
    return exploded


def niche_table(df, min_games=MIN_GAMES_PER_NICHE, threshold=PROFITABLE_THRESHOLD):
    """Résume chaque niche (tag) : concurrence, revenu médian, part de jeux rentables, dynamique.

    df : DataFrame enrichi par add_estimates.
    min_games : nombre minimum de jeux pour garder un tag.
    threshold : revenu net (scénario moyen) au-delà duquel un jeu est rentable.
    Renvoie un DataFrame indexé par tag, trié par revenu médian décroissant,
    avec les colonnes n_games, median_revenue, mean_revenue, profitable_share,
    recent_releases, previous_releases, growth.
    """
    games = explode_tags(df)
    games["profitable"] = games["revenue_mid"] >= threshold
    games["recent"] = games["release_year"].isin(RECENT_YEARS)
    games["previous"] = games["release_year"].isin(PREVIOUS_YEARS)

    table = games.groupby("tag").agg(
        n_games=("app_id", "count"),
        median_revenue=("revenue_mid", "median"),
        mean_revenue=("revenue_mid", "mean"),
        profitable_share=("profitable", "mean"),
        recent_releases=("recent", "sum"),
        previous_releases=("previous", "sum"),
    )
    table = table[table["n_games"] >= min_games]
    # Croissance des sorties : +0.5 = 50 % de jeux en plus sur les 2 dernières années.
    table["growth"] = table["recent_releases"] / table["previous_releases"].clip(lower=1) - 1
    return table.sort_values("median_revenue", ascending=False)


def promising_niches(niches):
    """Filtre un tableau de niche_table pour ne garder que les niches prometteuses.

    Retire les META_TAGS, puis garde les tags peu encombrés, souvent rentables
    et qui ne se remplissent pas trop vite. Renvoie un DataFrame trié par revenu médian.
    """
    genres = niches.drop(index=[tag for tag in META_TAGS if tag in niches.index])
    return genres[(genres["n_games"] <= PROMISING_MAX_GAMES)
                  & (genres["profitable_share"] >= PROMISING_MIN_PROFITABLE_SHARE)
                  & (genres["growth"] < PROMISING_MAX_GROWTH)]


def tag_pair_table(df, min_games=MIN_GAMES_PER_NICHE, threshold=PROFITABLE_THRESHOLD,
                   top_tags=60):
    """Même analyse que niche_table, mais sur les paires de tags (ex. Roguelike + Deckbuilding).

    Pour limiter le calcul, on ne combine que les top_tags tags les plus fréquents.
    Renvoie un DataFrame indexé par paire "Tag A + Tag B".
    """
    frequent = set(pd.Series(count_tags_loop(df)).nlargest(top_tags).index)
    rows = []
    for tag_string, revenue in zip(df["tags"], df["revenue_mid"]):
        tags = sorted(set(split_tags(tag_string)) & frequent)
        for tag_a, tag_b in combinations(tags, 2):
            rows.append((f"{tag_a} + {tag_b}", revenue))
    pairs = pd.DataFrame(rows, columns=["pair", "revenue_mid"])
    pairs["profitable"] = pairs["revenue_mid"] >= threshold
    table = pairs.groupby("pair").agg(
        n_games=("revenue_mid", "count"),
        median_revenue=("revenue_mid", "median"),
        profitable_share=("profitable", "mean"),
    )
    table = table[table["n_games"] >= min_games]
    return table.sort_values("median_revenue", ascending=False)


def normalize_tag(tag):
    """Met un tag sous une forme comparable : "Rogue-like " -> "roguelike".

    Steam écrit "Rogue-like" alors qu'un utilisateur tapera "Roguelike" :
    on ignore donc la casse, les espaces autour et les tirets.
    """
    return tag.strip().lower().replace("-", "")


def has_all_tags(game_tags, wanted_tags):
    """Renvoie True si le jeu a tous les tags demandés (sans tenir compte de la casse ni des tirets).

    game_tags : str "Indie,Action" ou liste de tags du jeu.
    wanted_tags : liste de tags recherchés. Une liste vide renvoie True.
    """
    if isinstance(game_tags, str) or game_tags is None:
        game_tags = split_tags(game_tags)
    game_set = {normalize_tag(tag) for tag in game_tags}
    wanted_set = {normalize_tag(tag) for tag in wanted_tags}
    return wanted_set <= game_set


def find_comparables(df, tags, price=None, since_year=None, price_tolerance=PRICE_TOLERANCE):
    """Trouve les jeux comparables à un concept.

    df : DataFrame enrichi par add_estimates.
    tags : liste des tags que le jeu comparable doit tous avoir.
    price : prix du concept ; si donné, on garde les jeux à ± price_tolerance.
    since_year : si donné, on garde les jeux sortis cette année-là ou après.
    Renvoie le sous-ensemble de df correspondant.
    """
    # Les filtres rapides (prix, année) passent avant le filtre lent (tags, ligne par ligne).
    result = df
    if price is not None:
        low, high = price * (1 - price_tolerance), price * (1 + price_tolerance)
        result = result[result["price"].between(low, high)]
    if since_year is not None:
        result = result[result["release_year"] >= since_year]
    return result[result["tags"].apply(has_all_tags, args=(tags,))]


def add_price_band(df):
    """Ajoute la colonne price_band (tranche de prix) à une copie de df."""
    df = df.copy()
    df["price_band"] = pd.cut(df["price"], bins=PRICE_BINS, labels=PRICE_LABELS)
    return df


def price_table(comparables, threshold=PROFITABLE_THRESHOLD):
    """Par tranche de prix : nombre de jeux, revenu médian et part de jeux rentables.

    comparables : DataFrame (en général issu de find_comparables, sans filtre de prix).
    Renvoie un DataFrame de 6 lignes, une par tranche de PRICE_LABELS.
    """
    games = add_price_band(comparables)
    games["profitable"] = games["revenue_mid"] >= threshold
    table = games.groupby("price_band", observed=False).agg(
        n_games=("revenue_mid", "count"),
        median_revenue=("revenue_mid", "median"),
        profitable_share=("profitable", "mean"),
    )
    return table.fillna(0)


def recommend_price(comparables, min_games=MIN_GAMES_PER_PRICE_BAND):
    """Renvoie la tranche de prix au revenu médian le plus élevé.

    Les tranches avec moins de min_games jeux sont ignorées.
    Renvoie le nom de la tranche (str), ou None si aucune tranche n'a assez de jeux.
    """
    table = price_table(comparables)
    table = table[table["n_games"] >= min_games]
    if table.empty:
        return None
    return table["median_revenue"].idxmax()
