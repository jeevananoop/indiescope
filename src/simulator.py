"""Simulateur go / no-go : un concept de jeu -> probabilité de rembourser son budget.

La classe GameConcept regroupe les données d'un concept (tags, prix, budget) ;
toute la logique reste dans les fonctions des modules estimation et analysis.
"""

from src.analysis import MIN_COMPARABLES, find_comparables, recommend_price
from src.estimation import SCENARIOS

# Seuils de recommandation, du plus haut au plus bas.
# GO : au moins 1 jeu comparable sur 2 a remboursé ce budget (pile ou face favorable).
# RISKY : entre 1 sur 4 et 1 sur 2 : faisable, mais un échec est probable.
# NO-GO : moins d'1 jeu sur 4 : le budget est trop élevé pour cette niche.
GO_THRESHOLD = 0.50
RISKY_THRESHOLD = 0.25

# Les comparables doivent être sortis après cette année (marché récent),
# sauf si ce filtre laisse moins de MIN_COMPARABLES jeux.
RECENT_SINCE_YEAR = 2020

# Percentiles de la fourchette de revenu affichée (pessimiste, typique, optimiste).
REVENUE_PERCENTILES = (0.25, 0.50, 0.75)


def break_even_probability(comparables, budget, scenario="mid"):
    """Part des jeux comparables dont le revenu net dépasse le budget.

    comparables : DataFrame enrichi par add_estimates.
    budget : float, budget du studio en dollars.
    scenario : "low", "mid" ou "high".
    Renvoie un float entre 0 et 1 (0.0 s'il n'y a aucun comparable).
    """
    if len(comparables) == 0:
        return 0.0
    return float((comparables[f"revenue_{scenario}"] >= budget).mean())


def recommendation(probability):
    """Transforme une probabilité en verdict "GO", "RISKY" ou "NO-GO".

    Les seuils sont testés du plus haut au plus bas : sinon tout tomberait
    dans la première condition.
    """
    if probability >= GO_THRESHOLD:
        return "GO"
    elif probability >= RISKY_THRESHOLD:
        return "RISKY"
    else:
        return "NO-GO"


def revenue_range(comparables, scenario="mid"):
    """Fourchette de revenu : 25e percentile, médiane, 75e percentile.

    Renvoie un tuple de 3 floats, ou (0.0, 0.0, 0.0) sans comparable.
    """
    if len(comparables) == 0:
        return (0.0, 0.0, 0.0)
    quantiles = comparables[f"revenue_{scenario}"].quantile(list(REVENUE_PERCENTILES))
    return tuple(float(value) for value in quantiles)


class GameConcept:
    """Un concept de jeu à évaluer : ses tags, son prix et le budget du studio."""

    def __init__(self, tags, price, budget):
        """Vérifie et stocke le concept.

        tags : liste non vide de tags Steam (str).
        price : prix de vente prévu en dollars (> 0).
        budget : budget du studio en dollars (> 0).
        Lève ValueError si une entrée est invalide.
        """
        if not tags:
            raise ValueError("Choisissez au moins un tag.")
        if price is None or price <= 0:
            raise ValueError("Le prix doit être strictement positif.")
        if budget is None or budget <= 0:
            raise ValueError("Le budget doit être strictement positif.")
        self.tags = list(tags)
        self.price = float(price)
        self.budget = float(budget)
        self.result = None
        self.niche = None         # jeux avec les mêmes tags, rempli par evaluate
        self.comparables = None   # niche filtrée par prix et année, rempli par evaluate

    def find_comparables(self, df):
        """Comparables récents (même tags, prix ± 50 %), ou tous les ans si trop peu de jeux récents."""
        recent = find_comparables(df, self.tags, price=self.price, since_year=RECENT_SINCE_YEAR)
        if len(recent) >= MIN_COMPARABLES:
            return recent
        return find_comparables(df, self.tags, price=self.price)

    def evaluate(self, df):
        """Évalue le concept sur le marché df (DataFrame enrichi par add_estimates).

        Renvoie un dictionnaire : tags, price, budget, n_comparables,
        revenue_range (p25, médiane, p75 en scénario moyen), probabilities
        (une par scénario), recommendation (scénario moyen), recommendations
        (une par scénario), recommended_price, warning (str ou None).
        """
        # La niche (mêmes tags, tous prix) sert au prix conseillé ; les comparables
        # sont cherchés dans la niche, ce qui évite de reparcourir tout le marché.
        niche = find_comparables(df, self.tags)
        comparables = self.find_comparables(niche)
        self.niche, self.comparables = niche, comparables
        probabilities = {s: break_even_probability(comparables, self.budget, s) for s in SCENARIOS}

        warning = None
        if len(comparables) == 0:
            warning = "Aucun jeu comparable : impossible d'évaluer ce concept."
        elif len(comparables) < MIN_COMPARABLES:
            warning = (f"Seulement {len(comparables)} jeux comparables (minimum conseillé : "
                       f"{MIN_COMPARABLES}) : résultat peu fiable.")

        verdict = recommendation(probabilities["mid"])
        # Sans assez de preuves, on ne conseille jamais GO : 1 succès sur 1 jeu
        # ne prouve rien. Le verdict est plafonné à RISKY.
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
            "recommendations": {s: recommendation(p) for s, p in probabilities.items()},
            "recommended_price": recommend_price(niche),
            "warning": warning,
        }
        return self.result

    def summary(self):
        """Renvoie une phrase lisible résumant la dernière évaluation."""
        if self.result is None:
            return "Concept pas encore évalué : appelez evaluate(df) d'abord."
        r = self.result
        budget = f"{r['budget']:,.0f}".replace(",", " ")  # 60000 -> "60 000"
        text = (f"{r['n_comparables']} jeux comparables, {r['probabilities']['mid']:.0%} ont remboursé "
                f"{budget} $ : {r['recommendation']}. "
                f"Prix conseillé : {r['recommended_price'] or 'non déterminé'}.")
        if r["warning"]:
            text += f" Attention : {r['warning']}"
        return text
