from __future__ import annotations

from functools import lru_cache

from .model import BLACK, UNKNOWN, Board, Cell, Puzzle, RING, RunToken


def cyclic_runs(bits: tuple[int, ...]) -> tuple[int, ...]:
    """Retorna os comprimentos dos blocos de 1 em um anel binário."""
    if not any(bits):
        return ()
    if all(bits):
        return (len(bits),)
    zero = bits.index(0)
    runs: list[int] = []
    current = 0
    for step in range(1, len(bits) + 1):
        bit = bits[(zero + step) % len(bits)]
        if bit:
            current += 1
        elif current:
            runs.append(current)
            current = 0
    if current:
        runs.append(current)
    return tuple(runs)


def matches_clue(runs: tuple[int, ...], clue: tuple[RunToken, ...]) -> bool:
    """As pistas de Tapa são um multiconjunto; '?' casa com qualquer bloco positivo."""
    if clue == (0,):
        return not runs
    if len(runs) != len(clue):
        return False
    remaining = list(runs)
    wildcards = 0
    for token in clue:
        if token == "?":
            wildcards += 1
            continue
        try:
            remaining.remove(token)
        except ValueError:
            return False
    return len(remaining) == wildcards


@lru_cache(maxsize=None)
def patterns_for_clue(clue: tuple[RunToken, ...]) -> tuple[tuple[int, ...], ...]:
    patterns: list[tuple[int, ...]] = []
    for mask in range(256):
        bits = tuple((mask >> position) & 1 for position in range(8))
        if matches_clue(cyclic_runs(bits), clue):
            patterns.append(bits)
    return tuple(patterns)


def ring_indices(puzzle: Puzzle, cell: Cell) -> tuple[int | None, ...]:
    row, col = cell
    slots: list[int | None] = []
    for delta_row, delta_col in RING:
        neighbor = row + delta_row, col + delta_col
        slots.append(puzzle.index(*neighbor) if puzzle.in_bounds(*neighbor) else None)
    return tuple(slots)


def compatible_patterns(board: Board, cell: Cell) -> tuple[tuple[int, ...], ...]:
    clue = board.puzzle.clues[cell]
    slots = ring_indices(board.puzzle, cell)
    compatible: list[tuple[int, ...]] = []
    for pattern in patterns_for_clue(clue):
        accepted = True
        for bit, index in zip(pattern, slots, strict=True):
            if index is None:
                accepted = bit != BLACK
            else:
                value = board.values[index]
                accepted = value == UNKNOWN or value == bit
            if not accepted:
                break
        if accepted:
            compatible.append(pattern)
    return tuple(compatible)


