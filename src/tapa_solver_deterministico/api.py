"""API compatível com a chamada de resolução do frontend integrado."""

from __future__ import annotations

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .model import BLACK, Puzzle
from .solver import solve

MAX_BOARD_AREA = 300
DEFAULT_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://filipeandersonn.github.io",
)


class CellInput(BaseModel):
    type: Literal["clue", "unknown"]
    label: str = Field(default="", max_length=64)


class SolveRequest(BaseModel):
    id: str = Field(default="frontend", min_length=1, max_length=200)
    width: int = Field(ge=1, le=200)
    height: int = Field(ge=1, le=200)
    cells: list[CellInput] = Field(max_length=MAX_BOARD_AREA)
    heuristic: str = "first"
    expression: str | None = None
    timeout_seconds: float = Field(default=120.0, gt=0, le=120.0)
    node_limit: int = Field(default=1_000_000, gt=0, le=5_000_000)


def request_to_puzzle(request: SolveRequest) -> Puzzle:
    if request.width * request.height > MAX_BOARD_AREA:
        raise ValueError(f"o tabuleiro excede o limite de {MAX_BOARD_AREA} células")
    if len(request.cells) != request.width * request.height:
        raise ValueError("a quantidade de células não corresponde às dimensões")
    clues: dict[tuple[int, int], tuple[int | str, ...]] = {}
    for index, cell in enumerate(request.cells):
        if cell.type != "clue":
            continue
        tokens = cell.label.split()
        if not tokens:
            raise ValueError(f"pista vazia na célula {divmod(index, request.width)}")
        try:
            clues[divmod(index, request.width)] = tuple(
                "?" if token in {"-", "?"} else int(token) for token in tokens
            )
        except ValueError as exc:
            raise ValueError(f"pista inválida na célula {divmod(index, request.width)}") from exc
    return Puzzle(request.height, request.width, clues, request.id)


def allowed_origins() -> list[str]:
    configured = os.getenv("TAPA_ALLOWED_ORIGINS", "")
    if not configured.strip():
        return list(DEFAULT_ORIGINS)
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


app = FastAPI(title="Tapa Solver Determinístico", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/solve")
def solve_endpoint(request: SolveRequest) -> dict[str, object]:
    if request.heuristic != "first" or request.expression is not None:
        raise HTTPException(
            status_code=400,
            detail="Este serviço aceita apenas heuristic='first', sem expression.",
        )
    try:
        result = solve(
            request_to_puzzle(request),
            timeout_seconds=request.timeout_seconds,
            node_limit=request.node_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stats = result.stats
    return {
        "boardId": request.id,
        "solved": result.solved,
        "message": result.message,
        "solution": (
            [1 if value == BLACK else 0 for value in result.board.values]
            if result.board is not None else None
        ),
        "stats": {
            "nodes": stats.nodes,
            "decisions": stats.decisions,
            "backtracks": stats.backtracks,
            "contradictions": stats.contradictions,
            "propagatedAssignments": stats.propagated_assignments,
            "propagationRounds": stats.propagation_rounds,
            "maxDepth": stats.max_depth,
            "elapsedSeconds": stats.elapsed_seconds,
            "timedOut": stats.timed_out,
            "nodeLimitReached": stats.node_limit_reached,
            "cancelled": False,
            "byRule": dict(stats.by_rule),
        },
    }


def run() -> None:
    import uvicorn

    uvicorn.run("tapa_solver_deterministico.api:app", host="127.0.0.1", port=8002)

