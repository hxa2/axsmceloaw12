"""
backend/tests/test_services/test_solver_service.py
=====================================================
Unit tests cho SolverService.
"""

import pytest

from backend.app.schemas.request import SolveRequest
from backend.app.services.solver_service import SolverService


@pytest.fixture
def service():
    return SolverService()


@pytest.fixture
def simple_request():
    return SolveRequest(
        costMatrix=[[2.0, 3.0, 1.0], [5.0, 4.0, 8.0]],
        supply=[20.0, 30.0],
        demand=[10.0, 25.0, 15.0],
        initialMethod="least_cost",
        optimizationMethod="potential",
    )


@pytest.fixture
def classic_request():
    return SolveRequest(
        costMatrix=[
            [2.0, 3.0, 1.0, 5.0],
            [7.0, 3.0, 4.0, 6.0],
            [3.0, 8.0, 2.0, 4.0],
        ],
        supply=[7.0, 5.0, 7.0],
        demand=[5.0, 4.0, 6.0, 4.0],
        initialMethod="least_cost",
        optimizationMethod="potential",
    )


class TestSolverService:

    def test_solve_returns_response(self, service, simple_request):
        response = service.solve(simple_request)
        assert response is not None

    def test_allocation_matrix_shape(self, service, simple_request):
        response = service.solve(simple_request)
        assert len(response.allocationMatrix) == 2
        for row in response.allocationMatrix:
            assert len(row) == 3

    def test_total_cost_is_positive(self, service, simple_request):
        response = service.solve(simple_request)
        assert response.totalCost > 0

    def test_is_optimal_when_using_potential(self, service, simple_request):
        response = service.solve(simple_request)
        assert response.isOptimal is True

    def test_classic_3x4_optimal_cost(self, service, classic_request):
        """Bài toán cổ điển 3×4 nên cho f* = 50."""
        response = service.solve(classic_request)
        assert response.isOptimal is True
        assert abs(response.totalCost - 50.0) < 1e-3, (
            f"Chi phí tối ưu = {response.totalCost}, cần ≈ 50"
        )

    def test_no_optimization_returns_initial_solution(self, service, simple_request):
        request = SolveRequest(**{
            **simple_request.model_dump(),
            "optimizationMethod": "none",
        })
        response = service.solve(request)
        assert response is not None
        assert response.totalCost > 0

    def test_northwest_corner_method(self, service, simple_request):
        request = SolveRequest(**{
            **simple_request.model_dump(),
            "initialMethod": "northwest_corner",
        })
        response = service.solve(request)
        assert response is not None
        assert response.isOptimal is True

    def test_invalid_cost_matrix_raises(self, service):
        from fastapi import HTTPException
        request = SolveRequest(
            costMatrix=[[-1.0, 2.0], [3.0, 4.0]],  # Âm
            supply=[5.0, 5.0],
            demand=[5.0, 5.0],
        )
        with pytest.raises(HTTPException) as exc_info:
            service.solve(request)
        assert exc_info.value.status_code == 400

    def test_shape_mismatch_raises(self, service):
        from fastapi import HTTPException
        request = SolveRequest(
            costMatrix=[[1.0, 2.0], [3.0, 4.0]],
            supply=[5.0, 5.0, 5.0],  # 3 phần tử nhưng cost_matrix chỉ 2 hàng
            demand=[7.5, 7.5],
        )
        with pytest.raises(HTTPException) as exc_info:
            service.solve(request)
        assert exc_info.value.status_code == 400

    def test_unbalanced_problem_gets_balanced(self, service):
        """Bài toán không cân bằng được cân bằng tự động, trả cảnh báo."""
        request = SolveRequest(
            costMatrix=[[2.0, 3.0], [5.0, 4.0]],
            supply=[20.0, 30.0],  # Tổng = 50
            demand=[15.0, 20.0],  # Tổng = 35 → không cân bằng
        )
        response = service.solve(request)
        assert response is not None
        # Phải có warning về cân bằng
        assert any("dummy" in w.lower() or "cân bằng" in w.lower() for w in response.warnings), (
            f"Không có cảnh báo cân bằng. Warnings: {response.warnings}"
        )

    def test_response_has_source_names(self, service):
        request = SolveRequest(
            costMatrix=[[2.0, 3.0], [5.0, 4.0]],
            supply=[10.0, 10.0],
            demand=[10.0, 10.0],
            sourceNames=["Hà Nội", "Đà Nẵng"],
            destinationNames=["TPHCM", "Cần Thơ"],
        )
        response = service.solve(request)
        assert response.sourceNames == ["Hà Nội", "Đà Nẵng"]
        assert response.destinationNames == ["TPHCM", "Cần Thơ"]

    def test_iterations_included_by_default(self, service, simple_request):
        response = service.solve(simple_request)
        assert len(response.iterations) > 0

    def test_iterations_excluded_when_requested(self, service, simple_request):
        request = SolveRequest(**{
            **simple_request.model_dump(),
            "includeIterations": False,
        })
        response = service.solve(request)
        assert len(response.iterations) == 0
