"""
backend/core/algorithms/initial_solution/least_cost.py
=========================================================
Phương pháp Cực tiểu Chi phí (Least Cost Method).

Tách từ initial_solution.py cũ, refactored để:
  - Tuân thủ interface InitialSolutionAlgorithm.
  - Trả TransportationSolution (không BasisSet raw).
  - Không phụ thuộc UI hay file system.
"""

import logging
from typing import List, Optional, Set, Tuple

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


class LeastCostMethod(InitialSolutionAlgorithm):
    """
    Tìm phương án cực biên xuất phát bằng Phương pháp Cực tiểu Chi phí.

    Thuật toán:
        Bước 1.1 – Tìm ô (i0, j0) có c_ij nhỏ nhất trong phần bảng chưa xóa.
        Bước 1.2 – Phân phối x_{i0,j0} = min(a_{i0}, b_{j0}).
        Bước 1.3 – Cập nhật và thu hẹp bảng (xóa hàng hoặc cột).
                   Trường hợp suy biến (a_{i0} = b_{j0}): chỉ xóa cột.
        Bước 1.4 – Lặp lại đến khi phân phối hết.
    """

    @property
    def name(self) -> str:
        return "Least Cost"

    @property
    def description(self) -> str:
        return "Chọn ô có chi phí nhỏ nhất trước. Cho nghiệm ban đầu thường tốt hơn Góc Tây Bắc."

    def solve(self, problem: TransportationProblem) -> TransportationSolution:
        """
        Tìm phương án cực biên xuất phát.

        Returns
        -------
        TransportationSolution với:
          - allocation_matrix: ma trận phân phối ban đầu.
          - is_optimal: False (chưa tối ưu).
          - iterations: 1 iteration (bước khởi tạo).
          - basis_cells: danh sách ô cơ sở.
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

        logger.info("GIAI ĐOẠN 1: PHƯƠNG ÁN CỰC BIÊN – CỰC TIỂU CHI PHÍ")

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

            # Bước 1.1: Tìm ô có cước phí nhỏ nhất
            min_cost, candidates = _find_min_cost_cells(C, deleted_rows, deleted_cols, m, n)
            if not candidates:
                break

            # Chọn ô tốt nhất
            i0, j0 = _select_best_candidate(candidates, supply, demand)

            # Bước 1.2: Phân phối
            allocation = min(supply[i0], demand[j0])
            X[i0, j0] = allocation
            basis.add(i0, j0)

            logger.debug(
                f"Bước {step:>2d}: Chọn ô ({i0+1},{j0+1}) | "
                f"c={C[i0,j0]:.4g} | x={allocation:.4g}"
            )

            # Bước 1.3: Cập nhật cung/cầu
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

        # Bổ sung ô suy biến nếu cần
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
            description=f"Phương án ban đầu. Chi phí = {initial_cost:.4g}",
        )

        return TransportationSolution(
            allocation_matrix=allocation_list,
            total_cost=initial_cost,
            is_optimal=False,
            iterations=[initial_iter],
            message="Phương án khởi tạo bằng Least Cost Method.",
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

        while True:
            active_rows = [i for i in range(m) if i not in deleted_rows]
            active_cols = [j for j in range(n) if j not in deleted_cols]
            if not active_rows or not active_cols:
                break
            if sum(supply[i] for i in active_rows) < _EPS:
                break

            min_cost, candidates = _find_min_cost_cells(C, deleted_rows, deleted_cols, m, n)
            if not candidates:
                break

            i0, j0 = _select_best_candidate(candidates, supply, demand)
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


# ── Helpers nội bộ ────────────────────────────────────────────────────────

def _find_min_cost_cells(
    C: np.ndarray,
    deleted_rows: Set[int],
    deleted_cols: Set[int],
    m: int,
    n: int,
) -> Tuple[float, List[Tuple[int, int]]]:
    min_cost = np.inf
    candidates: List[Tuple[int, int]] = []
    for i in range(m):
        if i in deleted_rows:
            continue
        for j in range(n):
            if j in deleted_cols:
                continue
            cij = C[i, j]
            if cij < min_cost - _EPS:
                min_cost = cij
                candidates = [(i, j)]
            elif abs(cij - min_cost) <= _EPS:
                candidates.append((i, j))
    return min_cost, candidates


def _select_best_candidate(
    candidates: List[Tuple[int, int]],
    supply: np.ndarray,
    demand: np.ndarray,
) -> Tuple[int, int]:
    best_cell: Optional[Tuple[int, int]] = None
    best_alloc = -1.0
    for (i, j) in candidates:
        alloc = min(supply[i], demand[j])
        if alloc > best_alloc + _EPS:
            best_alloc = alloc
            best_cell = (i, j)
        elif abs(alloc - best_alloc) <= _EPS:
            if best_cell is None or (i, j) < best_cell:
                best_cell = (i, j)
    return best_cell  # type: ignore[return-value]
