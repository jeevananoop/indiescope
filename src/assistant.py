"""Bonus: turn the simulator result into a short piece of advice written by an AI.

Uses mirascope (course 6). The API key is read from the environment variables
or from a .env file (never from the code). Without a key, the app works without the AI.
"""

import os

# Model called ("provider/model"). It can be changed without touching the code
# with the INDIESCOPE_MODEL environment variable (e.g. "openai/gpt-4o-mini").
MODEL = os.environ.get("INDIESCOPE_MODEL", "anthropic/claude-sonnet-5-5")

# Environment variable that must hold the key, by provider.
API_KEY_VARIABLES = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}

SYSTEM_PROMPT = (
    "You are a consultant who advises the founders of small independent video game studios. "
    "You are given the figures produced by a profitability simulator for Steam. "
    "Write a 4 to 5 sentence piece of advice, in English, clear and direct. "
    "Strict rules: use ONLY the figures provided, do not invent any figure, any game name "
    "or any statistic. End with a sentence that recalls a limitation of the method "
    "(sales are estimated from reviews; neither marketing nor game quality is taken into account)."
)


def result_to_text(result):
    """Turn the dictionary returned by GameConcept.evaluate into text for the AI.

    result: dict returned by evaluate().
    Returns a str of a few lines.
    """
    p25, median, p75 = result["revenue_range"]
    probabilities = result["probabilities"]
    return (
        f"Concept tags: {', '.join(result['tags'])}\n"
        f"Planned price: ${result['price']:.2f}\n"
        f"Studio budget: ${result['budget']:,.0f}\n"
        f"Number of comparable games: {result['n_comparables']}\n"
        f"Net revenue of comparable games (mid scenario): 25th percentile ${p25:,.0f}, "
        f"median ${median:,.0f}, 75th percentile ${p75:,.0f}\n"
        f"Probability of covering the budget: low scenario {probabilities['low']:.0%}, "
        f"mid {probabilities['mid']:.0%}, high {probabilities['high']:.0%}\n"
        f"Verdict: {result['recommendation']}\n"
        f"Recommended price band: {result['recommended_price'] or 'not determined'}\n"
        f"Warning: {result['warning'] or 'none'}"
    )


def api_key_available(model=MODEL):
    """True if the API key of the model's provider is set (environment variable or .env file)."""
    # python-dotenv is optional: without it, only the environment variables are read.
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
    """Ask the AI for written advice on the simulator result.

    result: dict returned by GameConcept.evaluate.
    Returns the advice (str), or a clear message if the AI is not available.
    The app must work without the AI: we return a message instead of crashing.
    """
    if not api_key_available(model):
        return ("ℹ️ The AI explanation is not available: no API key found. "
                "Add ANTHROPIC_API_KEY to a .env file to enable it.")
    try:
        from mirascope import llm
    except ImportError:
        return "ℹ️ The AI explanation needs the mirascope library (pip install mirascope)."

    # Same syntax as the mirascope course: a function decorated with @llm.call
    # that returns the system message and the user message.
    @llm.call(model)
    def advise(results_text: str):
        return [
            llm.messages.system(SYSTEM_PROMPT),
            llm.messages.user(f"Simulator results:\n{results_text}"),
        ]

    try:
        return advise(result_to_text(result)).text()
    except Exception:
        # Network down, key refused, quota exceeded...: warn without crashing.
        return "⚠️ The AI could not answer. The results above are still valid."
