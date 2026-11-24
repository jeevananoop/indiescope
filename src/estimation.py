"""Estimation des ventes et du revenu net de chaque jeu, en 3 scénarios.

Steam ne publie pas les ventes : on les estime à partir du nombre d'avis
(méthode Boxleiter). Chaque hypothèse est une constante commentée ci-dessous.
"""

# Ventes par avis (méthode Boxleiter) : un jeu reçoit en moyenne 1 avis
# pour 20 à 60 ventes (règle empirique de l'industrie). 40 est la valeur
# centrale. Validation (notebook 03_estimation) : nos ventes sont plutôt
# sous la fourchette SteamSpy (estimation prudente), et les ventes officielles
# de Valheim, Balatro et Hollow Knight tombent entre les scénarios bas et moyen.
SALES_PER_REVIEW = {"low": 20, "mid": 40, "high": 60}

# Part du prix gardée par Steam : 30 % (taux standard sous 10 M$ de revenu).
STEAM_SHARE = 0.30

# Part des ventes remboursées : Steam rembourse sur demande (moins de 2 h
# de jeu, moins de 14 jours). On retient un ordre de grandeur de 10 %.
REFUND_RATE = 0.10

# Prix moyen réellement payé / prix affiché : une grande partie des ventes
# se fait pendant les soldes. On retient une remise moyenne de 25 %.
PRICE_PAID_RATIO = 0.75

SCENARIOS = list(SALES_PER_REVIEW)


def estimate_sales(n_reviews, scenario="mid"):
    """Estime le nombre de ventes à partir du nombre d'avis.

    n_reviews : int ou pandas.Series, nombre total d'avis (positifs + négatifs).
    scenario : "low", "mid" ou "high" (clé de SALES_PER_REVIEW).
    Renvoie le nombre de ventes estimé (même type que n_reviews).
    """
    if scenario not in SALES_PER_REVIEW:
        raise ValueError(f"Scénario inconnu : {scenario}. Choisir parmi {SCENARIOS}.")
    return n_reviews * SALES_PER_REVIEW[scenario]


def net_revenue(sales, price, refund_rate=REFUND_RATE, price_paid_ratio=PRICE_PAID_RATIO):
    """Calcule le revenu net du studio (après Steam, remboursements et promotions).

    sales : int/float ou Series, nombre de ventes.
    price : float ou Series, prix affiché en dollars.
    refund_rate : part des ventes remboursées (0 pour l'ignorer).
    price_paid_ratio : prix moyen payé / prix affiché (1 pour l'ignorer).
    Renvoie le revenu net en dollars.
    """
    kept_sales = sales * (1 - refund_rate)
    price_paid = price * price_paid_ratio
    return kept_sales * price_paid * (1 - STEAM_SHARE)


def add_estimates(df, refund_rate=REFUND_RATE, price_paid_ratio=PRICE_PAID_RATIO):
    """Ajoute le nombre d'avis, les ventes et le revenu net dans les 3 scénarios.

    df : DataFrame propre (contrat de données : colonnes positive, negative, price).
    Renvoie une copie de df avec les colonnes reviews, sales_low/mid/high
    et revenue_low/mid/high.
    """
    df = df.copy()
    df["reviews"] = df["positive"] + df["negative"]
    for scenario in SCENARIOS:
        sales = estimate_sales(df["reviews"], scenario)
        df[f"sales_{scenario}"] = sales
        df[f"revenue_{scenario}"] = net_revenue(sales, df["price"], refund_rate, price_paid_ratio)
    return df
