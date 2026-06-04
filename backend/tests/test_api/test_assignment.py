"""
backend/tests/test_api/test_assignment.py
==========================================
Tests cho bài toán phân việc (Hungarian Algorithm).
POST /api/assignment/solve
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

URL = "/api/assignment/solve"


class TestAssignmentSolve:
    def _square_min(self):
        return {
            "matrix": [
                [9, 2, 7, 8],
                [6, 4, 3, 7],
                [5, 8, 1, 8],
                [7, 6, 9, 4],
            ],
            "objective": "minimize",
        }

    def test_solve_returns_200(self):
        r = client.post(URL, json=self._square_min())
        assert r.status_code == 200

    def test_variant_is_assignment(self):
        r = client.post(URL, json=self._square_min())
        assert r.json()["variant"] == "assignment"
        assert r.json()["problemType"] == "assignment"

    def test_exactly_n_assignments(self):
        r = client.post(URL, json=self._square_min())
        data = r.json()
        assignments = [a for a in data["solution"]["assignments"] if not a.get("isDummy")]
        n = len(self._square_min()["matrix"])
        # Số phân công thật = n (mỗi người đúng 1 việc)
        assert len(assignments) == n

    def test_total_cost_is_known_optimal(self):
        """Ma trận kinh điển, nghiệm tối ưu là 13."""
        r = client.post(URL, json={
            "matrix": [
                [9, 2, 7, 8],
                [6, 4, 3, 7],
                [5, 8, 1, 8],
                [7, 6, 9, 4],
            ],
            "objective": "minimize",
        })
        data = r.json()
        # Optimal cost = 2 + 3 + 1 + 4 = 10
        assert abs(data["solution"]["totalCost"] - 10) < 1e-6

    def test_maximize_returns_different_cost(self):
        r_min = client.post(URL, json={**self._square_min(), "objective": "minimize"})
        r_max = client.post(URL, json={**self._square_min(), "objective": "maximize"})
        assert r_min.status_code == 200
        assert r_max.status_code == 200
        cost_min = r_min.json()["solution"]["totalCost"]
        profit_max = r_max.json()["solution"]["totalProfit"]
        # Không thể bằng nhau
        assert abs(cost_min - profit_max) > 0.1

    def test_steps_include_reduction(self):
        r = client.post(URL, json=self._square_min())
        data = r.json()
        step_types = {s["type"] for s in data["steps"]}
        assert "row_reduction" in step_types
        assert "column_reduction" in step_types

    def test_non_square_matrix_auto_padded(self):
        """Ma trận 3×4 không vuông — pad thành 4×4."""
        r = client.post(URL, json={
            "matrix": [
                [3, 5, 7, 2],
                [8, 1, 4, 6],
                [2, 9, 3, 7],
            ],
            "objective": "minimize",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["transformedProblem"] is not None
        # addedDummyWorkers = 1
        pad_trans = next((t for t in data["transformations"] if t["type"] == "rectangular_to_square"), None)
        assert pad_trans is not None
        assert pad_trans["details"]["addedDummyWorkers"] == 1

    def test_custom_names_in_response(self):
        r = client.post(URL, json={
            "matrix": [[1, 2], [3, 4]],
            "objective": "minimize",
            "workerNames": ["Alice", "Bob"],
            "jobNames": ["Lập trình", "Thiết kế"],
        })
        assert r.status_code == 200
        data = r.json()
        assignments = data["solution"]["assignments"]
        names_in = {a["workerName"] for a in assignments} | {a["jobName"] for a in assignments}
        assert "Alice" in names_in or "Bob" in names_in

    def test_2x2_optimal(self):
        """2×2: min([[10,5],[8,12]]) = 5+8=13."""
        r = client.post(URL, json={
            "matrix": [[10, 5], [8, 12]],
            "objective": "minimize",
        })
        assert r.status_code == 200
        data = r.json()
        assert abs(data["solution"]["totalCost"] - 13) < 1e-6
