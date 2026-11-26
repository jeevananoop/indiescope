"""Bonus : transforme le résultat du simulateur en un court avis rédigé par une IA.

Utilise mirascope (cours 6). La clé API se lit dans les variables d'environnement
ou dans un fichier .env (jamais dans le code). Sans clé, l'appli fonctionne sans l'IA.
"""

import os

# Modèle appelé ("fournisseur/modèle"). Modifiable sans toucher au code via la
# variable d'environnement INDIESCOPE_MODEL (ex. "openai/gpt-4o-mini").
MODEL = os.environ.get("INDIESCOPE_MODEL", "anthropic/claude-sonnet-5-5")

# Variable d'environnement qui doit contenir la clé, selon le fournisseur.
API_KEY_VARIABLES = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}

SYSTEM_PROMPT = (
    "Tu es un consultant qui conseille des fondateurs de petits studios de jeux vidéo indépendants. "
    "On te donne les résultats chiffrés d'un simulateur de rentabilité sur Steam. "
    "Rédige un avis de 4 à 5 phrases, en français, clair et direct. "
    "Règles strictes : n'utilise QUE les chiffres fournis, n'invente aucun chiffre, aucun nom de jeu, "
    "aucune statistique. Termine par une phrase qui rappelle une limite de la méthode "
    "(ventes estimées à partir des avis, ni le marketing ni la qualité du jeu ne sont pris en compte)."
)


def result_to_text(result):
    """Transforme le dictionnaire renvoyé par GameConcept.evaluate en texte pour l'IA.

    result : dict renvoyé par evaluate().
    Renvoie une str de quelques lignes.
    """
    p25, median, p75 = result["revenue_range"]
    probas = result["probabilities"]
    return (
        f"Tags du concept : {', '.join(result['tags'])}\n"
        f"Prix prévu : {result['price']:.2f} $\n"
        f"Budget du studio : {result['budget']:,.0f} $\n"
        f"Nombre de jeux comparables : {result['n_comparables']}\n"
        f"Revenu net des comparables (scénario moyen) : 25e percentile {p25:,.0f} $, "
        f"médiane {median:,.0f} $, 75e percentile {p75:,.0f} $\n"
        f"Probabilité de rembourser le budget : scénario bas {probas['low']:.0%}, "
        f"moyen {probas['mid']:.0%}, haut {probas['high']:.0%}\n"
        f"Verdict : {result['recommendation']}\n"
        f"Tranche de prix conseillée : {result['recommended_price'] or 'non déterminée'}\n"
        f"Avertissement : {result['warning'] or 'aucun'}"
    )


def api_key_available(model=MODEL):
    """True si la clé API du fournisseur de model est définie (variable d'environnement ou fichier .env)."""
    # Lit le fichier .env s'il existe. Si la bibliothèque python-dotenv n'est pas
    # installée, on continue avec les seules variables d'environnement.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    provider = model.split("/")[0]          # "anthropic/claude-..." -> "anthropic"
    variable = API_KEY_VARIABLES.get(provider)
    if variable is None:
        return False
    return os.environ.get(variable, "") != ""


def explain_result(result, model=MODEL):
    """Demande à l'IA un avis rédigé sur le résultat du simulateur.

    result : dict renvoyé par GameConcept.evaluate.
    Renvoie le texte de l'avis (str), ou un message clair si l'IA n'est pas disponible.
    L'appli doit marcher sans l'IA : on renvoie un message au lieu de planter.
    """
    if not api_key_available(model):
        return ("ℹ️ L'explication par l'IA n'est pas disponible : aucune clé API trouvée. "
                "Ajoutez ANTHROPIC_API_KEY dans un fichier .env pour l'activer.")
    try:
        from mirascope import llm
    except ImportError:
        return "ℹ️ L'explication par l'IA demande la bibliothèque mirascope (pip install mirascope)."

    # Même syntaxe que le cours sur mirascope : une fonction décorée par @llm.call
    # qui renvoie le message système et le message utilisateur.
    @llm.call(model)
    def advise(results_text: str):
        return [
            llm.messages.system(SYSTEM_PROMPT),
            llm.messages.user(f"Résultats du simulateur :\n{results_text}"),
        ]

    try:
        return advise(result_to_text(result)).text()
    except Exception:
        # Réseau coupé, clé refusée, quota dépassé... : on prévient sans planter.
        return "⚠️ L'IA n'a pas pu répondre. Les résultats ci-dessus restent valables."
