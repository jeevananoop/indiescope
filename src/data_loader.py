"""Chargement du fichier brut games.csv (Steam Games Dataset, FronkonGames).

Ce module corrige le décalage de colonnes du fichier source et renvoie
un DataFrame pandas dont chaque nom de colonne correspond à son contenu.
"""

import pandas as pd

# Liste des 40 vrais noms de colonnes. L'en-tête du fichier n'en contient
# que 39, car "Discount" et "DLC count" y sont collés en "DiscountDLC count".
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
    """Charge games.csv en corrigeant le décalage de colonnes.

    Le problème : l'en-tête du fichier a 39 noms, mais chaque ligne a
    40 valeurs ("Discount" et "DLC count" sont fusionnés en un seul nom).
    Avec un simple pd.read_csv, pandas prend alors la 1re valeur (AppID)
    comme index, et chaque nom se retrouve au-dessus de la colonne
    suivante : "Name" contient la date, "Price" contient la remise, etc.
    La correction : ignorer l'en-tête du fichier (header=0 + names=...)
    et donner nous-mêmes la liste des 40 noms, sans colonne d'index.

    Paramètres
    ----------
    path : str
        Chemin vers games.csv.
    usecols : list of str, optional
        Colonnes à garder (None = toutes). Charger moins de colonnes
        économise beaucoup de mémoire sur un fichier de 400 Mo.

    Renvoie
    -------
    pandas.DataFrame
        Une ligne par jeu, avec des colonnes aux bons noms.
    """
    return pd.read_csv(
        path,
        header=0,             # la 1re ligne est l'en-tête faux : on la saute
        names=COLUMN_NAMES,   # et on la remplace par les 40 bons noms
        index_col=False,      # aucune colonne ne doit servir d'index
        usecols=usecols,
    )
