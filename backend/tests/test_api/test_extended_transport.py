"""
backend/tests/test_api/test_extended_transport.py
===================================================
Tests cho các bài toán vận tải mở rộng:
  - Max transportation (POST /api/transportation/max)
  - Forbidden cells   (POST /api/transportation/forbidden)
  - Inequality        (POST /api/transportation/inequality)
  - Warehouse         (POST /api/transportation/warehouse)
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# ── Max Transportation ────────────────────────────────────────────────────────

class TestMaxTransportation:
    def _base_request(self):
        return {
            "profitMatrix": [
                [5, 8, 6],
                [3, 7, 4],
                [6, 5, 9],
            ],
            "supply": [30, 40, 30],
            "demand": [25, 35, 40],
        }

    def test_solve_returns_200(self):
        r = client.post("/api/transportation/max", json=self._base_request())
        assert r.status_code == 200

    def test_variant_is_max_profit(self):
        r = client.post("/api/transportation/max", json=self._base_request())
        data = r.json()
        assert data["variant"] == "max_profit"
        assert data["problemType"] == "transportation"

    def test_has_transformation_info(self):
        r = client.post("/api/transportation/max", json=self._base_request())
        data = r.json()
        trans = data["transformations"]
        assert len(trans) >= 1
        assert trans[0]["type"] == "max_to_min"
        assert "pMax" in trans[0]["details"]

    def test_total_profit_is_positive(self):
        r = client.post("/api/transportation/max", json=self._base_request())
        data = r.json()
        assert data["solution"]["totalProfit"] > 0

    def test_allocation_sums_match_supply_demand(self):
        r = client.post("/api/transportation/max", json=self._base_request())
        data = r.json()
        alloc = data["solution"]["allocationMatrix"]
        supply = self._base_request()["supply"]
        demand = self._base_request()["demand"]
        for i, row in enumerate(alloc):
            assert abs(sum(row) - supply[i]) < 1e-6, f"Row {i} sum mismatch"
        for j in range(len(demand)):
            col_sum = sum(alloc[i][j] for i in range(len(alloc)))
            assert abs(col_sum - demand[j]) < 1e-6, f"Col {j} sum mismatch"

    def test_balanced_problem(self):
        """Bài toán đã cân bằng."""
        r = client.post("/api/transportation/max", json={
            "profitMatrix": [[10, 5], [3, 8]],
            "supply": [100, 100],
            "demand": [100, 100],
        })
        assert r.status_code == 200
        assert r.json()["solution"]["totalProfit"] > 0


# ── Forbidden Cells ───────────────────────────────────────────────────────────

class TestForbiddenCells:
    def _base_request(self):
        return {
            "costMatrix": [
                [2, 3, 1],
                [5, 4, 8],
                [5, 6, 8],
            ],
            "supply": [120, 80, 80],
            "demand": [150, 70, 60],
            "forbiddenCells": [{"row": 0, "col": 2}],
        }

    def test_solve_returns_200(self):
        r = client.post("/api/transportation/forbidden", json=self._base_request())
        assert r.status_code == 200

    def test_variant_is_forbidden_cells(self):
        r = client.post("/api/transportation/forbidden", json=self._base_request())
        data = r.json()
        assert data["variant"] == "forbidden_cells"

    def test_has_big_m_transformation(self):
        r = client.post("/api/transportation/forbidden", json=self._base_request())
        data = r.json()
        assert len(data["transformations"]) >= 1
        assert data["transformations"][0]["type"] == "forbidden_cells_big_m"
        assert "bigMValue" in data["transformedProblem"]

    def test_forbidden_cell_not_used(self):
        """Ô cấm (0,2) không được phân bổ."""
        r = client.post("/api/transportation/forbidden", json=self._base_request())
        data = r.json()
        alloc = data["solution"]["allocationMatrix"]
        assert alloc[0][2] < 1e-6, "Ô cấm (0,2) có allocation dương!"

    def test_feasibility_flag_present(self):
        r = client.post("/api/transportation/forbidden", json=self._base_request())
        data = r.json()
        assert "isFeasibleRespectingForbiddenCells" in data["interpretation"]

    def test_empty_forbidden_list(self):
        """Không có ô cấm nào — vẫn giải được bình thường."""
        req = self._base_request()
        req["forbiddenCells"] = []
        r = client.post("/api/transportation/forbidden", json=req)
        assert r.status_code == 200

    def test_out_of_bounds_cell_returns_400(self):
        req = self._base_request()
        req["forbiddenCells"] = [{"row": 10, "col": 0}]
        r = client.post("/api/transportation/forbidden", json=req)
        assert r.status_code in (400, 422, 500)


# ── Inequality Constraints ────────────────────────────────────────────────────

class TestInequalityConstraints:
    def _base_request(self):
        return {
            "costMatrix": [
                [2, 3, 1],
                [5, 4, 8],
                [5, 6, 2],
            ],
            "supply": [50, 60, 50],  # totalSupply = 160 > totalDemand = 120
            "demand": [40, 50, 30],
            "supplyConstraint": "less_or_equal",
            "demandConstraint": "equal",
        }

    def test_solve_returns_200(self):
        r = client.post("/api/transportation/inequality", json=self._base_request())
        assert r.status_code == 200

    def test_variant_is_inequality(self):
        r = client.post("/api/transportation/inequality", json=self._base_request())
        assert r.json()["variant"] == "inequality_constraints"

    def test_dummy_destination_added(self):
        """Vì supply > demand → thêm dummy destination."""
        r = client.post("/api/transportation/inequality", json=self._base_request())
        data = r.json()
        # transformed demand có thêm 1 phần tử
        orig_n = len(self._base_request()["demand"])
        transformed_demand = data["transformedProblem"]["demand"]
        assert len(transformed_demand) == orig_n + 1

    def test_unused_supply_interpretation(self):
        r = client.post("/api/transportation/inequality", json=self._base_request())
        data = r.json()
        assert "unusedSupplyBySource" in data["interpretation"]
        unused = data["interpretation"]["unusedSupplyBySource"]
        assert len(unused) == len(self._base_request()["supply"])
        total_unused = sum(u["unusedAmount"] for u in unused)
        supply_total = sum(self._base_request()["supply"])
        demand_total = sum(self._base_request()["demand"])
        assert abs(total_unused - (supply_total - demand_total)) < 1e-6

    def test_infeasible_supply_less_than_demand(self):
        """supply < demand với constraint less_or_equal → 400."""
        req = self._base_request()
        req["supply"] = [10, 10, 10]  # totalSupply = 30 < totalDemand = 120
        r = client.post("/api/transportation/inequality", json=req)
        assert r.status_code == 400

    def test_unsupported_constraint_returns_422(self):
        req = self._base_request()
        req["demandConstraint"] = "greater_or_equal"
        r = client.post("/api/transportation/inequality", json=req)
        assert r.status_code == 422

    def test_balanced_equal_equal(self):
        """supply = demand, constraint equal/equal → dùng solver thông thường."""
        r = client.post("/api/transportation/inequality", json={
            "costMatrix": [[1, 2], [3, 4]],
            "supply": [50, 50],
            "demand": [50, 50],
            "supplyConstraint": "equal",
            "demandConstraint": "equal",
        })
        assert r.status_code == 200


# ── Warehouse Receiving ───────────────────────────────────────────────────────

class TestWarehouseReceiving:
    def _base_request(self):
        return {
            "baseCostMatrix": [
                [3, 5],
                [4, 2],
                [6, 3],
            ],
            "supply": [50, 60, 40],
            "demand": [40, 60],
            "warehouses": [
                {
                    "name": "Kho A",
                    "demandMode": "fixed",
                    "amount": 50,
                    "costsFromSources": [2, 3, 4],
                    "storageCostPerUnit": 1,
                }
            ],
        }

    def test_solve_returns_200(self):
        r = client.post("/api/transportation/warehouse", json=self._base_request())
        assert r.status_code == 200

    def test_variant_is_warehouse(self):
        r = client.post("/api/transportation/warehouse", json=self._base_request())
        assert r.json()["variant"] == "warehouse_receiving"

    def test_warehouse_added_as_destination(self):
        r = client.post("/api/transportation/warehouse", json=self._base_request())
        data = r.json()
        orig_n = len(self._base_request()["demand"])
        n_warehouses = len(self._base_request()["warehouses"])
        assert len(data["transformedProblem"]["demand"]) == orig_n + n_warehouses

    def test_warehouse_usage_interpretation(self):
        r = client.post("/api/transportation/warehouse", json=self._base_request())
        data = r.json()
        assert "warehouseUsage" in data["interpretation"]
        usage = data["interpretation"]["warehouseUsage"]
        assert len(usage) == 1
        assert usage[0]["name"] == "Kho A"
        assert usage[0]["receivedAmount"] >= 0

    def test_max_capacity_mode_returns_422(self):
        req = self._base_request()
        req["warehouses"][0]["demandMode"] = "max_capacity"
        r = client.post("/api/transportation/warehouse", json=req)
        assert r.status_code == 422

    def test_wrong_costs_from_sources_length_returns_error(self):
        """costsFromSources phải có đúng len(supply) phần tử."""
        req = self._base_request()
        req["warehouses"][0]["costsFromSources"] = [2, 3]  # cần 3 nhưng truyền 2
        r = client.post("/api/transportation/warehouse", json=req)
        assert r.status_code in (400, 422, 500)
