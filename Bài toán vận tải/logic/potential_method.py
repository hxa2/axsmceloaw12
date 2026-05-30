"""
Module: potential_method.py
============================
Giai đoạn 2 – Thuật toán Thế vị (Potential Method) tối ưu hóa phương án vận tải.

Các thành phần chính (theo thứ tự bước thuật toán):
  ┌──────────────────────────────────────────────────────────────────┐
  │ compute_potentials()  – Bước 2.1: Tính u_i, v_j qua BFS        │
  │ compute_deltas()      – Bước 2.2: Tính Δ_ij = u_i+v_j−c_ij    │
  │ find_pivot_cells()    – Bước 2.3: Tìm ô vào (max Δ > 0)        │
  │ find_cycle_dfs()      – Bước 2.4.2: Tìm chu trình bằng DFS     │
  │ adjust_flow()         – Bước 2.4.3–5: Điều chỉnh luồng + cơ sở│
  │ optimize()            – Vòng lặp chính tích hợp tất cả bước     │
  └──────────────────────────────────────────────────────────────────┘

Xử lý suy biến (θ = 0):
  - Phát hiện và ghi log cảnh báo.
  - Tiếp tục pivot (ô vào thay ô ra dù không di chuyển hàng hóa).
  - Phát hiện cycling bằng lịch sử frozenset tập cơ sở.
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from logic.initial_solution import BasisSet

logger = logging.getLogger(__name__)

# Ngưỡng so sánh số thực dấu phẩy động
_EPS = 1e-9


# ===========================================================================
# Bước 2.1 – Tính hệ thế vị u_i và v_j
# ===========================================================================

def compute_potentials(
    C: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Giải hệ phương trình thế vị:
        u_i + v_j = c_ij   với mọi (i, j) ∈ G(x^0)

    Phương pháp: Lan truyền BFS trên đồ thị lưỡng phân của tập cơ sở.
    Điều kiện neo: u_0 = 0 (gán cố định để hệ có nghiệm duy nhất).

    Đồ thị lưỡng phân:
        - Node hàng (row node): đại diện cho u_i
        - Node cột (col node):  đại diện cho v_j
        - Cạnh (i,j):           kết nối row node i với col node j

    Parameters
    ----------
    C     : np.ndarray, shape (m, n)   Ma trận cước phí.
    basis : BasisSet                   Tập ô cơ sở hiện tại.
    m, n  : int                        Số trạm phát / thu.

    Returns
    -------
    u : np.ndarray, shape (m,)   Thế vị hàng.
    v : np.ndarray, shape (n,)   Thế vị cột.

    Raises
    ------
    ValueError  Nếu tập cơ sở không liên thông (không tính được đủ thế vị).
    """
    # Khởi tạo thế vị bằng NaN – sẽ được điền dần qua BFS
    u = np.full(m, np.nan)
    v = np.full(n, np.nan)
    u[0] = 0.0   # Neo: u_1 = 0

    # Xây dựng danh sách kề từ tập ô cơ sở
    # row_to_cols[i] = danh sách j sao cho (i,j) ∈ basis
    # col_to_rows[j] = danh sách i sao cho (i,j) ∈ basis
    row_to_cols: Dict[int, List[int]] = defaultdict(list)
    col_to_rows: Dict[int, List[int]] = defaultdict(list)
    for (i, j) in basis:
        row_to_cols[i].append(j)
        col_to_rows[j].append(i)

    # BFS: lan truyền từ u_0 đã biết sang các thế vị lân cận
    # Mỗi phần tử queue: ('row', i) hoặc ('col', j)
    queue: deque = deque()
    queue.append(('row', 0))

    while queue:
        node_type, idx = queue.popleft()

        if node_type == 'row':
            # Từ u_i đã biết → tính v_j = c_ij - u_i
            i = idx
            for j in row_to_cols[i]:
                if np.isnan(v[j]):
                    v[j] = C[i, j] - u[i]
                    queue.append(('col', j))
        else:
            # Từ v_j đã biết → tính u_i = c_ij - v_j
            j = idx
            for i in col_to_rows[j]:
                if np.isnan(u[i]):
                    u[i] = C[i, j] - v[j]
                    queue.append(('row', i))

    # Kiểm tra xem tất cả thế vị đã được tính chưa
    missing_u = [i + 1 for i in range(m) if np.isnan(u[i])]
    missing_v = [j + 1 for j in range(n) if np.isnan(v[j])]
    if missing_u or missing_v:
        raise ValueError(
            f"Tap co so khong lien thong – khong tinh duoc the vi: "
            f"u chua tinh tai hang {missing_u}, "
            f"v chua tinh tai cot {missing_v}. "
            f"Kiem tra lai tap co so: {basis}"
        )

    return u, v


# ===========================================================================
# Bước 2.2 – Tính ma trận ước lượng Δ_ij
# ===========================================================================

def compute_deltas(
    C: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> np.ndarray:
    """
    Tính chỉ số ước lượng cho toàn bộ ô loại (ô không thuộc tập cơ sở):
        Δ_ij = u_i + v_j - c_ij

    Ô cơ sở được gán NaN để phân biệt trong ma trận kết quả.

    Parameters
    ----------
    C, u, v : np.ndarray   Ma trận cước phí và hai vectơ thế vị.
    basis   : BasisSet     Tập ô cơ sở hiện tại.
    m, n    : int

    Returns
    -------
    Delta : np.ndarray, shape (m, n)
        Ma trận ước lượng (NaN tại vị trí ô cơ sở).
    """
    Delta = np.full((m, n), np.nan)

    for i in range(m):
        for j in range(n):
            if (i, j) not in basis:
                # Chỉ tính cho ô loại
                Delta[i, j] = u[i] + v[j] - C[i, j]

    return Delta


# ===========================================================================
# Bước 2.3 – Kiểm tra tính tối ưu và tìm ô vào (pivot cell)
# ===========================================================================

def find_pivot_cells(
    Delta: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> Tuple[Optional[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Tìm ô điều chỉnh (ô vào) có Δ_ij lớn nhất dương.

    Tiêu chí tối ưu: Nếu Δ_ij ≤ 0 với mọi ô loại → phương án đã tối ưu.

    Khi có nhiều ô đồng giá trị Δ_max:
        - Tất cả ô đồng giá trị được ghi vào log (traceability).
        - Ô được chọn là ô có chỉ số lexicographic nhỏ nhất (i nhỏ nhất, rồi j).

    Parameters
    ----------
    Delta  : np.ndarray   Ma trận ước lượng (từ compute_deltas).
    basis  : BasisSet     Tập cơ sở hiện tại.
    m, n   : int

    Returns
    -------
    pivot    : tuple(i,j) hoặc None
        Ô được chọn làm ô vào. None nếu phương án đã tối ưu.
    all_tied : list of tuple(i,j)
        Toàn bộ ô có cùng Δ_max > 0 (kể cả pivot).
    """
    max_delta = _EPS   # Chỉ xét Δ > 0 (dương thực sự)
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
                # Tìm được Δ lớn hơn → cập nhật
                max_delta = delta
                pivot = (i, j)
                all_tied = [(i, j)]

            elif delta > _EPS and abs(delta - max_delta) <= _EPS:
                # Bằng Δ_max hiện tại → thêm vào danh sách đồng giá trị
                all_tied.append((i, j))

    return pivot, all_tied


# ===========================================================================
# Bước 2.4.2 – Tìm chu trình điều chỉnh bằng DFS
# ===========================================================================

def find_cycle_dfs(
    entering_cell: Tuple[int, int],
    basis: BasisSet,
) -> Optional[List[Tuple[int, int]]]:
    """
    Tìm chu trình điều chỉnh khép kín duy nhất qua ô vào bằng DFS.

    Định nghĩa chu trình trong bảng vận tải:
        Dãy ô (e, c_1, c_2, ..., c_{2k-1}) thỏa:
          - e = entering_cell  (ô vào, ký hiệu '+')
          - Các ô c_1..c_{2k-1} ∈ G(x^0)  (ô cơ sở)
          - Liên tiếp nhau theo hàng hoặc cột, xen kẽ: H → V → H → V → ...
          - Ô cuối c_{2k-1} có thể di chuyển về e để đóng chu trình.
          - Độ dài chu trình là số chẵn (≥ 4).

    Thuật toán DFS:
        1. Xây dựng row_map và col_map từ G(x^0) ∪ {entering_cell}.
        2. Bắt đầu DFS từ entering_cell, bước đầu tiên di chuyển theo hàng (H).
        3. Tại mỗi bước, xen kẽ hướng di chuyển H ↔ V.
        4. Điều kiện đóng chu trình: tìm được ứng viên = entering_cell
           và len(path) ≥ 3 (đảm bảo ít nhất 4 ô trong chu trình).

    Parameters
    ----------
    entering_cell : (i_s, j_s)  Ô vào (không thuộc basis).
    basis         : BasisSet    Tập ô cơ sở G(x^0).

    Returns
    -------
    cycle : list of (i, j)
        Danh sách ô theo thứ tự chu trình, bắt đầu bằng entering_cell.
        Ô cuối ngầm nối trở lại entering_cell (đóng chu trình).
        None nếu không tìm được chu trình (lỗi tập cơ sở).
    """
    i_s, j_s = entering_cell
    basis_set: Set[Tuple[int, int]] = basis.to_set()

    # ── Xây dựng bản đồ hàng/cột từ G(x^0) ∪ {entering_cell} ───────────
    # row_map[i] = danh sách các cột j có ô trong tập này
    # col_map[j] = danh sách các hàng i có ô trong tập này
    row_map: Dict[int, List[int]] = defaultdict(list)
    col_map: Dict[int, List[int]] = defaultdict(list)

    all_cells: Set[Tuple[int, int]] = basis_set | {entering_cell}
    for (i, j) in all_cells:
        row_map[i].append(j)
        col_map[j].append(i)

    # ── DFS đệ quy tìm chu trình ─────────────────────────────────────────
    def dfs(
        path: List[Tuple[int, int]],
        direction: str,   # 'h' = di chuyển ngang, 'v' = di chuyển dọc
    ) -> Optional[List[Tuple[int, int]]]:
        """
        DFS tìm đường đi từ path[-1] quay về entering_cell.

        Parameters
        ----------
        path      : Đường đi hiện tại (path[0] = entering_cell).
        direction : Hướng bước tiếp theo ('h' hoặc 'v').

        Returns
        -------
        Danh sách ô của chu trình hoàn chỉnh, hoặc None nếu không tìm được.
        """
        curr_i, curr_j = path[-1]
        next_dir = 'v' if direction == 'h' else 'h'

        if direction == 'h':
            # Bước ngang: tìm ô cùng hàng curr_i, cột khác curr_j
            candidate_cells = [
                (curr_i, j) for j in row_map[curr_i] if j != curr_j
            ]
        else:
            # Bước dọc: tìm ô cùng cột curr_j, hàng khác curr_i
            candidate_cells = [
                (i, curr_j) for i in col_map[curr_j] if i != curr_i
            ]

        for candidate in candidate_cells:

            # ── Điều kiện đóng chu trình ──────────────────────────────────
            # Tìm được đường trở về entering_cell với đủ độ dài (≥ 4 ô)
            if candidate == entering_cell and len(path) >= 3:
                return path   # Chu trình hoàn chỉnh: path[0..] → path[0]

            # ── Điều kiện tiếp tục đi ────────────────────────────────────
            # Chỉ đi vào ô cơ sở chưa được thăm trong lần đi này
            # path[1:] vì path[0] = entering_cell (cho phép đóng về đó)
            if candidate in basis_set and candidate not in path[1:]:
                result = dfs(path + [candidate], next_dir)
                if result is not None:
                    return result

        return None   # Không tìm được từ hướng đi này

    # ── Khởi động DFS từ entering_cell, bước đầu tiên theo hàng ─────────
    cycle = dfs([entering_cell], 'h')
    return cycle


# ===========================================================================
# Bước 2.4.3–5 – Điều chỉnh luồng theo chu trình và cập nhật cơ sở
# ===========================================================================

def adjust_flow(
    X: np.ndarray,
    cycle: List[Tuple[int, int]],
    basis: BasisSet,
) -> Tuple[np.ndarray, "BasisSet", Tuple[int, int], Tuple[int, int], float]:
    """
    Thực hiện điều chỉnh luồng hàng hóa dọc theo chu trình K.

    Quy tắc đánh dấu dấu (+) / (-):
        cycle[0]  = entering_cell → dấu (+)
        cycle[1]                  → dấu (-)
        cycle[2]                  → dấu (+)
        ...   (xen kẽ theo chỉ số chẵn/lẻ)

    Công thức điều chỉnh:
        θ = min { x_ij | (i,j) ∈ K⁻ }       (lượng hàng điều chỉnh)
        x_ij ← x_ij + θ  với (i,j) ∈ K⁺     (ô dấu +)
        x_ij ← x_ij − θ  với (i,j) ∈ K⁻     (ô dấu -)

    Cập nhật tập cơ sở:
        - Ô ra (leaving cell): ô dấu (−) đạt giá trị x_ij = θ, chỉ số nhỏ nhất.
        - Ô vào (entering cell) = cycle[0]: thêm vào tập cơ sở.
        - Ô ra: xóa khỏi tập cơ sở.

    Xử lý suy biến (θ = 0):
        Ghi cảnh báo nhưng vẫn tiếp tục pivot (ô vào/ra thay đổi dù x không đổi).

    Parameters
    ----------
    X     : np.ndarray   Ma trận phương án hiện tại.
    cycle : list         Chu trình điều chỉnh (từ find_cycle_dfs).
    basis : BasisSet     Tập cơ sở hiện tại.

    Returns
    -------
    X_new        : np.ndarray         Ma trận phương án sau điều chỉnh.
    basis_new    : BasisSet           Tập cơ sở sau cập nhật.
    entering_cell: tuple(i,j)         Ô vào (cycle[0]).
    leaving_cell : tuple(i,j)         Ô ra.
    theta        : float              Lượng hàng điều chỉnh θ.
    """
    entering_cell = cycle[0]

    # ── Phân loại ô theo dấu ─────────────────────────────────────────────
    # Chỉ số chẵn (0, 2, 4, ...) → dấu (+)
    # Chỉ số lẻ  (1, 3, 5, ...) → dấu (-)
    plus_cells  = [cycle[k] for k in range(0, len(cycle), 2)]
    minus_cells = [cycle[k] for k in range(1, len(cycle), 2)]

    # ── Tính θ = min lượng hàng tại các ô dấu (−) ────────────────────────
    theta_candidates = [(X[i, j], (i, j)) for (i, j) in minus_cells]
    theta, leaving_cell = min(theta_candidates, key=lambda t: (t[0], t[1]))

    # ── Xử lý trường hợp suy biến (θ ≈ 0) ───────────────────────────────
    if theta < _EPS:
        logger.warning(
            f"[SUY BIEN] theta = {theta:.2e} ~ 0. "
            f"O vao: ({entering_cell[0]+1},{entering_cell[1]+1}), "
            f"O ra: ({leaving_cell[0]+1},{leaving_cell[1]+1}). "
            f"Pivot suy bien duoc thuc hien de thay doi tap co so."
        )

    # ── Điều chỉnh luồng trên chu trình ─────────────────────────────────
    X_new = X.copy()

    for (i, j) in plus_cells:
        X_new[i, j] += theta

    for (i, j) in minus_cells:
        X_new[i, j] -= theta
        # Làm tròn giá trị cực nhỏ về 0 (tránh -1e-15 do dấu phẩy động)
        if abs(X_new[i, j]) < _EPS:
            X_new[i, j] = 0.0

    # ── Cập nhật tập cơ sở ───────────────────────────────────────────────
    basis_new = basis.copy()
    basis_new.add(*entering_cell)    # Thêm ô vào
    basis_new.remove(*leaving_cell)  # Xóa ô ra

    return X_new, basis_new, entering_cell, leaving_cell, theta


# ===========================================================================
# Vòng lặp chính – optimize()
# ===========================================================================

def optimize(
    C: np.ndarray,
    X_init: np.ndarray,
    basis_init: BasisSet,
    A: np.ndarray,
    B: np.ndarray,
    max_iterations: int = 1000,
) -> Tuple[np.ndarray, "BasisSet", float, int]:
    """
    Vòng lặp chính của Thuật toán Thế vị.

    Lặp lại các bước 2.1 → 2.2 → 2.3 → 2.4 cho đến khi:
        (a) Tất cả Δ_ij ≤ 0  → phương án tối ưu toàn cục.
        (b) Đạt max_iterations → dừng với cảnh báo (phòng cycling).

    Phát hiện cycling:
        Lưu frozenset của mỗi tập cơ sở đã gặp. Nếu lặp lại → cảnh báo.
        (Với bài toán không suy biến, cycling không thể xảy ra.)

    Parameters
    ----------
    C           : np.ndarray   Ma trận cước phí.
    X_init      : np.ndarray   Phương án cực biên xuất phát (từ giai đoạn 1).
    basis_init  : BasisSet     Tập cơ sở ban đầu G(x^0).
    A, B        : np.ndarray   Vectơ lượng phát và lượng thu.
    max_iterations : int       Giới hạn vòng lặp (bảo vệ khi suy biến).

    Returns
    -------
    X_opt      : np.ndarray   Ma trận phương án tối ưu X*.
    basis_opt  : BasisSet     Tập cơ sở tối ưu G(X*).
    cost_opt   : float        Tổng chi phí tối ưu f(X*).
    iterations : int          Số vòng lặp đã thực hiện.

    Raises
    ------
    RuntimeError  Nếu không tìm được chu trình (lỗi tập cơ sở).
    """
    m, n = C.shape
    X = X_init.copy()
    basis = basis_init.copy()

    # Lịch sử frozenset tập cơ sở – dùng để phát hiện cycling
    seen_bases: Set[frozenset] = set()
    seen_bases.add(basis.frozen())

    logger.info("\n" + "=" * 64)
    logger.info("GIAI ĐOAN 2: THUAT TOAN THE VI – TOI UU HOA")
    logger.info("=" * 64)
    logger.info(f"Chi phi ban dau f(x^0) = {np.sum(C * X):.6g}")

    for iteration in range(1, max_iterations + 1):

        logger.info(f"\n{'─' * 64}")
        logger.info(f"VONG LAP #{iteration}")
        logger.info(f"{'─' * 64}")

        # ── Bước 2.1: Tính hệ thế vị ─────────────────────────────────────
        u, v = compute_potentials(C, basis, m, n)

        logger.info(
            "The vi hang  u = [" +
            ", ".join(f"{x:+.4g}" for x in u) + "]"
        )
        logger.info(
            "The vi cot   v = [" +
            ", ".join(f"{x:+.4g}" for x in v) + "]"
        )

        # ── Bước 2.2: Tính ma trận Δ ─────────────────────────────────────
        Delta = compute_deltas(C, u, v, basis, m, n)
        _log_delta_matrix(Delta, basis, m, n)

        # ── Bước 2.3: Kiểm tra tính tối ưu ───────────────────────────────
        pivot, all_tied = find_pivot_cells(Delta, basis, m, n)

        if pivot is None:
            # Tất cả Δ_ij ≤ 0 → tối ưu
            cost_opt = float(np.sum(C * X))
            logger.info(
                f"\n>>> PHUONG AN TOI UU SAU {iteration - 1} VONG LAP <<<\n"
                f"    Tong chi phi toi uu: f(X*) = {cost_opt:.6g}"
            )
            return X, basis, cost_opt, iteration - 1

        # ── Ghi log ô vào (và các ô đồng Δ nếu có) ───────────────────────
        _log_pivot_selection(pivot, all_tied, Delta)

        # ── Bước 2.4.2: Tìm chu trình qua ô vào bằng DFS ─────────────────
        cycle = find_cycle_dfs(pivot, basis)

        if cycle is None:
            raise RuntimeError(
                f"Khong tim duoc chu trinh qua o vao "
                f"({pivot[0]+1},{pivot[1]+1}). "
                f"Tap co so co the bi loi: {basis}"
            )

        # Ghi log chu trình chính
        logger.info("Chu trinh chinh:")
        _log_cycle_detail(cycle, X, Delta)

        # Nếu có ô đồng Δ: ghi log các chu trình thay thế để tham khảo
        if len(all_tied) > 1:
            logger.info(f"  [{len(all_tied) - 1} chu trinh thay the (cac o dong Delta):]")
            for alt_cell in all_tied[1:]:
                alt_cycle = find_cycle_dfs(alt_cell, basis)
                prefix = f"  [O ({alt_cell[0]+1},{alt_cell[1]+1})]"
                if alt_cycle is not None:
                    _log_cycle_detail(alt_cycle, X, Delta, prefix=prefix)
                else:
                    logger.info(f"{prefix} Khong tim duoc chu trinh.")

        # ── Bước 2.4.3–5: Điều chỉnh luồng ──────────────────────────────
        X_new, basis_new, entering, leaving, theta = adjust_flow(X, cycle, basis)

        new_cost = float(np.sum(C * X_new))
        delta_cost = new_cost - float(np.sum(C * X))

        logger.info(
            f"theta = {theta:.6g} | "
            f"O VAO → ({entering[0]+1},{entering[1]+1}) | "
            f"O RA  → ({leaving[0]+1},{leaving[1]+1}) | "
            f"Chi phi moi = {new_cost:.6g} "
            f"(thay doi {delta_cost:+.6g})"
        )

        # ── Phát hiện cycling ─────────────────────────────────────────────
        basis_key = basis_new.frozen()
        if basis_key in seen_bases:
            logger.warning(
                f"[CANH BAO CYCLING] Tap co so da xuat hien truoc do "
                f"tai vong lap {iteration}. Co the bi cycling do suy bien. "
                f"Nen ap dung phuong phap nhieu loan (perturbation) neu can."
            )
        seen_bases.add(basis_key)

        X = X_new
        basis = basis_new

    # ── Hết giới hạn vòng lặp ────────────────────────────────────────────
    cost_final = float(np.sum(C * X))
    logger.warning(
        f"[CANH BAO] Dat gioi han {max_iterations} vong lap. "
        f"Chi phi cuoi: {cost_final:.6g}. "
        f"Phuong an co the chua toi uu – tang max_iterations neu can."
    )
    return X, basis, cost_final, max_iterations


# ===========================================================================
# Các hàm hỗ trợ logging nội bộ
# ===========================================================================

def _log_delta_matrix(
    Delta: np.ndarray,
    basis: BasisSet,
    m: int,
    n: int,
) -> None:
    """Ghi log ma trận Δ theo dạng bảng dễ đọc."""
    logger.info("Ma tran uoc luong Delta (--- = o co so):")
    # Header hàng
    header = "         " + "".join(f"  T{j+1:>3}" for j in range(n))
    logger.info(header)
    logger.info("         " + "─" * (6 * n))

    for i in range(m):
        row_parts = []
        for j in range(n):
            if (i, j) in basis:
                row_parts.append("  [---]")
            else:
                d = Delta[i, j]
                # Đánh dấu ô có Δ > 0 bằng dấu *
                marker = "*" if d > _EPS else " "
                row_parts.append(f"{d:+7.3f}{marker}")
        logger.info(f"  Hang {i+1}: " + "  ".join(row_parts))


def _log_pivot_selection(
    pivot: Tuple[int, int],
    all_tied: List[Tuple[int, int]],
    Delta: np.ndarray,
) -> None:
    """Ghi log ô vào được chọn và các ô đồng Δ (nếu có)."""
    delta_val = Delta[pivot]
    if len(all_tied) > 1:
        logger.info(
            f"[DONG GIA TRI] Co {len(all_tied)} o cung Delta_max = {delta_val:.6g}:"
        )
        for cell in all_tied:
            marker = " ← CHON" if cell == pivot else ""
            logger.info(
                f"  O ({cell[0]+1},{cell[1]+1}) | Delta = {Delta[cell]:.6g}{marker}"
            )
        logger.info(
            f"  → Chon o ({pivot[0]+1},{pivot[1]+1}) "
            f"(chi so lexicographic nho nhat)"
        )
    else:
        logger.info(
            f"O vao: ({pivot[0]+1},{pivot[1]+1}) | "
            f"Delta = {delta_val:.6g}  (lon nhat duong)"
        )


def _log_cycle_detail(
    cycle: List[Tuple[int, int]],
    X: np.ndarray,
    Delta: np.ndarray,
    prefix: str = "  ",
) -> None:
    """
    Ghi log chi tiết một chu trình: dấu +/−, lượng hàng, và giá trị θ.

    Format mỗi ô trong chu trình:
        (hang, cot)[+/-| x=<gia_tri>]
    """
    # Dấu: chỉ số chẵn → '+', chỉ số lẻ → '−'
    signs = ['+' if k % 2 == 0 else '-' for k in range(len(cycle))]

    # Xây dựng chuỗi hiển thị chu trình
    parts = []
    for k, (r, c) in enumerate(cycle):
        parts.append(f"({r+1},{c+1})[{signs[k]}|x={X[r,c]:.4g}]")
    cycle_str = " → ".join(parts) + " → (dong)"
    logger.info(f"{prefix}  {cycle_str}")

    # Xác định θ và ô ra
    minus_vals = [
        (X[r, c], (r, c))
        for k, (r, c) in enumerate(cycle)
        if signs[k] == '-'
    ]
    if minus_vals:
        theta_val, leaving = min(minus_vals, key=lambda t: (t[0], t[1]))
        logger.info(
            f"{prefix}  theta = min{{...}} = {theta_val:.4g} | "
            f"O ra = ({leaving[0]+1},{leaving[1]+1})"
        )
