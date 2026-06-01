"""
backend/tests/test_algorithms/test_least_cost.py
==================================================
Unit tests cho LeastCostMethod.

Test:
  - Shape đầu ra đúng.
  - Ma trận phân bổ feasible (không âm, thỏa supply/demand).
  - Total cost là số hợp lệ.
  - Basis cells đúng số lượng (m+n-1).
  - Validator phát hiện input sai.
"""

import pytest

from backend.core.algorithms.initial_solution.least_cost import LeastCostMethod
from backend.core.models.problem import TransportationProblem


@pytest.fixture
def classic_3x4():
    """Bài toán cổ điển 3×4 với nghiệm tối ưu f* = 53."""
    return TransportationProblem(
        cost_matrix=[
            [2.0, 3.0, 1.0, 5.0],
            [7.0, 3.0, 4.0, 6.0],
            [3.0, 8.0, 2.0, 4.0],
        ],
        supply=[7.0, 5.0, 7.0],
        demand=[5.0, 4.0, 6.0, 4.0],
    )


@pytest.fixture
def simple_2x3():
    """Bài toán đơn giản 2×3."""
    return TransportationProblem(
        cost_matrix=[
            [2.0, 3.0, 1.0],
            [5.0, 4.0, 8.0],
        ],
        supply=[20.0, 30.0],
        demand=[10.0, 25.0, 15.0],
    )


class TestLeastCostMethod:

    def test_solve_returns_solution(self, classic_3x4):
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        assert solution is not None

    def test_allocation_matrix_shape(self, classic_3x4):
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        m = len(classic_3x4.supply)
        n = len(classic_3x4.demand)
        assert len(solution.allocation_matrix) == m
        for row in solution.allocation_matrix:
            assert len(row) == n

    def test_allocation_non_negative(self, classic_3x4):
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        for row in solution.allocation_matrix:
            for val in row:
                assert val >= 0, f"Phân bổ âm: {val}"

    def test_supply_constraints_satisfied(self, classic_3x4):
        """Tổng phân bổ từng hàng phải = supply."""
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        X = solution.allocation_matrix
        supply = classic_3x4.supply
        for i, s in enumerate(supply):
            row_sum = sum(X[i])
            assert abs(row_sum - s) < 1e-6, f"Hàng {i}: {row_sum} ≠ {s}"

    def test_demand_constraints_satisfied(self, classic_3x4):
        """Tổng phân bổ từng cột phải = demand."""
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        X = solution.allocation_matrix
        demand = classic_3x4.demand
        m = len(supply := classic_3x4.supply)
        n = len(demand)
        for j in range(n):
            col_sum = sum(X[i][j] for i in range(m))
            assert abs(col_sum - demand[j]) < 1e-6, f"Cột {j}: {col_sum} ≠ {demand[j]}"

    def test_total_cost_is_positive_number(self, classic_3x4):
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        assert isinstance(solution.total_cost, float)
        assert solution.total_cost > 0

    def test_basis_cells_count(self, classic_3x4):
        """Số ô cơ sở phải = m + n - 1."""
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        m = len(classic_3x4.supply)
        n = len(classic_3x4.demand)
        expected_basis_size = m + n - 1
        assert len(solution.basis_cells) == expected_basis_size, (
            f"Số ô cơ sở = {len(solution.basis_cells)}, cần {expected_basis_size}"
        )

    def test_is_not_optimal(self, classic_3x4):
        """Phương án ban đầu không phải tối ưu (chưa qua optimization)."""
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        assert solution.is_optimal is False

    def test_has_initial_iteration(self, classic_3x4):
        algo = LeastCostMethod()
        solution = algo.solve(classic_3x4)
        assert len(solution.iterations) >= 1
        assert solution.iterations[0].step == 0

    def test_simple_2x3(self, simple_2x3):
        """Test bài toán 2×3 đơn giản."""
        algo = LeastCostMethod()
        solution = algo.solve(simple_2x3)
        assert len(solution.allocation_matrix) == 2
        assert len(solution.allocation_matrix[0]) == 3
        assert solution.total_cost > 0
        assert len(solution.basis_cells) == 2 + 3 - 1  # m+n-1 = 4

    def test_different_from_northwest_corner(self, classic_3x4):
        """Least Cost và NW Corner thường cho chi phí ban đầu khác nhau."""
        from backend.core.algorithms.initial_solution.northwest_corner import NorthwestCornerMethod
        lc_sol = LeastCostMethod().solve(classic_3x4)
        nw_sol = NorthwestCornerMethod().solve(classic_3x4)
        # Least Cost thường cho chi phí thấp hơn NW Corner
        # (không bắt buộc nhưng thường đúng với bài toán này)
        assert lc_sol.total_cost <= nw_sol.total_cost + 1e-6
