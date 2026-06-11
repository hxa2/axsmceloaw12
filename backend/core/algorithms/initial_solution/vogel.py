"""
backend/core/algorithms/initial_solution/vogel.py
===================================================
Phương pháp Xấp xỉ Vogel (Vogel Approximation Method – VAM).
"""

import logging
from typing import Set, Tuple

import numpy as np

from backend.core.algorithms.base import InitialSolutionAlgorithm
from backend.core.algorithms.initial_solution._basis import (
    BasisSet,
    supplement_degenerate_cells,
)
from backend.core.models.problem import TransportationProblem
from backend.core.models.solution import IterationResult, TransportationSolution

logger = logging.getLogger(__name__)
_EPS = 1e-9


class VogelApproximationMethod(InitialSolutionAlgorithm):
    """
    Phương pháp Xấp xỉ Vogel.

    Thường cho nghiệm ban đầu tốt hơn Least Cost và Northwest Corner,
    nhưng phức tạp hơn khi cài đặt.
    """

    @property
    def name(self) -> str:
        return "Vogel Approximation"

    @property
    def description(self) -> str:
        return "Phương pháp xấp xỉ Vogel (VAM). Thường cho nghiệm ban đầu tốt nhất."

    def solve(self, problem: TransportationProblem) -> TransportationSolution:
        """
        Tìm phương án cực biên bằng Vogel Approximation Method.
        """
        X, basis = self._get_basis(problem)

        C = np.array(problem.cost_matrix, dtype=float)
        initial_cost = float(np.sum(C * X))
        allocation_list = X.tolist()
        basis_cells = sorted(basis.to_set())

        initial_iter = IterationResult(
            step=0,
            allocation_matrix=allocation_list,
            total_cost=initial_cost,
            description=f"Phương án ban đầu. Chi phí = {initial_cost:.4g}",
        )

        return TransportationSolution(
            allocation_matrix=allocation_list,
            total_cost=initial_cost,
            is_optimal=False,
            iterations=[initial_iter],
            message="Phương án khởi tạo bằng Vogel Approximation Method.",
            initial_cost=initial_cost,
            num_iterations=0,
            basis_cells=basis_cells,
        )

    def _get_basis(self, problem: TransportationProblem) -> Tuple[np.ndarray, BasisSet]:
        """
        Internal helper: trả (X, basis) dạng numpy để solver_service có thể
        tiếp tục tối ưu hóa.
        """
        C = np.array(problem.cost_matrix, dtype=float)
        A = np.array(problem.supply, dtype=float)
        B = np.array(problem.demand, dtype=float)
        m, n = C.shape

        X = np.zeros((m, n), dtype=float)
        supply = A.copy()
        demand = B.copy()
        basis = BasisSet()
        deleted_rows: Set[int] = set()
        deleted_cols: Set[int] = set()

        logger.info("GIAI ĐOẠN 1: PHƯƠNG ÁN CỰC BIÊN – PHƯƠNG PHÁP XẤP XỈ VOGEL")

        step = 0
        while True:
            active_rows = [i for i in range(m) if i not in deleted_rows]
            active_cols = [j for j in range(n) if j not in deleted_cols]
            if not active_rows or not active_cols:
                break
            remaining = sum(supply[i] for i in active_rows)
            if remaining < _EPS:
                break

            step += 1

            # Tính chênh lệch (Penalty) cho từng hàng
            row_penalties = {}
            for i in active_rows:
                costs = sorted([C[i, j] for j in active_cols])
                if len(costs) >= 2:
                    row_penalties[i] = costs[1] - costs[0]
                elif len(costs) == 1:
                    row_penalties[i] = costs[0]
                else:
                    row_penalties[i] = 0.0

            # Tính chênh lệch (Penalty) cho từng cột
            col_penalties = {}
            for j in active_cols:
                costs = sorted([C[i, j] for i in active_rows])
                if len(costs) >= 2:
                    col_penalties[j] = costs[1] - costs[0]
                elif len(costs) == 1:
                    col_penalties[j] = costs[0]
                else:
                    col_penalties[j] = 0.0

            max_penalty = -1.0
            selected_type = None  # 'row' or 'col'
            selected_idx = -1

            # Lựa chọn hàng hoặc cột có mức Penalty lớn nhất
            for i, p in row_penalties.items():
                if p > max_penalty:
                    max_penalty = p
                    selected_type = 'row'
                    selected_idx = i

            for j, p in col_penalties.items():
                if p > max_penalty:
                    max_penalty = p
                    selected_type = 'col'
                    selected_idx = j

            # Tìm ô có cước phí nhỏ nhất trong hàng/cột được chọn
            i0, j0 = -1, -1
            min_cost = np.inf

            if selected_type == 'row':
                i = selected_idx
                for j in active_cols:
                    if C[i, j] < min_cost:
                        min_cost = C[i, j]
                        i0, j0 = i, j
            elif selected_type == 'col':
                j = selected_idx
                for i in active_rows:
                    if C[i, j] < min_cost:
                        min_cost = C[i, j]
                        i0, j0 = i, j
            else:
                break  # Không nên xảy ra

            # Phân phối
            allocation = min(supply[i0], demand[j0])
            X[i0, j0] = allocation
            basis.add(i0, j0)

            logger.debug(
                f"Bước {step:>2d}: Chọn ô ({i0+1},{j0+1}) | "
                f"c={C[i0,j0]:.4g} | x={allocation:.4g} | penalty={max_penalty:.4g}"
            )

            supply[i0] -= allocation
            demand[j0] -= allocation
            if abs(supply[i0]) < _EPS:
                supply[i0] = 0.0
            if abs(demand[j0]) < _EPS:
                demand[j0] = 0.0

            if supply[i0] == 0.0 and demand[j0] == 0.0:
                deleted_cols.add(j0)  # Suy biến: chỉ xóa cột
            elif supply[i0] == 0.0:
                deleted_rows.add(i0)
            else:
                deleted_cols.add(j0)

        required = m + n - 1
        if len(basis) < required:
            basis = supplement_degenerate_cells(basis, X, m, n, required)

        return X, basis
