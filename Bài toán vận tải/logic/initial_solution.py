"""
Module: initial_solution.py
============================
Giai đoạn 1 – Tìm phương án cực biên xuất phát bằng Phương pháp Cực tiểu Chi phí.

Triển khai các thành phần:
  1. BasisSet  – Cấu trúc dữ liệu chuyên biệt quản lý tập ô cơ sở G(x).
  2. least_cost_method() – Thuật toán phân bổ theo cước phí nhỏ nhất.
  3. Các hàm hỗ trợ nội bộ: tìm ô tốt nhất, bổ sung ô suy biến, phát hiện chu trình.

Tính chất bất biến (invariant) của tập cơ sở sau giai đoạn 1:
  - |G(x^0)| = m + n - 1   (đúng số lượng ô cơ sở)
  - G(x^0) không chứa chu trình khép kín (đảm bảo độc lập tuyến tính)
"""

import logging
from collections import defaultdict
from typing import List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Ngưỡng so sánh số thực dấu phẩy động
_EPS = 1e-9


# ===========================================================================
# Cấu trúc dữ liệu: BasisSet
# ===========================================================================

class BasisSet:
    """
    Cấu trúc dữ liệu chuyên biệt lưu trữ và quản lý tập ô cơ sở G(x).

    Tập ô cơ sở là tập hợp các cặp chỉ số (i, j) tương ứng với các biến
    cơ sở (basic variables) trong phương án cực biên hiện tại.

    Bất biến:
        |G(x)| == m + n - 1  (bảo đảm bởi thuật toán, không phải bởi class)

    Lưu trữ nội bộ:
        set[tuple[int, int]] – tra cứu thành viên O(1).
    """

    def __init__(self) -> None:
        # Lưu trữ nội bộ: tập hợp các cặp (i, j)
        self._cells: Set[Tuple[int, int]] = set()

    # ── Ghi / Xóa ─────────────────────────────────────────────────────────

    def add(self, i: int, j: int) -> None:
        """Thêm ô (i, j) vào tập cơ sở."""
        self._cells.add((i, j))

    def remove(self, i: int, j: int) -> None:
        """
        Xóa ô (i, j) khỏi tập cơ sở.
        Không ném ngoại lệ nếu ô không tồn tại (dùng discard).
        """
        self._cells.discard((i, j))

    # ── Truy vấn ──────────────────────────────────────────────────────────

    def __contains__(self, cell: Tuple[int, int]) -> bool:
        """Kiểm tra O(1) xem ô (i, j) có thuộc tập cơ sở không."""
        return cell in self._cells

    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self):
        return iter(self._cells)

    def __repr__(self) -> str:
        return f"BasisSet({sorted(self._cells)})"

    # ── Sao chép và chuyển đổi ────────────────────────────────────────────

    def copy(self) -> "BasisSet":
        """Tạo bản sao độc lập (deep copy) của tập cơ sở."""
        new_basis = BasisSet()
        new_basis._cells = self._cells.copy()
        return new_basis

    def to_set(self) -> Set[Tuple[int, int]]:
        """Trả về bản sao dạng set Python thuần – dùng cho logic ngoài class."""
        return self._cells.copy()

    def to_sorted_list(self) -> List[Tuple[int, int]]:
        """Trả về danh sách sắp xếp theo (i, j) – để hiển thị nhất quán."""
        return sorted(self._cells)

    # ── Truy vấn theo hàng / cột ──────────────────────────────────────────

    def get_row_cells(self, i: int) -> List[Tuple[int, int]]:
        """Trả về danh sách ô cơ sở thuộc hàng i."""
        return [(r, c) for (r, c) in self._cells if r == i]

    def get_col_cells(self, j: int) -> List[Tuple[int, int]]:
        """Trả về danh sách ô cơ sở thuộc cột j."""
        return [(r, c) for (r, c) in self._cells if c == j]

    def frozen(self) -> frozenset:
        """Trả về frozenset – dùng làm khóa trong dict/set để phát hiện cycling."""
        return frozenset(self._cells)


# ===========================================================================
# Hàm công khai chính: Phương pháp Cực tiểu Chi phí
# ===========================================================================

def least_cost_method(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
) -> Tuple[np.ndarray, "BasisSet"]:
    """
    Tìm phương án cực biên xuất phát x^0 bằng Phương pháp Cực tiểu Chi phí.

    Thuật toán:
        Bước 1.1 – Tìm ô (i0, j0) có c_ij nhỏ nhất trong phần bảng chưa xóa.
        Bước 1.2 – Phân phối x_{i0,j0} = min(a_{i0}, b_{j0}).
        Bước 1.3 – Cập nhật và thu hẹp bảng (xóa hàng hoặc cột).
                   Trường hợp suy biến (a_{i0} = b_{j0}): chỉ xóa cột.
        Bước 1.4 – Lặp lại đến khi phân phối hết.

    Parameters
    ----------
    C : np.ndarray, shape (m, n)   Ma trận cước phí.
    A : np.ndarray, shape (m,)     Vectơ lượng phát.
    B : np.ndarray, shape (n,)     Vectơ lượng thu.

    Returns
    -------
    X      : np.ndarray, shape (m, n)   Ma trận phương án cực biên x^0.
    basis  : BasisSet                   Tập ô cơ sở ban đầu G(x^0).

    Raises
    ------
    RuntimeError  Nếu không thể hoàn chỉnh tập cơ sở m+n-1 ô.
    """
    m, n = C.shape

    # Ma trận phân phối hàng hóa (khởi tạo = 0)
    X = np.zeros((m, n), dtype=float)

    # Bản sao của vectơ cung/cầu – sẽ bị cập nhật dần trong quá trình phân bổ
    supply = A.astype(float).copy()   # Trữ lượng còn lại của từng trạm phát
    demand = B.astype(float).copy()   # Nhu cầu còn lại của từng trạm thu

    # Tập ô cơ sở – được xây dựng tăng dần
    basis = BasisSet()

    # Theo dõi hàng và cột đã bị loại khỏi bảng đang xét
    deleted_rows: Set[int] = set()
    deleted_cols: Set[int] = set()

    step = 0

    logger.info("=" * 64)
    logger.info("GIAI ĐOẠN 1: PHƯƠNG ÁN CỰC BIÊN – CỰC TIỂU CHI PHÍ")
    logger.info("=" * 64)

    # ── Vòng lặp chính – phân bổ từng ô ────────────────────────────────
    while True:
        # Kiểm tra điều kiện dừng: tất cả hàng hoặc tất cả cột đã xóa
        active_rows = [i for i in range(m) if i not in deleted_rows]
        active_cols = [j for j in range(n) if j not in deleted_cols]

        if not active_rows or not active_cols:
            break

        # Kiểm tra nếu toàn bộ cung/cầu còn lại đều ≈ 0
        remaining = sum(supply[i] for i in active_rows)
        if remaining < _EPS:
            break

        step += 1

        # ── Bước 1.1: Tìm ô (i0, j0) có cước phí nhỏ nhất ─────────────
        min_cost, candidate_cells = _find_min_cost_cells(
            C, deleted_rows, deleted_cols, m, n
        )

        if not candidate_cells:
            break   # Không còn ô nào khả dụng

        # ── Chọn ô tốt nhất từ các ứng viên cùng cước phí nhỏ nhất ─────
        #    Ưu tiên: (1) phân phối được khối lượng lớn nhất,
        #             (2) nếu bằng nhau → chỉ số (i, j) nhỏ nhất
        i0, j0 = _select_best_candidate(candidate_cells, supply, demand)

        # ── Bước 1.2: Phân phối lượng hàng tối đa vào ô (i0, j0) ───────
        allocation = min(supply[i0], demand[j0])
        X[i0, j0] = allocation
        basis.add(i0, j0)

        logger.info(
            f"Bước {step:>2d}: Chọn ô ({i0+1},{j0+1}) | "
            f"c={C[i0,j0]:.4g} | x={allocation:.4g} | "
            f"a_{i0+1}={supply[i0]:.4g} | b_{j0+1}={demand[j0]:.4g}"
        )

        # ── Bước 1.3: Cập nhật cung/cầu và thu hẹp bảng ─────────────────
        supply[i0] -= allocation
        demand[j0] -= allocation

        # Chuẩn hóa giá trị gần 0 tránh lỗi dấu phẩy động
        if abs(supply[i0]) < _EPS:
            supply[i0] = 0.0
        if abs(demand[j0]) < _EPS:
            demand[j0] = 0.0

        supply_zero = supply[i0] == 0.0
        demand_zero = demand[j0] == 0.0

        if supply_zero and demand_zero:
            # Trường hợp suy biến: a_{i0} = b_{j0}
            # Quy ước: chỉ xóa cột j0, giữ hàng i0 với trữ lượng 0
            # → đảm bảo thuật toán có thể thêm ô suy biến sau nếu cần
            deleted_cols.add(j0)
            logger.info(
                f"         SUY BIẾN (a=b): Xóa COT {j0+1}, "
                f"giữ HANG {i0+1} (tru luong = 0)"
            )
        elif supply_zero:
            # Hàng i0 đã phân phối hết → xóa hàng
            deleted_rows.add(i0)
            logger.info(f"         Xoa HANG {i0+1} (tru luong vet sach)")
        else:
            # Cột j0 đã đáp ứng đủ nhu cầu → xóa cột
            deleted_cols.add(j0)
            logger.info(f"         Xoa COT {j0+1} (nhu cau da dap ung)")

    # ── Kiểm tra và bổ sung ô suy biến nếu số ô cơ sở chưa đủ ──────────
    required = m + n - 1
    if len(basis) < required:
        deficit = required - len(basis)
        logger.warning(
            f"So o co so = {len(basis)} < {required} (m+n-1). "
            f"Can bo sung {deficit} o suy bien."
        )
        basis = _supplement_degenerate_cells(basis, X, m, n, required)

    # ── Ghi log kết quả giai đoạn 1 ──────────────────────────────────────
    initial_cost = float(np.sum(C * X))
    logger.info(f"\nTap o co so G(x^0): {basis.to_sorted_list()}")
    logger.info(f"So o co so: {len(basis)} = m+n-1 = {required}")
    logger.info(f"Chi phi ban dau f(x^0) = {initial_cost:.6g}")

    return X, basis


# ===========================================================================
# Hàm công khai: Phương pháp Góc Tây Bắc (Northwest Corner Method)
# ===========================================================================

def northwest_corner_method(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
) -> Tuple[np.ndarray, "BasisSet"]:
    """
    Tìm phương án cực biên xuất phát x^0 bằng Phương pháp Góc Tây Bắc.

    Thuật toán:
        Bước 1.1 – Chọn ô ở góc Tây Bắc hiện tại (hàng nhỏ nhất, cột nhỏ nhất
                   chưa bị xóa, ban đầu là ô (1,1)).
        Bước 1.2 – Phân phối x_{ij} = min(a_i, b_j).
        Bước 1.3 – Cập nhật lượng thu phát và thu hẹp bảng:
                   - Nếu a_i < b_j: Xóa hàng i, cập nhật b_j' = b_j - a_i.
                   - Nếu b_j < a_i: Xóa cột j, cập nhật a_i' = a_i - b_j.
                   - Nếu a_i = b_j: Chỉ xóa cột j, giữ hàng i với a_i' = 0.
        Bước 1.4 – Lặp lại từ Bước 1.1 cho đến khi hết.

    Parameters
    ----------
    C : np.ndarray, shape (m, n)   Ma trận cước phí.
    A : np.ndarray, shape (m,)     Vectơ lượng phát.
    B : np.ndarray, shape (n,)     Vectơ lượng thu.

    Returns
    -------
    X      : np.ndarray, shape (m, n)   Ma trận phương án cực biên x^0.
    basis  : BasisSet                   Tập ô cơ sở ban đầu G(x^0).

    Raises
    ------
    RuntimeError  Nếu không thể hoàn chỉnh tập cơ sở m+n-1 ô.
    """
    m, n = C.shape

    # Ma trận phân phối hàng hóa (khởi tạo = 0)
    X = np.zeros((m, n), dtype=float)

    # Bản sao của vectơ cung/cầu – sẽ bị cập nhật dần
    supply = A.astype(float).copy()
    demand = B.astype(float).copy()

    # Tập ô cơ sở
    basis = BasisSet()

    # Theo dõi hàng và cột đã bị loại
    deleted_rows: Set[int] = set()
    deleted_cols: Set[int] = set()

    step = 0

    logger.info("=" * 64)
    logger.info("GIAI ĐOẠN 1: PHƯƠNG ÁN CỰC BIÊN – GÓC TÂY BẮC")
    logger.info("=" * 64)

    # ── Vòng lặp chính ──────────────────────────────────────────────────
    while True:
        # Tìm hàng và cột chưa xóa nhỏ nhất (góc Tây Bắc)
        active_rows = [i for i in range(m) if i not in deleted_rows]
        active_cols = [j for j in range(n) if j not in deleted_cols]

        if not active_rows or not active_cols:
            break

        # Kiểm tra cung còn lại
        remaining = sum(supply[i] for i in active_rows)
        if remaining < _EPS:
            break

        step += 1

        # Bước 1.1: Chọn ô góc Tây Bắc (hàng nhỏ nhất, cột nhỏ nhất)
        i0 = active_rows[0]
        j0 = active_cols[0]

        # Bước 1.2: Phân phối lượng hàng tối đa
        allocation = min(supply[i0], demand[j0])
        X[i0, j0] = allocation
        basis.add(i0, j0)

        logger.info(
            f"Bước {step:>2d}: Chọn ô ({i0+1},{j0+1}) [Góc Tây Bắc] | "
            f"c={C[i0,j0]:.4g} | x={allocation:.4g} | "
            f"a_{i0+1}={supply[i0]:.4g} | b_{j0+1}={demand[j0]:.4g}"
        )

        # Bước 1.3: Cập nhật cung/cầu
        supply[i0] -= allocation
        demand[j0] -= allocation

        # Chuẩn hóa giá trị gần 0
        if abs(supply[i0]) < _EPS:
            supply[i0] = 0.0
        if abs(demand[j0]) < _EPS:
            demand[j0] = 0.0

        supply_zero = supply[i0] == 0.0
        demand_zero = demand[j0] == 0.0

        if supply_zero and demand_zero:
            # Suy biến (a_i = b_j): chỉ xóa cột, giữ hàng với trữ lượng 0
            deleted_cols.add(j0)
            logger.info(
                f"         SUY BIẾN (a=b): Xóa CỘT {j0+1}, "
                f"giữ HÀNG {i0+1} (trữ lượng = 0)"
            )
        elif supply_zero:
            # Hàng i0 hết hàng → xóa hàng
            deleted_rows.add(i0)
            logger.info(f"         Xóa HÀNG {i0+1} (trữ lượng vét sạch)")
        else:
            # Cột j0 đáp ứng đủ → xóa cột
            deleted_cols.add(j0)
            logger.info(f"         Xóa CỘT {j0+1} (nhu cầu đã đáp ứng)")

    # ── Kiểm tra và bổ sung ô suy biến nếu cần ─────────────────────────
    required = m + n - 1
    if len(basis) < required:
        deficit = required - len(basis)
        logger.warning(
            f"Số ô cơ sở = {len(basis)} < {required} (m+n-1). "
            f"Cần bổ sung {deficit} ô suy biến."
        )
        basis = _supplement_degenerate_cells(basis, X, m, n, required)

    # ── Ghi log kết quả giai đoạn 1 ─────────────────────────────────────
    initial_cost = float(np.sum(C * X))
    logger.info(f"\nTập ô cơ sở G(x^0): {basis.to_sorted_list()}")
    logger.info(f"Số ô cơ sở: {len(basis)} = m+n-1 = {required}")
    logger.info(f"Chi phí ban đầu f(x^0) = {initial_cost:.6g}")

    return X, basis


# ===========================================================================
# Các hàm hỗ trợ nội bộ
# ===========================================================================

def _find_min_cost_cells(
    C: np.ndarray,
    deleted_rows: Set[int],
    deleted_cols: Set[int],
    m: int,
    n: int,
) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Quét phần bảng chưa xóa, tìm tất cả ô có cước phí nhỏ nhất.

    Returns
    -------
    min_cost   : float                 Giá trị cước phí nhỏ nhất.
    candidates : list of (i, j)        Danh sách ô đạt min_cost.
    """
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
                # Tìm được ô nhỏ hơn → cập nhật danh sách
                min_cost = cij
                candidates = [(i, j)]
            elif abs(cij - min_cost) <= _EPS:
                # Bằng giá trị nhỏ nhất hiện tại → bổ sung
                candidates.append((i, j))

    return min_cost, candidates


def _select_best_candidate(
    candidates: List[Tuple[int, int]],
    supply: np.ndarray,
    demand: np.ndarray,
) -> Tuple[int, int]:
    """
    Chọn ô tốt nhất từ danh sách các ô cùng cước phí nhỏ nhất.

    Tiêu chí ưu tiên (theo thứ tự):
        1. Khả năng phân phối lớn nhất: max min(a_i, b_j)
        2. Nếu bằng nhau → chỉ số (i, j) nhỏ nhất (lexicographic)

    Returns
    -------
    (i, j) : tuple  Ô được chọn.
    """
    best_cell: Optional[Tuple[int, int]] = None
    best_alloc = -1.0

    for (i, j) in candidates:
        alloc = min(supply[i], demand[j])
        if alloc > best_alloc + _EPS:
            best_alloc = alloc
            best_cell = (i, j)
        elif abs(alloc - best_alloc) <= _EPS:
            # Tie-break: chọn chỉ số lexicographic nhỏ hơn
            if best_cell is None or (i, j) < best_cell:
                best_cell = (i, j)

    return best_cell  # type: ignore[return-value]


def _supplement_degenerate_cells(
    basis: "BasisSet",
    X: np.ndarray,
    m: int,
    n: int,
    target: int,
) -> "BasisSet":
    """
    Bổ sung ô suy biến (x_ij = 0) vào tập cơ sở cho đến khi đủ m+n-1 ô.

    Được gọi khi nhiều bước phân bổ cùng triệt tiêu cả cung lẫn cầu,
    khiến số ô cơ sở ít hơn m+n-1 (hiện tượng suy biến).

    Chiến lược: Thêm ô (i, j) chưa thuộc basis, theo thứ tự lexicographic,
    sao cho sau khi thêm tập cơ sở vẫn không chứa chu trình.

    Parameters
    ----------
    basis  : BasisSet   Tập cơ sở hiện tại (có thể thiếu ô).
    X      : np.ndarray Ma trận phương án (sẽ gán 0 vào ô bổ sung).
    m, n   : int        Kích thước bài toán.
    target : int        Số ô cơ sở mục tiêu (= m + n - 1).

    Returns
    -------
    basis : BasisSet    Tập cơ sở đã bổ sung đủ ô.

    Raises
    ------
    RuntimeError  Nếu không thể tìm đủ ô để bổ sung.
    """
    added = 0
    needed = target - len(basis)

    for i in range(m):
        if added >= needed:
            break
        for j in range(n):
            if added >= needed:
                break
            if (i, j) in basis:
                continue

            # Thử thêm ô này vào tập cơ sở tạm thời
            basis.add(i, j)
            X[i, j] = 0.0

            # Kiểm tra nếu tạo ra chu trình → bỏ qua, thử ô khác
            if _has_cycle_in_basis(basis, m):
                basis.remove(i, j)
                X[i, j] = 0.0
            else:
                added += 1
                logger.warning(
                    f"  Bo sung o suy bien ({i+1},{j+1}) voi x=0 vao tap co so."
                )

    if len(basis) < target:
        raise RuntimeError(
            f"Khong the hoan chinh tap co so: "
            f"can {target} o nhung chi tim duoc {len(basis)} o."
        )

    return basis


def _has_cycle_in_basis(basis: "BasisSet", m: int) -> bool:
    """
    Kiểm tra tập cơ sở có tạo chu trình trên đồ thị lưỡng phân không.

    Nếu có chu trình → tập ô cơ sở không hợp lệ (hệ vectơ hàng/cột
    không độc lập tuyến tính → không giải được hệ phương trình thế vị).

    Đồ thị lưỡng phân:
        - Node hàng:  id = i           (i = 0..m-1)
        - Node cột:   id = m + j       (j = 0..n-1)
        - Cạnh (i,j): nối node i với node m+j

    Thuật toán: DFS trên đồ thị vô hướng – phát hiện chu trình qua back edge.

    Returns
    -------
    bool  True nếu tồn tại chu trình, False nếu không.
    """
    # Xây dựng danh sách kề (undirected)
    adj: dict = defaultdict(set)
    for (i, j) in basis:
        row_node = i
        col_node = m + j
        adj[row_node].add(col_node)
        adj[col_node].add(row_node)

    visited: Set[int] = set()

    def dfs(node: int, parent: int) -> bool:
        """DFS từ node, parent là node đến từ (để không đi ngược cạnh cũ)."""
        visited.add(node)
        for neighbor in adj[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                # Back edge → có chu trình
                return True
        return False

    # Lấy tất cả node xuất hiện trong đồ thị
    all_nodes: Set[int] = set()
    for (i, j) in basis:
        all_nodes.add(i)
        all_nodes.add(m + j)

    for node in all_nodes:
        if node not in visited:
            if dfs(node, -1):
                return True

    return False
