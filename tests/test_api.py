from fastapi.testclient import TestClient

from tapa_solver_deterministico.api import app
from tapa_solver_deterministico.model import Board
from tapa_solver_deterministico.verifier import DeterministicRulesEngine
from tapa_solver_deterministico.api import request_to_puzzle, SolveRequest


def _fixture() -> dict:
    clues = {
        (0, 2): "1 2", (0, 3): "2", (1, 1): "7",
        (2, 3): "5", (3, 0): "2", (3, 1): "4",
    }
    return {
        "id": "fixture",
        "width": 4,
        "height": 4,
        "cells": [
            {"type": "clue", "label": clues[(row, col)]}
            if (row, col) in clues else {"type": "unknown", "label": ""}
            for row in range(4) for col in range(4)
        ],
        "heuristic": "first",
        "timeout_seconds": 5,
        "node_limit": 10000,
    }


def test_frontend_contract_and_valid_solution() -> None:
    body = _fixture()
    response = TestClient(app).post("/api/solve", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["boardId"] == body["id"]
    assert data["solved"] is True
    assert len(data["solution"]) == 16
    assert set(data["solution"]) <= {0, 1}
    puzzle = request_to_puzzle(SolveRequest.model_validate(body))
    assert DeterministicRulesEngine().validate(Board(puzzle, data["solution"])).valid
    assert "nodes" in data["stats"] and "backtracks" in data["stats"]


def test_llm_expression_is_rejected() -> None:
    body = _fixture()
    body["heuristic"] = "expression"
    body["expression"] = "impact_black"
    response = TestClient(app).post("/api/solve", json=body)
    assert response.status_code == 400

