"""Motor tradicional do quebra-cabeça Tapa."""

from .model import Board, Puzzle
from .propagation import Contradiction, propagate
from .solver import SolveResult, solve
from .verifier import DeterministicRulesEngine, verify

__all__ = ["Board", "Puzzle", "Contradiction", "propagate", "SolveResult", "solve",
           "DeterministicRulesEngine", "verify"]

