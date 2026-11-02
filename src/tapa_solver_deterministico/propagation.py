from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .model import BLACK, UNKNOWN, WHITE, Board, ORTHOGONAL
from .patterns import compatible_patterns, ring_indices


class Contradiction(RuntimeError):
    pass


@dataclass(slots=True)
class PropagationReport:
    assignments: int = 0
    iterations: int = 0
    by_rule: Counter[str] = field(default_factory=Counter)


def _assign(board: Board, index: int, value: int, rule: str, report: PropagationReport) -> bool:
    current = board.values[index]
    if current == value:
        return False
    if current != UNKNOWN:
        raise Contradiction(f"atribuições incompatíveis na célula {board.puzzle.cell(index)}")
    board.values[index] = value
    report.assignments += 1
    report.by_rule[rule] += 1
    return True


def _potentially_connected(board: Board, blocked: int | None = None) -> bool:
    black = [index for index, value in enumerate(board.values) if value == BLACK and index != blocked]
    if len(black) <= 1:
        return True
    start = black[0]
    seen = {start}
    stack = [start]
    while stack:
        index = stack.pop()
        row, col = board.puzzle.cell(index)
        for delta_row, delta_col in ORTHOGONAL:
            neighbor = row + delta_row, col + delta_col
            if not board.puzzle.in_bounds(*neighbor):
                continue
            neighbor_index = board.puzzle.index(*neighbor)
            if neighbor_index == blocked or board.values[neighbor_index] == WHITE:
                continue
            if neighbor_index not in seen:
                seen.add(neighbor_index)
                stack.append(neighbor_index)
    return all(index in seen for index in black)


def propagate(board: Board) -> PropagationReport:
    """Aplica regras lógicas até ponto fixo ou levanta Contradiction."""
    report = PropagationReport()
    changed = True
    while changed:
        report.iterations += 1
        changed = False

        for cell in board.puzzle.clues:
            patterns = compatible_patterns(board, cell)
            if not patterns:
                raise Contradiction(f"nenhum padrão satisfaz a pista {cell}")
            slots = ring_indices(board.puzzle, cell)
            for position, index in enumerate(slots):
                if index is None or board.values[index] != UNKNOWN:
                    continue
                possible = {pattern[position] for pattern in patterns}
                if len(possible) == 1:
                    changed |= _assign(board, index, possible.pop(), "pista", report)

        for row in range(board.puzzle.rows - 1):
            for col in range(board.puzzle.cols - 1):
                indices = (
                    board.puzzle.index(row, col),
                    board.puzzle.index(row + 1, col),
                    board.puzzle.index(row, col + 1),
                    board.puzzle.index(row + 1, col + 1),
                )
                black_count = sum(board.values[index] == BLACK for index in indices)
                unknown = [index for index in indices if board.values[index] == UNKNOWN]
                if black_count == 4:
                    raise Contradiction(f"bloco preto 2x2 em ({row}, {col})")
                if black_count == 3 and len(unknown) == 1:
                    changed |= _assign(board, unknown[0], WHITE, "sem_2x2", report)

        if not _potentially_connected(board):
            raise Contradiction("componentes pretos não podem mais ser conectados")
        if sum(value == BLACK for value in board.values) >= 2:
            for index, value in enumerate(board.values):
                if value == UNKNOWN and not _potentially_connected(board, blocked=index):
                    changed |= _assign(board, index, BLACK, "conectividade", report)
    return report


def potential_connectivity(board: Board) -> bool:
    return _potentially_connected(board)


