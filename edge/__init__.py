"""Edge: an odds-comparison and value-betting engine.

De-vig bookmaker odds, estimate fair probabilities from the market, and surface
+EV bets across sportsbooks. Inspired by the EdgeTerminal-style "intelligence
layer" for bettors.
"""

from .engine import ValueBet, find_model_value_bets, find_value_bets
from .model import EloModel, TeamModel, results_from_scores
from .models import Event, Outcome
from .providers import MockProvider, OddsProvider, TheOddsApiProvider

__version__ = "0.1.0"

__all__ = [
    "find_value_bets",
    "find_model_value_bets",
    "ValueBet",
    "EloModel",
    "TeamModel",
    "results_from_scores",
    "Event",
    "Outcome",
    "OddsProvider",
    "MockProvider",
    "TheOddsApiProvider",
]
