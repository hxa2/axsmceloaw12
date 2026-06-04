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


class TestUnbalancedProblems:
    """
    Tests cho bài toán vận tải không cân bằng.
    Kiểm tra dummy row/col được thêm đúng và response nhất quán.
    """

    def test_supply_exceeds_demand_adds_dummy_destination(self, client):
        """supply > demand → backend thêm dummy destination (cột)."""
        payload = {
            "costMatrix": [[2.0, 3.0], [5.0, 4.0]],
            "supply": [100.0, 50.0],   # tổng = 150
            "demand": [60.0, 40.0],    # tổng = 100, thiếu 50
            "initialMethod": "least_cost",
            "optimizationMethod": "potential",
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Kiểm tra metadata cân bằng
        assert data["isBalancedOriginal"] is False
        assert data["balanceType"] == "dummy_destination"
        assert data["dummyDestinationIndex"] is not None
        assert data["dummySourceIndex"] is None
        assert data["originalSupplyTotal"] == 150.0
        assert data["originalDemandTotal"] == 100.0

        # Sau cân bằng: demand phải có 3 phần tử (2 gốc + 1 dummy)
        assert len(data["demand"]) == 3
        assert data["demand"][-1] == 50.0  # dummy demand = diff

        # costMatrix phải có 3 cột
        assert all(len(row) == 3 for row in data["costMatrix"])
        # costMatrix dummy col phải là 0
        assert all(row[-1] == 0.0 for row in data["costMatrix"])

        # allocationMatrix phải có 3 cột
        assert all(len(row) == 3 for row in data["allocationMatrix"])

        # destinationNames phải có 3 phần tử, cuối là "Dummy"
        assert data["destinationNames"] is not None
        assert len(data["destinationNames"]) == 3
        assert data["destinationNames"][-1] == "Dummy"

        # supply không đổi (2 phần tử)
        assert len(data["supply"]) == 2

        # Tổng cung = tổng cầu sau cân bằng
        assert abs(sum(data["supply"]) - sum(data["demand"])) < 1e-6

    def test_demand_exceeds_supply_adds_dummy_source(self, client):
        """demand > supply → backend thêm dummy source (hàng)."""
        payload = {
            "costMatrix": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            "supply": [30.0, 20.0],    # tổng = 50
            "demand": [25.0, 25.0, 20.0],  # tổng = 70, thừa 20
            "initialMethod": "least_cost",
            "optimizationMethod": "potential",
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Kiểm tra metadata cân bằng
        assert data["isBalancedOriginal"] is False
        assert data["balanceType"] == "dummy_source"
        assert data["dummySourceIndex"] is not None
        assert data["dummyDestinationIndex"] is None
        assert data["originalSupplyTotal"] == 50.0
        assert data["originalDemandTotal"] == 70.0

        # Sau cân bằng: supply phải có 3 phần tử (2 gốc + 1 dummy)
        assert len(data["supply"]) == 3
        assert data["supply"][-1] == 20.0  # dummy supply = diff

        # costMatrix phải có 3 hàng
        assert len(data["costMatrix"]) == 3
        # costMatrix dummy row phải là 0
        assert all(v == 0.0 for v in data["costMatrix"][-1])

        # allocationMatrix phải có 3 hàng
        assert len(data["allocationMatrix"]) == 3

        # sourceNames phải có 3 phần tử, cuối là "Dummy"
        assert data["sourceNames"] is not None
        assert len(data["sourceNames"]) == 3
        assert data["sourceNames"][-1] == "Dummy"

        # demand không đổi (3 phần tử)
        assert len(data["demand"]) == 3

        # Tổng cung = tổng cầu sau cân bằng
        assert abs(sum(data["supply"]) - sum(data["demand"])) < 1e-6

    def test_unbalanced_matrix_sizes_are_consistent(self, client):
        """Kích thước costMatrix, allocationMatrix, sourceNames, destinationNames luôn khớp."""
        # Test với supply > demand
        payload_sd = {
            "costMatrix": [[3.0, 1.0, 2.0], [5.0, 8.0, 4.0], [2.0, 6.0, 3.0]],
            "supply": [120.0, 80.0, 60.0],  # tổng = 260
            "demand": [70.0, 90.0, 50.0],   # tổng = 210, diff = 50
            "destinationNames": ["D-Hanoi", "D-HCM", "D-Danang"],
            "sourceNames": ["S-Bac", "S-Trung", "S-Nam"],
        }
        r1 = client.post("/api/transportation/solve", json=payload_sd)
        assert r1.status_code == 200
        d1 = r1.json()

        m1 = len(d1["supply"])
        n1 = len(d1["demand"])

        assert len(d1["costMatrix"]) == m1
        assert all(len(row) == n1 for row in d1["costMatrix"])
        assert len(d1["allocationMatrix"]) == m1
        assert all(len(row) == n1 for row in d1["allocationMatrix"])
        assert len(d1["sourceNames"]) == m1
        assert len(d1["destinationNames"]) == n1

        # Test với demand > supply
        payload_ds = {
            "costMatrix": [[2.0, 4.0], [3.0, 5.0]],
            "supply": [40.0, 30.0],    # tổng = 70
            "demand": [50.0, 60.0],    # tổng = 110, diff = 40
        }
        r2 = client.post("/api/transportation/solve", json=payload_ds)
        assert r2.status_code == 200
        d2 = r2.json()

        m2 = len(d2["supply"])
        n2 = len(d2["demand"])

        assert len(d2["costMatrix"]) == m2
        assert all(len(row) == n2 for row in d2["costMatrix"])
        assert len(d2["allocationMatrix"]) == m2
        assert all(len(row) == n2 for row in d2["allocationMatrix"])
        assert len(d2["sourceNames"]) == m2
        assert len(d2["destinationNames"]) == n2

    def test_balanced_problem_has_correct_metadata(self, client):
        """Bài toán cân bằng sẵn phải có isBalancedOriginal=True và balanceType='none'."""
        payload = {
            "costMatrix": [[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
            "supply": [20.0, 30.0],
            "demand": [10.0, 25.0, 15.0],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["isBalancedOriginal"] is True
        assert data["balanceType"] == "none"
        assert data["dummySourceIndex"] is None
        assert data["dummyDestinationIndex"] is None
        # Kích thước không thay đổi
        assert len(data["supply"]) == 2
        assert len(data["demand"]) == 3

    def test_unbalanced_with_user_provided_names(self, client):
        """Khi user cung cấp sourceNames/destinationNames, dummy name phải được append đúng."""
        payload = {
            "costMatrix": [[1.0, 2.0], [3.0, 4.0]],
            "supply": [80.0, 60.0],   # tổng = 140
            "demand": [50.0, 50.0],   # tổng = 100, diff = 40
            "sourceNames": ["Nhà máy A", "Nhà máy B"],
            "destinationNames": ["Kho X", "Kho Y"],
        }
        response = client.post("/api/transportation/solve", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["balanceType"] == "dummy_destination"
        assert data["destinationNames"] == ["Kho X", "Kho Y", "Dummy"]
        assert data["sourceNames"] == ["Nhà máy A", "Nhà máy B"]
