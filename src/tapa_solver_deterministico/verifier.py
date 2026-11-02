from __future__ import annotations

from dataclasses import dataclass

from .model import BLACK, UNKNOWN, WHITE, Board, ORTHOGONAL
from .patterns import compatible_patterns


@dataclass(frozen=True, slots=True)
class RuleViolation:
    """Violação produzida apenas pela aplicação das regras do Tapa."""

    rule: str
    message: str
    cells: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationResult:
    valid: bool
    errors: tuple[str, ...]
    violations: tuple[RuleViolation, ...] = ()
    rules_checked: tuple[str, ...] = ()


def black_cells_connected(board: Board) -> bool:
    black = {index for index, value in enumerate(board.values) if value == BLACK}
    if not black:
        return False
    start = next(iter(black))
    seen = {start}
    stack = [start]
    while stack:
        index = stack.pop()
        row, col = board.puzzle.cell(index)
        for delta_row, delta_col in ORTHOGONAL:
            neighbor = row + delta_row, col + delta_col
            if board.puzzle.in_bounds(*neighbor):
                neighbor_index = board.puzzle.index(*neighbor)
                if neighbor_index in black and neighbor_index not in seen:
                    seen.add(neighbor_index)
                    stack.append(neighbor_index)
    return seen == black


class DeterministicRulesEngine:
    """Validador independente: não busca, não usa heurística e não consulta LLM."""

    RULES = (
        "dimensions",
        "cell_domain",
        "complete_assignment",
        "clue_cells_white",
        "clue_runs",
        "no_black_2x2",
        "black_connectivity",
    )

    def validate(self, board: Board) -> VerificationResult:
        violations: list[RuleViolation] = []
        puzzle = board.puzzle

        if len(board.values) != puzzle.rows * puzzle.cols:
            violation = RuleViolation("dimensions", "dimensão interna do tabuleiro inválida")
            return VerificationResult(False, (violation.message,), (violation,), self.RULES)

        invalid = [
            puzzle.cell(index)
            for index, value in enumerate(board.values)
            if value not in {UNKNOWN, WHITE, BLACK}
        ]
        if invalid:
            violations.append(
                RuleViolation(
                    "cell_domain",
                    "a solução contém valores diferentes de preto, branco ou indefinido",
                    tuple(invalid),
                )
            )

        unknown = [puzzle.cell(index) for index, value in enumerate(board.values) if value == UNKNOWN]
        if unknown:
            violations.append(
                RuleViolation(
                    "complete_assignment",
                    "a solução contém células indefinidas",
                    tuple(unknown),
                )
            )

        for row, col in puzzle.clues:
            if board.get(row, col) != WHITE:
                violations.append(
                    RuleViolation(
                        "clue_cells_white",
                        f"a pista ({row}, {col}) não está branca",
                        ((row, col),),
                    )
                )
            elif not compatible_patterns(board, (row, col)):
                violations.append(
                    RuleViolation(
                        "clue_runs",
                        f"a pista ({row}, {col}) não foi satisfeita",
                        ((row, col),),
                    )
                )

        for row in range(puzzle.rows - 1):
            for col in range(puzzle.cols - 1):
                cells = ((row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1))
                if all(board.get(*cell) == BLACK for cell in cells):
                    violations.append(
                        RuleViolation(
                            "no_black_2x2",
                            f"há um bloco preto 2x2 com canto em ({row}, {col})",
                            cells,
                        )
                    )

        if not black_cells_connected(board):
            violations.append(
                RuleViolation(
                    "black_connectivity",
                    "as células pretas não formam um único componente não vazio",
                )
            )

        return VerificationResult(
            not violations,
            tuple(item.message for item in violations),
            tuple(violations),
            self.RULES,
        )


RULES_ENGINE = DeterministicRulesEngine()


def verify(board: Board) -> VerificationResult:
    """Mantém a API pública e delega ao motor determinístico de regras."""

    return RULES_ENGINE.validate(board)


