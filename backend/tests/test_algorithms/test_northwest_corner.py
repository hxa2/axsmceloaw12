"""
backend/tests/test_algorithms/test_northwest_corner.py
=========================================================
Unit tests cho NorthwestCornerMethod.
"""

import pytest

from backend.core.algorithms.initial_solution.northwest_corner import NorthwestCornerMethod
from backend.core.models.problem import TransportationProblem


@pytest.fixture
def classic_3x4():
    return TransportationProblem(
        cost_matrix=[
            [2.0, 3.0, 1.0, 5.0],
            [7.0, 3.0, 4.0, 6.0],
            [3.0, 8.0, 2.0, 4.0],
        ],
        supply=[7.0, 5.0, 7.0],
        demand=[5.0, 4.0, 6.0, 4.0],
    )


class TestNorthwestCornerMethod:

    def test_solve_returns_solution(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        assert solution is not None

    def test_allocation_shape(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        assert len(solution.allocation_matrix) == 3
        for row in solution.allocation_matrix:
            assert len(row) == 4

    def test_supply_satisfied(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        X = solution.allocation_matrix
        for i, s in enumerate(classic_3x4.supply):
            assert abs(sum(X[i]) - s) < 1e-6

    def test_demand_satisfied(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        X = solution.allocation_matrix
        n = len(classic_3x4.demand)
        m = len(classic_3x4.supply)
        for j in range(n):
            assert abs(sum(X[i][j] for i in range(m)) - classic_3x4.demand[j]) < 1e-6

    def test_basis_size(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        m, n = len(classic_3x4.supply), len(classic_3x4.demand)
        assert len(solution.basis_cells) == m + n - 1

    def test_total_cost_positive(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        assert solution.total_cost > 0

    def test_first_allocation_is_northwest_cell(self, classic_3x4):
        """Ô đầu tiên được phân bổ phải là (0, 0) – góc Tây Bắc."""
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        X = solution.allocation_matrix
        assert X[0][0] > 0, "Ô (0,0) phải có phân bổ > 0 trong Northwest Corner"

    def test_non_negative_allocation(self, classic_3x4):
        algo = NorthwestCornerMethod()
        solution = algo.solve(classic_3x4)
        for row in solution.allocation_matrix:
            for val in row:
                assert val >= 0
