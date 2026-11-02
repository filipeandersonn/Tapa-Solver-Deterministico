from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

UNKNOWN = -1
WHITE = 0
BLACK = 1

RunToken = int | str
Cell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Puzzle:
    rows: int
    cols: int
    clues: dict[Cell, tuple[RunToken, ...]]
    name: str = "sem_nome"

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("rows e cols devem ser positivos")
        normalized: dict[Cell, tuple[RunToken, ...]] = {}
        for (row, col), raw_runs in self.clues.items():
            if not self.in_bounds(row, col):
                raise ValueError(f"pista fora do tabuleiro: ({row}, {col})")
            runs: list[RunToken] = []
            for token in raw_runs:
                if token == "?":
                    runs.append("?")
                elif isinstance(token, int) and not isinstance(token, bool) and 0 <= token <= 8:
                    runs.append(token)
                else:
                    raise ValueError(f"pista inválida em ({row}, {col}): {token!r}")
            if not runs:
                raise ValueError(f"a pista em ({row}, {col}) não pode ser vazia")
            if 0 in runs and runs != [0]:
                raise ValueError(f"a pista zero deve aparecer sozinha em ({row}, {col})")
            normalized[(row, col)] = tuple(runs)
        object.__setattr__(self, "clues", normalized)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def index(self, row: int, col: int) -> int:
        return row * self.cols + col

    def cell(self, index: int) -> Cell:
        return divmod(index, self.cols)

    def cells(self) -> Iterator[Cell]:
        for row in range(self.rows):
            for col in range(self.cols):
                yield row, col


@dataclass(slots=True)
class Board:
    puzzle: Puzzle
    values: list[int]

    @classmethod
    def initial(cls, puzzle: Puzzle) -> "Board":
        values = [UNKNOWN] * (puzzle.rows * puzzle.cols)
        for row, col in puzzle.clues:
            values[puzzle.index(row, col)] = WHITE
        return cls(puzzle, values)

    @classmethod
    def from_rows(cls, puzzle: Puzzle, rows: Iterable[str]) -> "Board":
        materialized = [line.strip() for line in rows if line.strip()]
        if len(materialized) != puzzle.rows:
            raise ValueError(f"esperadas {puzzle.rows} linhas, recebidas {len(materialized)}")
        values: list[int] = []
        symbols = {"#": BLACK, "1": BLACK, ".": WHITE, "0": WHITE, "?": UNKNOWN}
        for row, line in enumerate(materialized):
            if len(line) != puzzle.cols:
                raise ValueError(f"linha {row} deve ter {puzzle.cols} caracteres")
            try:
                values.extend(symbols[char] for char in line)
            except KeyError as exc:
                raise ValueError(f"símbolo inválido na solução: {exc.args[0]!r}") from exc
        return cls(puzzle, values)

    def copy(self) -> "Board":
        return Board(self.puzzle, self.values.copy())

    def get(self, row: int, col: int) -> int:
        return self.values[self.puzzle.index(row, col)]

    def set(self, row: int, col: int, value: int) -> None:
        self.values[self.puzzle.index(row, col)] = value

    def unknown_indices(self) -> list[int]:
        return [index for index, value in enumerate(self.values) if value == UNKNOWN]

    def is_complete(self) -> bool:
        return UNKNOWN not in self.values

    def render(self, show_clues: bool = True) -> str:
        lines: list[str] = []
        for row in range(self.puzzle.rows):
            cells: list[str] = []
            for col in range(self.puzzle.cols):
                if show_clues and (row, col) in self.puzzle.clues:
                    clue = ",".join(map(str, self.puzzle.clues[(row, col)]))
                    cells.append(f"[{clue}]")
                else:
                    cells.append({BLACK: "#", WHITE: ".", UNKNOWN: "?"}[self.get(row, col)])
            lines.append(" ".join(cells) if show_clues else "".join(cells))
        return "\n".join(lines)


ORTHOGONAL = ((-1, 0), (0, 1), (1, 0), (0, -1))
RING = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))


