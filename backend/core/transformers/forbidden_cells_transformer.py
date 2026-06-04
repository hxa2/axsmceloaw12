"""
backend/core/transformers/forbidden_cells_transformer.py
==========================================================
Xử lý bài toán vận tải có ô cấm bằng phương pháp Big-M.

Với mỗi ô cấm (i, j): c_ij = M (rất lớn)
M = max(c_ij) * totalSupply * 1000 (hoặc ít nhất 1_000_000)
"""

from dataclasses import dataclass, field

BIG_M_DEFAULT = 1_000_000_000.0


@dataclass
class ForbiddenCellInfo:
    row: int
    col: int


@dataclass
class ForbiddenCellsResult:
    """Kết quả transform ô cấm → Big-M."""
    transformed_cost_matrix: list[list[float]]
    big_m_value: float
    forbidden_cells: list[ForbiddenCellInfo]


def transform_forbidden_cells(
    cost_matrix: list[list[float]],
    supply: list[float],
    forbidden_cells: list[ForbiddenCellInfo],
) -> ForbiddenCellsResult:
    """
    Thay các ô cấm bằng Big-M.

    Args:
        cost_matrix: Ma trận chi phí gốc m×n.
        supply: Vectơ lượng phát.
        forbidden_cells: Danh sách ô cấm.

    Returns:
        ForbiddenCellsResult với ma trận đã thay thế và giá trị M.
    """
    if not cost_matrix or not cost_matrix[0]:
        raise ValueError("Ma trận chi phí không được rỗng.")

    m = len(cost_matrix)
    n = len(cost_matrix[0])

    # Validate forbidden cells nằm trong ma trận
    for fc in forbidden_cells:
        if not (0 <= fc.row < m and 0 <= fc.col < n):
            raise ValueError(
                f"Ô cấm ({fc.row}, {fc.col}) nằm ngoài ma trận {m}×{n}."
            )

    # Tính M đủ lớn
    max_cost = max((v for row in cost_matrix for v in row), default=1.0)
    total_supply = sum(supply)
    big_m = max(max_cost * total_supply * 1000, BIG_M_DEFAULT)

    # Tạo ma trận đã transform
    transformed = [row[:] for row in cost_matrix]  # deep copy
    forbidden_set = {(fc.row, fc.col) for fc in forbidden_cells}
    for i in range(m):
        for j in range(n):
            if (i, j) in forbidden_set:
                transformed[i][j] = big_m

    return ForbiddenCellsResult(
        transformed_cost_matrix=transformed,
        big_m_value=big_m,
        forbidden_cells=forbidden_cells,
    )


def check_forbidden_cell_usage(
    allocation_matrix: list[list[float]],
    forbidden_cells: list[ForbiddenCellInfo],
    tolerance: float = 1e-6,
) -> list[dict]:
    """
    Kiểm tra xem ô cấm nào có allocation dương.

    Returns: list[dict] với {row, col, amount, valid}
    """
    results = []
    for fc in forbidden_cells:
        amount = allocation_matrix[fc.row][fc.col]
        results.append({
            "row": fc.row,
            "col": fc.col,
            "amount": amount,
            "valid": amount <= tolerance,
        })
    return results
