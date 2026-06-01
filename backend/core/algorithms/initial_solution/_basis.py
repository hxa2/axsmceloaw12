"""
backend/core/algorithms/initial_solution/_basis.py
=====================================================
Cấu trúc dữ liệu BasisSet – dùng chung giữa các thuật toán initial solution
và potential method.

Không phụ thuộc framework nào.
"""

from collections import defaultdict
from typing import Dict, List, Set, Tuple


_EPS = 1e-9


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
        self._cells: Set[Tuple[int, int]] = set()

    # ── Ghi / Xóa ─────────────────────────────────────────────────────────

    def add(self, i: int, j: int) -> None:
        """Thêm ô (i, j) vào tập cơ sở."""
        self._cells.add((i, j))

    def remove(self, i: int, j: int) -> None:
        """Xóa ô (i, j) khỏi tập cơ sở (không lỗi nếu không tồn tại)."""
        self._cells.discard((i, j))

    # ── Truy vấn ──────────────────────────────────────────────────────────

    def __contains__(self, cell: Tuple[int, int]) -> bool:
        return cell in self._cells

    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self):
        return iter(self._cells)

    def __repr__(self) -> str:
        return f"BasisSet({sorted(self._cells)})"

    # ── Sao chép và chuyển đổi ────────────────────────────────────────────

    def copy(self) -> "BasisSet":
        new = BasisSet()
        new._cells = self._cells.copy()
        return new

    def to_set(self) -> Set[Tuple[int, int]]:
        return self._cells.copy()

    def to_sorted_list(self) -> List[Tuple[int, int]]:
        return sorted(self._cells)

    # ── Truy vấn theo hàng / cột ──────────────────────────────────────────

    def get_row_cells(self, i: int) -> List[Tuple[int, int]]:
        return [(r, c) for (r, c) in self._cells if r == i]

    def get_col_cells(self, j: int) -> List[Tuple[int, int]]:
        return [(r, c) for (r, c) in self._cells if c == j]

    def frozen(self) -> frozenset:
        return frozenset(self._cells)


def has_cycle_in_basis(basis: BasisSet, m: int) -> bool:
    """
    Kiểm tra tập cơ sở có tạo chu trình trên đồ thị lưỡng phân không.

    Returns True nếu có chu trình (tập cơ sở không hợp lệ).
    """
    adj: Dict[int, Set[int]] = defaultdict(set)
    for (i, j) in basis:
        row_node = i
        col_node = m + j
        adj[row_node].add(col_node)
        adj[col_node].add(row_node)

    visited: Set[int] = set()

    def dfs(node: int, parent: int) -> bool:
        visited.add(node)
        for neighbor in adj[node]:
            if neighbor not in visited:
                if dfs(neighbor, node):
                    return True
            elif neighbor != parent:
                return True
        return False

    all_nodes: Set[int] = set()
    for (i, j) in basis:
        all_nodes.add(i)
        all_nodes.add(m + j)

    for node in all_nodes:
        if node not in visited:
            if dfs(node, -1):
                return True
    return False


def supplement_degenerate_cells(
    basis: BasisSet,
    X: "np.ndarray",  # type: ignore[name-defined]
    m: int,
    n: int,
    target: int,
) -> BasisSet:
    """
    Bổ sung ô suy biến (x_ij = 0) vào tập cơ sở cho đến khi đủ m+n-1 ô.

    Raises RuntimeError nếu không thể hoàn chỉnh.
    """
    import numpy as np

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

            basis.add(i, j)
            X[i, j] = 0.0

            if has_cycle_in_basis(basis, m):
                basis.remove(i, j)
                X[i, j] = 0.0
            else:
                added += 1

    if len(basis) < target:
        raise RuntimeError(
            f"Không thể hoàn chỉnh tập cơ sở: cần {target} ô nhưng chỉ tìm được {len(basis)} ô."
        )
    return basis
