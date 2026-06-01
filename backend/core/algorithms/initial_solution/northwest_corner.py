"""
backend/core/algorithms/initial_solution/northwest_corner.py
=============================================================
Phương pháp Góc Tây Bắc (Northwest Corner Method).

Tách từ initial_solution.py cũ, refactored để:
  - Tuân thủ interface InitialSolutionAlgorithm.
  - Trả TransportationSolution.
  - Không phụ thuộc UI hay file system.
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


class NorthwestCornerMethod(InitialSolutionAlgorithm):
    """
    Tìm phương án cực biên xuất phát bằng Phương pháp Góc Tây Bắc.

    Thuật toán:
        Bước 1.1 – Chọn ô ở góc Tây Bắc (hàng nhỏ nhất, cột nhỏ nhất chưa xóa).
        Bước 1.2 – Phân phối x_{ij} = min(a_i, b_j).
        Bước 1.3 – Cập nhật lượng thu phát và thu hẹp bảng.
        Bước 1.4 – Lặp lại.

    Đặc điểm: Nhanh, đơn giản, nhưng thường cho chi phí ban đầu cao.
    """

    @property
    def name(self) -> str:
        return "Northwest Corner"

    @property
    def description(self) -> str:
        return "Bắt đầu từ góc tây bắc của bảng. Đơn giản nhưng thường cho chi phí ban đầu cao."

    def solve(self, problem: TransportationProblem) -> TransportationSolution:
        """
        Tìm phương án cực biên xuất phát bằng Northwest Corner.

        Returns
        -------
        TransportationSolution với phương án ban đầu.
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

        logger.info("GIAI ĐOẠN 1: PHƯƠNG ÁN CỰC BIÊN – GÓC TÂY BẮC")

        step = 0
        while True:
            active_rows = [i for i in range(m) if i not in deleted_rows]
            active_cols = [j for j in range(n) if j not in deleted_cols]
            if not active_rows or not active_cols:
                break
            if sum(supply[i] for i in active_rows) < _EPS:
                break

            step += 1

            # Góc Tây Bắc: hàng nhỏ nhất, cột nhỏ nhất
            i0 = active_rows[0]
            j0 = active_cols[0]

            allocation = min(supply[i0], demand[j0])
            X[i0, j0] = allocation
            basis.add(i0, j0)

            logger.debug(
                f"Bước {step:>2d}: Ô ({i0+1},{j0+1}) [Góc TN] | "
                f"c={C[i0,j0]:.4g} | x={allocation:.4g}"
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

        initial_cost = float(np.sum(C * X))
        allocation_list = X.tolist()
        basis_cells = sorted(basis.to_set())

        initial_iter = IterationResult(
            step=0,
            allocation_matrix=allocation_list,
            total_cost=initial_cost,
            description=f"Phương án ban đầu (Northwest Corner). Chi phí = {initial_cost:.4g}",
        )

        return TransportationSolution(
            allocation_matrix=allocation_list,
            total_cost=initial_cost,
            is_optimal=False,
            iterations=[initial_iter],
            message="Phương án khởi tạo bằng Northwest Corner Method.",
            initial_cost=initial_cost,
            num_iterations=0,
            basis_cells=basis_cells,
        )

    def _get_basis(self, problem: TransportationProblem) -> Tuple[np.ndarray, BasisSet]:
        """Internal helper: trả (X, basis) để optimizer dùng."""
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

        while True:
            active_rows = [i for i in range(m) if i not in deleted_rows]
            active_cols = [j for j in range(n) if j not in deleted_cols]
            if not active_rows or not active_cols:
                break
            if sum(supply[i] for i in active_rows) < _EPS:
                break

            i0 = active_rows[0]
            j0 = active_cols[0]

            allocation = min(supply[i0], demand[j0])
            X[i0, j0] = allocation
            basis.add(i0, j0)

            supply[i0] -= allocation
            demand[j0] -= allocation
            if abs(supply[i0]) < _EPS:
                supply[i0] = 0.0
            if abs(demand[j0]) < _EPS:
                demand[j0] = 0.0

            if supply[i0] == 0.0 and demand[j0] == 0.0:
                deleted_cols.add(j0)
            elif supply[i0] == 0.0:
                deleted_rows.add(i0)
            else:
                deleted_cols.add(j0)

        required = m + n - 1
        if len(basis) < required:
            basis = supplement_degenerate_cells(basis, X, m, n, required)

        return X, basis
