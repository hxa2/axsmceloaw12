"""
backend/core/transformers/max_to_min_transformer.py
======================================================
Chuyển bài toán vận tải dạng tối đa lợi nhuận thành bài toán tối thiểu chi phí.

Công thức: c'_ij = P_max - p_ij
"""

from dataclasses import dataclass


@dataclass
class MaxToMinResult:
    """Kết quả transform bài toán Max → Min."""
    transformed_cost_matrix: list[list[float]]
    p_max: float
    original_profit_matrix: list[list[float]]


def transform_max_to_min(profit_matrix: list[list[float]]) -> MaxToMinResult:
    """
    Chuyển ma trận lợi nhuận p_ij thành ma trận chi phí quy đổi c'_ij.

    c'_ij = P_max - p_ij, với P_max = max(p_ij) trên toàn ma trận.

    Args:
        profit_matrix: Ma trận lợi nhuận kích thước m×n.

    Returns:
        MaxToMinResult chứa transformed_cost_matrix và P_max.
    """
    if not profit_matrix or not profit_matrix[0]:
        raise ValueError("Ma trận lợi nhuận không được rỗng.")

    p_max = max(v for row in profit_matrix for v in row)

    transformed = [
        [p_max - profit_matrix[i][j] for j in range(len(profit_matrix[i]))]
        for i in range(len(profit_matrix))
    ]

    return MaxToMinResult(
        transformed_cost_matrix=transformed,
        p_max=p_max,
        original_profit_matrix=profit_matrix,
    )


def compute_total_profit(
    profit_matrix: list[list[float]],
    allocation_matrix: list[list[float]],
) -> float:
    """
    Tính tổng lợi nhuận thực từ profit_matrix gốc và allocation.

    Z = Σ_i Σ_j p_ij * x_ij
    """
    total = 0.0
    for i, row in enumerate(allocation_matrix):
        for j, alloc in enumerate(row):
            total += profit_matrix[i][j] * alloc
    return total
