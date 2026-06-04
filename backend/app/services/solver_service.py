"""
backend/app/services/solver_service.py
=========================================
Service điều phối việc giải bài toán vận tải.

Trách nhiệm:
  - Nhận SolveRequest.
  - Validate dữ liệu.
  - Cân bằng bài toán nếu cần.
  - Chọn và gọi initial algorithm.
  - Chọn và gọi optimization algorithm.
  - Map kết quả sang SolveResponse.
  - Trả lỗi rõ ràng (không để lỗi Python thô).

Không được chứa logic thuật toán.
Không được render UI.
"""

import logging
from typing import Optional

from fastapi import HTTPException, status

from backend.app.schemas.request import SolveRequest
from backend.app.schemas.response import IterationResponse, SolveResponse
from backend.core.algorithms.initial_solution import (
    LeastCostMethod,
    NorthwestCornerMethod,
    VogelApproximationMethod,
)
from backend.core.algorithms.optimization import PotentialMethod
from backend.core.models.problem import TransportationProblem
from backend.core.models.solution import TransportationSolution
from backend.core.validation import TransportationValidator

logger = logging.getLogger(__name__)


class SolverService:
    """
    Service chính để giải bài toán vận tải.

    Usage:
        service = SolverService()
        response = service.solve(request)
    """

    def __init__(self) -> None:
        self._validator = TransportationValidator()

        # Registry các thuật toán initial solution
        self._initial_methods = {
            "least_cost": LeastCostMethod,
            "northwest_corner": NorthwestCornerMethod,
            "vogel": VogelApproximationMethod,
        }

        # Registry các thuật toán optimization
        self._optimization_methods = {
            "potential": PotentialMethod,
            "none": None,  # Chỉ trả initial solution
        }

    def solve(self, request: SolveRequest) -> SolveResponse:
        """
        Giải bài toán vận tải từ request.

        Raises
        ------
        HTTPException 400: Nếu dữ liệu đầu vào không hợp lệ.
        HTTPException 422: Nếu thuật toán không hỗ trợ.
        HTTPException 500: Nếu thuật toán gặp lỗi nội bộ.
        """
        logger.info(
            f"SolverService.solve: method={request.initialMethod}/{request.optimizationMethod}, "
            f"size={len(request.supply)}×{len(request.demand)}"
        )

        # ── 1. Validate ────────────────────────────────────────────────────
        validation = self._validator.validate(
            cost_matrix=request.costMatrix,
            supply=request.supply,
            demand=request.demand,
        )
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation.first_error or "Dữ liệu đầu vào không hợp lệ.",
            )

        # Collect warnings từ validation
        extra_warnings: list[str] = list(validation.warnings)

        # ── 2. Cân bằng bài toán nếu cần ─────────────────────────────────
        balance_info = self._validator.balance_problem(
            request.costMatrix, request.supply, request.demand
        )
        extra_warnings.extend(balance_info.warnings)

        # Xử lý tên nguồn/đích: bắt đầu từ request, append tên dummy nếu cần
        source_names: Optional[list[str]] = (
            list(request.sourceNames) if request.sourceNames else None
        )
        destination_names: Optional[list[str]] = (
            list(request.destinationNames) if request.destinationNames else None
        )

        if balance_info.balance_type == "dummy_destination":
            # Cung > Cầu → thêm dummy destination
            if destination_names is not None:
                destination_names.append("Dummy")
            # Nếu destination_names là None, TransportationProblem sẽ tự tạo tên D1..Dn
            # nhưng ta cần đảm bảo tên cuối cùng là "Dummy"
            if destination_names is None:
                destination_names = [
                    f"D{j + 1}" for j in range(len(balance_info.demand) - 1)
                ] + ["Dummy"]
        elif balance_info.balance_type == "dummy_source":
            # Cầu > Cung → thêm dummy source
            if source_names is not None:
                source_names.append("Dummy")
            if source_names is None:
                source_names = [
                    f"S{i + 1}" for i in range(len(balance_info.supply) - 1)
                ] + ["Dummy"]

        # ── 3. Tạo problem ─────────────────────────────────────────────────
        problem = TransportationProblem(
            cost_matrix=balance_info.cost_matrix,
            supply=balance_info.supply,
            demand=balance_info.demand,
            source_names=source_names,
            destination_names=destination_names,
        )

        # ── 4. Chọn và chạy initial algorithm ────────────────────────────
        initial_cls = self._initial_methods.get(request.initialMethod)
        if initial_cls is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Phương pháp khởi tạo '{request.initialMethod}' không hỗ trợ.",
            )

        try:
            initial_algo = initial_cls()
            initial_solution = initial_algo.solve(problem)
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )
        except RuntimeError as exc:
            logger.exception("Initial algorithm RuntimeError")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi tìm phương án ban đầu: {exc}",
            )

        # ── 5. Chọn và chạy optimization algorithm ───────────────────────
        if request.optimizationMethod == "none":
            final_solution = initial_solution
        else:
            opt_cls = self._optimization_methods.get(request.optimizationMethod)
            if opt_cls is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Phương pháp tối ưu '{request.optimizationMethod}' không hỗ trợ.",
                )
            try:
                opt_algo = opt_cls()
                final_solution = opt_algo.optimize(problem, initial_solution)
            except RuntimeError as exc:
                logger.exception("Optimization algorithm RuntimeError")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Lỗi tối ưu hóa: {exc}",
                )

        # Gộp warnings
        all_warnings = extra_warnings + final_solution.warnings

        # ── 6. Map sang response ──────────────────────────────────────────
        return self._map_to_response(
            solution=final_solution,
            problem=problem,
            balance_info=balance_info,
            extra_warnings=all_warnings,
            include_iterations=request.includeIterations,
        )

    def _map_to_response(
        self,
        solution: TransportationSolution,
        problem: TransportationProblem,
        balance_info,
        extra_warnings: list[str],
        include_iterations: bool,
    ) -> SolveResponse:
        """Map TransportationSolution sang SolveResponse (Pydantic)."""
        iterations: list[IterationResponse] = []

        if include_iterations:
            for it in solution.iterations:
                iterations.append(
                    IterationResponse(
                        step=it.step,
                        allocationMatrix=it.allocation_matrix,
                        totalCost=it.total_cost,
                        potentialsU=it.potentials_u,
                        potentialsV=it.potentials_v,
                        reducedCosts=it.reduced_costs,
                        enteringCell=it.entering_cell,
                        leavingCell=it.leaving_cell,
                        cycle=it.cycle,
                        theta=it.theta,
                        costDelta=it.cost_delta,
                        isOptimal=it.is_optimal,
                        description=it.description,
                    )
                )

        return SolveResponse(
            allocationMatrix=solution.allocation_matrix,
            totalCost=solution.total_cost,
            isOptimal=solution.is_optimal,
            iterations=iterations,
            message=solution.message,
            warnings=extra_warnings,
            initialCost=solution.initial_cost,
            numIterations=solution.num_iterations,
            basisCells=solution.basis_cells,
            costMatrix=problem.cost_matrix,
            supply=problem.supply,
            demand=problem.demand,
            sourceNames=problem.source_names,
            destinationNames=problem.destination_names,
            # Balance metadata
            isBalancedOriginal=balance_info.is_balanced_original,
            balanceType=balance_info.balance_type,
            dummySourceIndex=balance_info.dummy_source_index,
            dummyDestinationIndex=balance_info.dummy_destination_index,
            originalSupplyTotal=balance_info.original_supply_total,
            originalDemandTotal=balance_info.original_demand_total,
        )
