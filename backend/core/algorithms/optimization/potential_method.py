"""
backend/core/algorithms/optimization/potential_method.py
==========================================================
Thuật toán Thế vị (Potential Method / MODI Method).

Tách từ potential_method.py cũ, refactored để:
  - Tuân thủ interface OptimizationAlgorithm.
  - Trả TransportationSolution với đầy đủ iterations.
  - Log vào logger, KHÔNG ghi file trực tiếp.
  - Không phụ thuộc UI, file system, FastAPI.

Các bước thuật toán:
  2.1 – Tính thế vị u_i, v_j bằng BFS.
  2.2 – Tính ma trận ước lượng Δ_ij = u_i + v_j - c_ij.
  2.3 – Kiểm tra tính tối ưu (Δ_ij ≤ 0 cho tất cả ô loại).
  2.4 – Tìm chu trình qua ô vào bằng DFS, điều chỉnh luồng, cập nhật cơ sở.
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from backend.core.algorithms.base import OptimizationAlgorithm
from backend.core.algorithms.initial_solution._basis import BasisSet
from backend.core.models.problem import TransportationProblem
from backend.core.models.solution import IterationResult, TransportationSolution

logger = logging.getLogger(__name__)
_EPS = 1e-9


class PotentialMethod(OptimizationAlgorithm):
    """
    Thuật toán Thế vị (Potential Method / MODI Method).

    Tối ưu hóa phương án cực biên ban đầu bằng cách lặp:
      - Tính thế vị → ước lượng → tìm ô vào → tìm chu trình → điều chỉnh luồng.

    Phát hiện cycling qua lịch sử frozenset tập cơ sở.
    """

    def __init__(self, max_iterations: int = 1000) -> None:
        self.max_iterations = max_iterations

    @property
    def name(self) -> str:
        return "Potential Method"

    @property
    def description(self) -> str:
        return "Tối ưu nghiệm bằng phương pháp thế vị (MODI). Đảm bảo hội tụ về nghiệm tối ưu."

    def optimize(
        self,
        problem: TransportationProblem,
        initial_solution: TransportationSolution,
    ) -> TransportationSolution:
        """
        Tối ưu hóa phương án ban đầu bằng Thuật toán Thế vị.

        Parameters
        ----------
        problem : TransportationProblem
        initial_solution : TransportationSolution
            Phương án cực biên ban đầu (từ InitialSolutionAlgorithm).

        Returns
        -------
        TransportationSolution với iterations đầy đủ.
        """
        C = np.array(problem.cost_matrix, dtype=float)
        A = np.array(problem.supply, dtype=float)
        B = np.array(problem.demand, dtype=float)
        m, n = C.shape

        # Khôi phục basis từ initial_solution
        X = np.array(initial_solution.allocation_matrix, dtype=float)
        basis = BasisSet()
        for cell in initial_solution.basis_cells:
            basis.add(cell[0], cell[1])

        # Nếu không có basis_cells, tái tạo từ allocation_matrix
        if len(basis) == 0:
            for i in range(m):
                for j in range(n):
                    if X[i, j] > _EPS:
                        basis.add(i, j)

        seen_bases: Set[frozenset] = set()
        seen_bases.add(basis.frozen())

        # Giữ tất cả iterations (bắt đầu từ initial_solution iterations)
        all_iterations: List[IterationResult] = list(initial_solution.iterations)
        warnings: List[str] = []
        initial_cost = float(np.sum(C * X))

        logger.info(f"GIAI ĐOẠN 2: THUẬT TOÁN THẾ VỊ. Chi phí ban đầu = {initial_cost:.4g}")

        for iteration in range(1, self.max_iterations + 1):

            # Bước 2.1: Tính thế vị
            try:
                u, v = _compute_potentials(C, basis, m, n)
            except ValueError as exc:
                warnings.append(f"Lỗi tính thế vị: {exc}")
                break

            # Bước 2.2: Tính ma trận Δ
            Delta = _compute_deltas(C, u, v, basis, m, n)

            # Bước 2.3: Kiểm tra tối ưu
            pivot, all_tied = _find_pivot_cells(Delta, basis, m, n)

            # Xây dựng iteration result cho vòng lặp hiện tại
            # (với thế vị và reduced costs)
            reduced_costs = [
                [None if np.isnan(Delta[i, j]) else float(Delta[i, j]) for j in range(n)]
                for i in range(m)
            ]
            potentials_u = [float(x) for x in u]
            potentials_v = [float(x) for x in v]

            if pivot is None:
                # Tối ưu!
                cost_opt = float(np.sum(C * X))
                logger.info(f">>> TỐI ƯU sau {iteration - 1} vòng lặp. Chi phí = {cost_opt:.4g}")

                # Thêm iteration cuối (trạng thái tối ưu)
                opt_iter = IterationResult(
                    step=iteration,
                    allocation_matrix=X.tolist(),
                    total_cost=cost_opt,
                    potentials_u=potentials_u,
                    potentials_v=potentials_v,
                    reduced_costs=reduced_costs,
                    is_optimal=True,
                    description=f"✓ Phương án tối ưu. Tất cả Δ_ij ≤ 0. f(X*) = {cost_opt:.4g}",
                )
                all_iterations.append(opt_iter)

                basis_cells = sorted(basis.to_set())
                pct_improvement = (
                    (initial_cost - cost_opt) / initial_cost * 100
                    if initial_cost > _EPS else 0.0
                )

                return TransportationSolution(
                    allocation_matrix=X.tolist(),
                    total_cost=cost_opt,
                    is_optimal=True,
                    iterations=all_iterations,
                    message=(
                        f"Giải thành công. Chi phí tối ưu = {cost_opt:.4g}. "
                        f"Cải thiện {pct_improvement:.1f}% so với ban đầu."
                    ),
                    warnings=warnings,
                    initial_cost=initial_cost,
                    num_iterations=iteration - 1,
                    basis_cells=basis_cells,
                )

            # Bước 2.4.2: Tìm chu trình
            cycle = _find_cycle_dfs(pivot, basis)
            if cycle is None:
                raise RuntimeError(
                    f"Không tìm được chu trình qua ô vào ({pivot[0]+1},{pivot[1]+1}). "
                    f"Tập cơ sở có thể bị lỗi: {basis}"
                )

            # Bước 2.4.3: Điều chỉnh luồng
            X_new, basis_new, entering, leaving, theta = _adjust_flow(X, cycle, basis)

            new_cost = float(np.sum(C * X_new))
            description = (
                f"Vòng lặp {iteration}: θ={theta:.4g} | "
                f"O vào ({entering[0]+1},{entering[1]+1}) → O ra ({leaving[0]+1},{leaving[1]+1}) | "
                f"Chi phí: {float(np.sum(C * X)):.4g} → {new_cost:.4g}"
            )

            if theta < _EPS:
                warnings.append(f"Suy biến tại vòng lặp {iteration} (θ ≈ 0).")

            # Lưu iteration result
            iter_result = IterationResult(
                step=iteration,
                allocation_matrix=X_new.tolist(),
                total_cost=new_cost,
                potentials_u=potentials_u,
                potentials_v=potentials_v,
                reduced_costs=reduced_costs,
                entering_cell=entering,
                leaving_cell=leaving,
                cycle=cycle,
                theta=theta,
                cost_delta=new_cost - float(np.sum(C * X)),
                is_optimal=False,
                description=description,
            )
            all_iterations.append(iter_result)

            # Phát hiện cycling
            basis_key = basis_new.frozen()
            if basis_key in seen_bases:
                warnings.append(
                    f"[CYCLING] Tập cơ sở lặp lại tại vòng lặp {iteration}. "
                    f"Có thể bị cycling do suy biến."
                )
            seen_bases.add(basis_key)

            X = X_new
            basis = basis_new

        # Hết giới hạn vòng lặp
        cost_final = float(np.sum(C * X))
        warnings.append(
            f"Đạt giới hạn {self.max_iterations} vòng lặp. "
            f"Phương án có thể chưa tối ưu."
        )
        basis_cells = sorted(basis.to_set())

        return TransportationSolution(
            allocation_matrix=X.tolist(),
            total_cost=cost_final,
            is_optimal=False,
            iterations=all_iterations,
            message=f"Dừng sau {self.max_iterations} vòng lặp (chưa tối ưu). Chi phí = {cost_final:.4g}.",
            warnings=warnings,
            initial_cost=initial_cost,
            num_iterations=self.max_iterations,
            basis_cells=basis_cells,
        )


# ============================================================
# Các hàm thuần nội bộ (không phụ thuộc class)
# ============================================================

def _compute_potentials(
    C: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Tính thế vị u_i, v_j bằng BFS. u[0] = 0."""
    u = np.full(m, np.nan)
    v = np.full(n, np.nan)
    u[0] = 0.0

    row_to_cols: Dict[int, List[int]] = defaultdict(list)
    col_to_rows: Dict[int, List[int]] = defaultdict(list)
    for (i, j) in basis:
        row_to_cols[i].append(j)
        col_to_rows[j].append(i)

    queue: deque = deque([("row", 0)])
    while queue:
        node_type, idx = queue.popleft()
        if node_type == "row":
            for j in row_to_cols[idx]:
                if np.isnan(v[j]):
                    v[j] = C[idx, j] - u[idx]
                    queue.append(("col", j))
        else:
            for i in col_to_rows[idx]:
                if np.isnan(u[i]):
                    u[i] = C[i, idx] - v[idx]
                    queue.append(("row", i))

    missing_u = [i + 1 for i in range(m) if np.isnan(u[i])]
    missing_v = [j + 1 for j in range(n) if np.isnan(v[j])]
    if missing_u or missing_v:
        raise ValueError(
            f"Tập cơ sở không liên thông – không tính được thế vị: "
            f"u thiếu tại hàng {missing_u}, v thiếu tại cột {missing_v}."
        )
    return u, v


def _compute_deltas(
    C: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> np.ndarray:
    """Tính Δ_ij = u_i + v_j - c_ij cho ô loại. NaN cho ô cơ sở."""
    Delta = np.full((m, n), np.nan)
    for i in range(m):
        for j in range(n):
            if (i, j) not in basis:
                Delta[i, j] = u[i] + v[j] - C[i, j]
    return Delta


def _find_pivot_cells(
    Delta: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> Tuple[Optional[Tuple[int, int]], List[Tuple[int, int]]]:
    """Tìm ô vào có Δ_ij lớn nhất dương. Trả (pivot, all_tied)."""
    max_delta = _EPS
    pivot: Optional[Tuple[int, int]] = None
    all_tied: List[Tuple[int, int]] = []

    for i in range(m):
        for j in range(n):
            if (i, j) in basis:
                continue
            delta = Delta[i, j]
            if np.isnan(delta):
                continue
            if delta > max_delta + _EPS:
                max_delta = delta
                pivot = (i, j)
                all_tied = [(i, j)]
            elif delta > _EPS and abs(delta - max_delta) <= _EPS:
                all_tied.append((i, j))

    return pivot, all_tied


def _find_cycle_dfs(
    entering_cell: Tuple[int, int],
    basis: BasisSet,
) -> Optional[List[Tuple[int, int]]]:
    """Tìm chu trình điều chỉnh qua ô vào bằng DFS."""
    i_s, j_s = entering_cell
    basis_set: Set[Tuple[int, int]] = basis.to_set()

    row_map: Dict[int, List[int]] = defaultdict(list)
    col_map: Dict[int, List[int]] = defaultdict(list)
    all_cells: Set[Tuple[int, int]] = basis_set | {entering_cell}
    for (i, j) in all_cells:
        row_map[i].append(j)
        col_map[j].append(i)

    def dfs(
        path: List[Tuple[int, int]],
        direction: str,
    ) -> Optional[List[Tuple[int, int]]]:
        curr_i, curr_j = path[-1]
        next_dir = "v" if direction == "h" else "h"

        if direction == "h":
            candidates = [(curr_i, j) for j in row_map[curr_i] if j != curr_j]
        else:
            candidates = [(i, curr_j) for i in col_map[curr_j] if i != curr_i]

        for candidate in candidates:
            if candidate == entering_cell and len(path) >= 3:
                return path
            if candidate in basis_set and candidate not in path[1:]:
                result = dfs(path + [candidate], next_dir)
                if result is not None:
                    return result

        return None

    return dfs([entering_cell], "h")


def _adjust_flow(
    X: np.ndarray,
    cycle: List[Tuple[int, int]],
    basis: BasisSet,
) -> Tuple[np.ndarray, BasisSet, Tuple[int, int], Tuple[int, int], float]:
    """Điều chỉnh luồng theo chu trình. Trả (X_new, basis_new, entering, leaving, theta)."""
    entering_cell = cycle[0]
    plus_cells = [cycle[k] for k in range(0, len(cycle), 2)]
    minus_cells = [cycle[k] for k in range(1, len(cycle), 2)]

    theta_candidates = [(X[i, j], (i, j)) for (i, j) in minus_cells]
    theta, leaving_cell = min(theta_candidates, key=lambda t: (t[0], t[1]))

    X_new = X.copy()
    for (i, j) in plus_cells:
        X_new[i, j] += theta
    for (i, j) in minus_cells:
        X_new[i, j] -= theta
        if abs(X_new[i, j]) < _EPS:
            X_new[i, j] = 0.0

    basis_new = basis.copy()
    basis_new.add(*entering_cell)
    basis_new.remove(*leaving_cell)

    return X_new, basis_new, entering_cell, leaving_cell, theta
