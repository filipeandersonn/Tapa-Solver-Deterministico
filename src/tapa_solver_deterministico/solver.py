"""Resolvedor exato com escolha fixa da primeira casa desconhecida."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field

from .model import BLACK, WHITE, Board, Puzzle
from .propagation import Contradiction, propagate
from .verifier import verify


@dataclass(slots=True)
class SearchStats:
    nodes: int = 0
    decisions: int = 0
    backtracks: int = 0
    contradictions: int = 0
    propagated_assignments: int = 0
    propagation_rounds: int = 0
    max_depth: int = 0
    elapsed_seconds: float = 0.0
    timed_out: bool = False
    node_limit_reached: bool = False
    by_rule: Counter[str] = field(default_factory=Counter)


@dataclass(slots=True)
class SolveResult:
    solved: bool
    board: Board | None
    stats: SearchStats
    message: str


class _StopSearch(Exception):
    pass


def solve(
    puzzle: Puzzle,
    timeout_seconds: float | None = 120.0,
    node_limit: int | None = 1_000_000,
) -> SolveResult:
    """Propaga regras e, quando necessário, tenta a primeira casa em ordem linear."""
    stats = SearchStats()
    started = time.monotonic()

    def check_limits() -> None:
        if timeout_seconds is not None and time.monotonic() - started >= timeout_seconds:
            stats.timed_out = True
            raise _StopSearch
        if node_limit is not None and stats.nodes >= node_limit:
            stats.node_limit_reached = True
            raise _StopSearch

    def search(board: Board, depth: int) -> Board | None:
        check_limits()
        stats.nodes += 1
        stats.max_depth = max(stats.max_depth, depth)
        try:
            report = propagate(board)
        except Contradiction:
            stats.contradictions += 1
            return None
        stats.propagated_assignments += report.assignments
        stats.propagation_rounds += report.iterations
        stats.by_rule.update(report.by_rule)

        if board.is_complete():
            return board if verify(board).valid else None

        index = board.unknown_indices()[0]
        stats.decisions += 1
        for color in (BLACK, WHITE):
            child = board.copy()
            child.values[index] = color
            answer = search(child, depth + 1)
            if answer is not None:
                return answer
            stats.backtracks += 1
        return None

    try:
        board = search(Board.initial(puzzle), 0)
    except _StopSearch:
        board = None
    stats.elapsed_seconds = time.monotonic() - started
    if board is not None:
        return SolveResult(True, board, stats, "solução encontrada e verificada")
    if stats.timed_out:
        return SolveResult(False, None, stats, "tempo limite atingido")
    if stats.node_limit_reached:
        return SolveResult(False, None, stats, "limite de nós atingido")
    return SolveResult(False, None, stats, "a instância não possui solução")

