"""
backend/core/solvers/assignment_solver.py
==========================================
Hungarian Algorithm cho bài toán phân việc.

Hỗ trợ:
  - Ma trận vuông n×n
  - Ma trận không vuông (tự động thêm dummy rows/cols)
  - Minimize và Maximize (max → min bằng c'_ij = P_max - p_ij)

Tham khảo: https://en.wikipedia.org/wiki/Hungarian_algorithm
"""

import copy
from dataclasses import dataclass, field
from typing import Any


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class AssignmentStep:
    """Một bước trong walkthrough Hungarian."""
    type: str
    description: str
    matrix_before: list[list[float]] | None = None
    matrix_after: list[list[float]] | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentResult:
    """Kết quả giải bài toán phân việc."""
    assignment_matrix: list[list[int]]   # 0/1 matrix, 1 = assigned
    assignments: list[dict]              # [{workerIndex, jobIndex, workerName, jobName, value}]
    total_cost: float
    total_profit: float
    objective_value: float
    is_maximize: bool
    original_matrix: list[list[float]]
    working_matrix: list[list[float]]    # ma trận cuối sau Hungarian
    n_workers_orig: int
    n_jobs_orig: int
    n_size: int                          # kích thước sau khi pad
    steps: list[AssignmentStep]
    # Transformation info
    added_dummy_workers: int = 0
    added_dummy_jobs: int = 0
    p_max: float | None = None           # Nếu maximize, lưu P_max


# ── Main Solver ───────────────────────────────────────────────────────────────

def solve_assignment(
    matrix: list[list[float]],
    objective: str = "minimize",
    worker_names: list[str] | None = None,
    job_names: list[str] | None = None,
) -> AssignmentResult:
    """
    Giải bài toán phân việc bằng Hungarian Algorithm.

    Args:
        matrix: Ma trận chi phí/lợi nhuận m×n (có thể không vuông).
        objective: "minimize" hoặc "maximize".
        worker_names: Tên người (tuỳ chọn).
        job_names: Tên công việc (tuỳ chọn).

    Returns:
        AssignmentResult với assignment và walkthrough steps.
    """
    if not matrix or not matrix[0]:
        raise ValueError("Ma trận phân việc không được rỗng.")

    is_maximize = (objective == "maximize")
    n_workers_orig = len(matrix)
    n_jobs_orig = len(matrix[0])

    steps: list[AssignmentStep] = []

    # ── Step 0: Lưu ma trận gốc ──────────────────────────────────────────────
    original_matrix = [row[:] for row in matrix]

    # ── Step 1: Transform Max → Min ──────────────────────────────────────────
    p_max = None
    if is_maximize:
        p_max = max(v for row in matrix for v in row)
        matrix = [[p_max - matrix[i][j] for j in range(n_jobs_orig)] for i in range(n_workers_orig)]
        steps.append(AssignmentStep(
            type="max_to_min",
            description=f"Chuyển bài toán Max thành Min bằng c'_ij = P_max - p_ij (P_max = {p_max}).",
            matrix_before=original_matrix,
            matrix_after=[row[:] for row in matrix],
            details={"p_max": p_max, "formula": "c'_ij = P_max - p_ij"},
        ))

    # ── Step 2: Pad matrix vuông ─────────────────────────────────────────────
    n = max(n_workers_orig, n_jobs_orig)
    added_dummy_workers = n - n_workers_orig
    added_dummy_jobs = n - n_jobs_orig

    mat = [row[:] + [0.0] * added_dummy_jobs for row in matrix]
    for _ in range(added_dummy_workers):
        mat.append([0.0] * n)

    if added_dummy_workers > 0 or added_dummy_jobs > 0:
        steps.append(AssignmentStep(
            type="pad_to_square",
            description=f"Ma trận không vuông ({n_workers_orig}×{n_jobs_orig}), thêm {added_dummy_workers} hàng dummy và {added_dummy_jobs} cột dummy (cost=0) để thành {n}×{n}.",
            matrix_before=[row[:] for row in matrix],
            matrix_after=[row[:] for row in mat],
            details={"addedDummyWorkers": added_dummy_workers, "addedDummyJobs": added_dummy_jobs},
        ))

    # ── Step 3: Row reduction ─────────────────────────────────────────────────
    mat_before_row = [row[:] for row in mat]
    row_minima = []
    for i in range(n):
        r_min = min(mat[i])
        row_minima.append(r_min)
        mat[i] = [v - r_min for v in mat[i]]

    steps.append(AssignmentStep(
        type="row_reduction",
        description="Trừ mỗi hàng cho giá trị nhỏ nhất của hàng đó.",
        matrix_before=mat_before_row,
        matrix_after=[row[:] for row in mat],
        details={"rowMinima": row_minima},
    ))

    # ── Step 4: Column reduction ──────────────────────────────────────────────
    mat_before_col = [row[:] for row in mat]
    col_minima = []
    for j in range(n):
        c_min = min(mat[i][j] for i in range(n))
        col_minima.append(c_min)
        for i in range(n):
            mat[i][j] -= c_min

    steps.append(AssignmentStep(
        type="column_reduction",
        description="Trừ mỗi cột cho giá trị nhỏ nhất của cột đó.",
        matrix_before=mat_before_col,
        matrix_after=[row[:] for row in mat],
        details={"columnMinima": col_minima},
    ))

    # ── Step 5: Hungarian iterations (cover zeros → adjust) ──────────────────
    max_iter = 100
    for iteration in range(max_iter):
        assignment = _find_assignment(mat, n)
        if assignment is not None:
            break

        # Cover zeros
        row_lines, col_lines = _min_cover_zeros(mat, n)
        n_lines = len(row_lines) + len(col_lines)

        mat_before_adj = [row[:] for row in mat]

        steps.append(AssignmentStep(
            type="cover_zeros",
            description=f"Che phủ tất cả số 0 bằng {n_lines} đường (cần {n} đường để có nghiệm).",
            matrix_after=[row[:] for row in mat],
            details={
                "rowLines": list(row_lines),
                "columnLines": list(col_lines),
                "numberOfLines": n_lines,
                "n": n,
            },
        ))

        # Adjust matrix
        covered_rows = set(row_lines)
        covered_cols = set(col_lines)
        uncovered_min = min(
            mat[i][j]
            for i in range(n)
            for j in range(n)
            if i not in covered_rows and j not in covered_cols
        )

        for i in range(n):
            for j in range(n):
                if i not in covered_rows and j not in covered_cols:
                    mat[i][j] -= uncovered_min
                elif i in covered_rows and j in covered_cols:
                    mat[i][j] += uncovered_min
                # Single-line covered: không đổi

        steps.append(AssignmentStep(
            type="adjust_matrix",
            description=f"Phần tử nhỏ nhất chưa bị che phủ = {uncovered_min}. Trừ vào các ô chưa che, cộng vào giao điểm hai đường.",
            matrix_before=mat_before_adj,
            matrix_after=[row[:] for row in mat],
            details={
                "uncoveredMinimum": uncovered_min,
                "rowLines": list(row_lines),
                "columnLines": list(col_lines),
            },
        ))
    else:
        raise RuntimeError("Hungarian Algorithm không hội tụ sau 100 vòng lặp.")

    # ── Step 6: Select independent zeros ─────────────────────────────────────
    assert assignment is not None
    selected_cells = [(i, assignment[i]) for i in range(n)]

    steps.append(AssignmentStep(
        type="select_independent_zeros",
        description="Chọn các số 0 độc lập: mỗi hàng và mỗi cột có đúng một ô được chọn.",
        matrix_after=[row[:] for row in mat],
        details={
            "selectedCells": [{"row": r, "col": c} for r, c in selected_cells],
        },
    ))

    # ── Tạo assignment_matrix (0/1) ──────────────────────────────────────────
    assignment_matrix = [[0] * n for _ in range(n)]
    for i, j in selected_cells:
        assignment_matrix[i][j] = 1

    # Trim về kích thước gốc
    final_assignment_matrix = [
        assignment_matrix[i][:n_jobs_orig]
        for i in range(n_workers_orig)
    ]

    # ── Tính totalCost / totalProfit từ original matrix ─────────────────────
    total_cost = 0.0
    assignments_list = []

    wnames = worker_names or [f"Người {i+1}" for i in range(n_workers_orig)]
    jnames = job_names or [f"Việc {j+1}" for j in range(n_jobs_orig)]

    # Pad names với dummy
    all_wnames = wnames + [f"Dummy người {k+1}" for k in range(added_dummy_workers)]
    all_jnames = jnames + [f"Dummy việc {k+1}" for k in range(added_dummy_jobs)]

    for i in range(n_workers_orig):
        j = assignment[i]
        if j < n_jobs_orig:
            value = original_matrix[i][j]
            total_cost += value
            assignments_list.append({
                "workerIndex": i,
                "jobIndex": j,
                "workerName": all_wnames[i],
                "jobName": all_jnames[j],
                "value": value,
                "isDummy": False,
            })
        else:
            # Worker thật nhưng được gán vào dummy job
            assignments_list.append({
                "workerIndex": i,
                "jobIndex": j,
                "workerName": all_wnames[i],
                "jobName": all_jnames[j],
                "value": 0.0,
                "isDummy": True,
            })

    total_profit = total_cost if is_maximize else 0.0
    if not is_maximize:
        objective_value = total_cost
    else:
        # totalCost đang là tổng p_ij thực (vì ta tính từ original_matrix)
        objective_value = total_cost  # đây thực ra là profit
        total_profit = total_cost

    return AssignmentResult(
        assignment_matrix=final_assignment_matrix,
        assignments=assignments_list,
        total_cost=total_cost if not is_maximize else 0.0,
        total_profit=total_profit,
        objective_value=objective_value,
        is_maximize=is_maximize,
        original_matrix=original_matrix,
        working_matrix=[row[:n_jobs_orig] for row in mat[:n_workers_orig]],
        n_workers_orig=n_workers_orig,
        n_jobs_orig=n_jobs_orig,
        n_size=n,
        steps=steps,
        added_dummy_workers=added_dummy_workers,
        added_dummy_jobs=added_dummy_jobs,
        p_max=p_max,
    )


# ── Helper Functions ──────────────────────────────────────────────────────────

def _find_assignment(mat: list[list[float]], n: int) -> dict[int, int] | None:
    """
    Tìm gán 1-1 từ zeros. Dùng augmenting path (Kuhn's algorithm).
    Trả None nếu chưa có đủ n zeros độc lập.
    """
    EPS = 1e-9
    match_job: dict[int, int] = {}   # job_idx → worker_idx
    match_worker: dict[int, int] = {}  # worker_idx → job_idx

    def try_augment(worker: int, visited: set) -> bool:
        for job in range(n):
            if mat[worker][job] < EPS and job not in visited:
                visited.add(job)
                if job not in match_job or try_augment(match_job[job], visited):
                    match_job[job] = worker
                    match_worker[worker] = job
                    return True
        return False

    for worker in range(n):
        try_augment(worker, set())

    if len(match_worker) < n:
        return None

    return match_worker  # worker → job


def _min_cover_zeros(mat: list[list[float]], n: int) -> tuple[set[int], set[int]]:
    """
    Tìm số đường tối thiểu che phủ tất cả số 0 (Konig's theorem).
    Trả (row_lines, col_lines).
    """
    EPS = 1e-9

    # Bước 1: Tìm matching tối đa
    match_job: dict[int, int] = {}
    match_worker: dict[int, int] = {}

    def try_augment(worker: int, visited: set) -> bool:
        for job in range(n):
            if mat[worker][job] < EPS and job not in visited:
                visited.add(job)
                if job not in match_job or try_augment(match_job[job], visited):
                    match_job[job] = worker
                    match_worker[worker] = job
                    return True
        return False

    for worker in range(n):
        try_augment(worker, set())

    # Bước 2: Tìm minimum vertex cover qua alternating paths
    matched_workers = set(match_worker.keys())
    unmatched_workers = set(range(n)) - matched_workers

    # BFS/DFS alternating từ unmatched workers
    reachable_workers: set[int] = set()
    reachable_jobs: set[int] = set()
    queue = list(unmatched_workers)

    while queue:
        w = queue.pop()
        reachable_workers.add(w)
        for j in range(n):
            if mat[w][j] < EPS and j not in reachable_jobs:
                reachable_jobs.add(j)
                # Theo matched edge
                if j in match_job:
                    w2 = match_job[j]
                    if w2 not in reachable_workers:
                        queue.append(w2)

    # Minimum vertex cover: matched workers NOT reachable + reachable jobs
    row_lines = matched_workers - reachable_workers
    col_lines = reachable_jobs

    return row_lines, col_lines
