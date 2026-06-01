"""
backend/tests/test_api/test_transportation_api.py
===================================================
Integration tests cho FastAPI endpoints.
Dùng httpx.AsyncClient để test API.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_ok(self, client):
        response = client.get("/api/transportation/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestMethodsEndpoint:

    def test_methods_returns_lists(self, client):
        response = client.get("/api/transportation/methods")
        assert response.status_code == 200
        data = response.json()
        assert "initialMethods" in data
        assert "optimizationMethods" in data

    def test_initial_methods_have_required_fields(self, client):
        response = client.get("/api/transportation/methods")
        data = response.json()
        for method in data["initialMethods"]:
            assert "id" in method
            assert "name" in method
            assert "description" in method
            assert "isAvailable" in method

    def test_least_cost_is_available(self, client):
        response = client.get("/api/transportation/methods")
        data = response.json()
        ids = {m["id"] for m in data["initialMethods"]}
        assert "least_cost" in ids
        lc = next(m for m in data["initialMethods"] if m["id"] == "least_cost")
        assert lc["isAvailable"] is True

    def test_vogel_is_not_available(self, client):
        response = client.get("/api/transportation/methods")
        data = response.json()
        vogel = next((m for m in data["initialMethods"] if m["id"] == "vogel"), None)
        if vogel:
            assert vogel["isAvailable"] is False


class TestSampleEndpoint:

    def test_sample_returns_problem(self, client):
        response = client.get("/api/transportation/sample")
        assert response.status_code == 200
        data = response.json()
        assert "costMatrix" in data
        assert "supply" in data
        assert "demand" in data

    def test_classic_3x4_sample(self, client):
        response = client.get("/api/transportation/sample?id=classic_3x4")
        assert response.status_code == 200
        data = response.json()
        assert len(data["supply"]) == 3
        assert len(data["demand"]) == 4

    def test_samples_list(self, client):
        response = client.get("/api/transportation/samples")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestSolveEndpoint:

    def test_solve_simple_2x3(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
            "initialMethod": "least_cost",
            "optimizationMethod": "potential",
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "allocationMatrix" in data
        assert "totalCost" in data
        assert "isOptimal" in data

    def test_solve_returns_optimal(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
        }
        response = client.post("/api/transportation/solve", json=payload)
        data = response.json()
        assert data["isOptimal"] is True

    def test_solve_classic_3x4_optimal_cost(self, client):
        """Chi phí tối ưu bài toán cổ điển 3×4 phải ≈ 50."""
        payload = {
            "costMatrix": [
                [2.0, 3.0, 1.0, 5.0],
                [7.0, 3.0, 4.0, 6.0],
                [3.0, 8.0, 2.0, 4.0],
            ],
            "supply": [7.0, 5.0, 7.0],
            "demand": [5.0, 4.0, 6.0, 4.0],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert abs(data["totalCost"] - 50.0) < 1e-3

    def test_solve_allocation_shape(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
        }
        response = client.post("/api/transportation/solve", json=payload)
        data = response.json()
        X = data["allocationMatrix"]
        assert len(X) == 2
        for row in X:
            assert len(row) == 3

    def test_solve_with_northwest_corner(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
            "initialMethod": "northwest_corner",
            "optimizationMethod": "potential",
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["isOptimal"] is True

    def test_solve_invalid_negative_cost(self, client):
        payload = {
            "costMatrix": [[-1.0, 2.0], [3.0, 4.0]],
            "supply": [5.0, 5.0],
            "demand": [5.0, 5.0],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_solve_shape_mismatch(self, client):
        payload = {
            "costMatrix": [[1.0, 2.0], [3.0, 4.0]],
            "supply": [5.0, 5.0, 5.0],  # 3 rows, matrix has 2
            "demand": [7.5, 7.5],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 400

    def test_solve_empty_matrix_rejected(self, client):
        payload = {
            "costMatrix": [],
            "supply": [],
            "demand": [],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code in (400, 422)

    def test_solve_no_optimization(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
            "optimizationMethod": "none",
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "totalCost" in data

    def test_solve_includes_iterations(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
            "includeIterations": True,
        }
        response = client.post("/api/transportation/solve", json=payload)
        data = response.json()
        assert len(data["iterations"]) > 0

    def test_solve_excludes_iterations_when_requested(self, client):
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
            "includeIterations": False,
        }
        response = client.post("/api/transportation/solve", json=payload)
        data = response.json()
        assert len(data["iterations"]) == 0


class TestRootEndpoint:

    def test_root_returns_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "docs" in data
