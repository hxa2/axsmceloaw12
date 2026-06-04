"""
backend/core/transformers/inequality_transformer.py
=====================================================
Chuyển bài toán vận tải với ràng buộc bất đẳng thức về bài toán cân bằng.

Mode A (hỗ trợ hiện tại):
  supplyConstraint = "less_or_equal"
  demandConstraint = "equal"

  Σ_j x_ij <= a_i   (nguồn không cần phát hết)
  Σ_i x_ij = b_j    (điểm thu nhận đúng nhu cầu)

  Nếu totalSupply > totalDemand:
    → Thêm destination ảo "Không sử dụng" với demand = totalSupply - totalDemand, cost = 0.
  Nếu totalSupply < totalDemand:
    → Bài toán không khả thi.
"""

from dataclasses import dataclass, field


@dataclass
class InequalityTransformResult:
    """Kết quả transform bài toán bất đẳng thức → cân bằng."""
    transformed_cost_matrix: list[list[float]]
    transformed_supply: list[float]
    transformed_demand: list[float]
    transformed_source_names: list[str]
    transformed_destination_names: list[str]
    added_dummy_destination: bool
    dummy_destination_index: int | None
    dummy_amount: float
    supply_constraint: str
    demand_constraint: str


SUPPORTED_COMBINATIONS = {
    ("less_or_equal", "equal"),
}


def transform_inequality(
    cost_matrix: list[list[float]],
    supply: list[float],
    demand: list[float],
    supply_constraint: str,
    demand_constraint: str,
    source_names: list[str] | None = None,
    destination_names: list[str] | None = None,
) -> InequalityTransformResult:
    """
    Transform bài toán bất đẳng thức thành bài toán vận tải cân bằng.

    Raises:
        NotImplementedError: Nếu tổ hợp ràng buộc chưa được hỗ trợ.
        ValueError: Nếu bài toán không khả thi (tổng cung < tổng cầu ở Mode A).
    """
    combo = (supply_constraint, demand_constraint)
    if combo not in SUPPORTED_COMBINATIONS:
        raise NotImplementedError(
            f"Tổ hợp ràng buộc '{supply_constraint}' / '{demand_constraint}' chưa được hỗ trợ. "
            f"Hiện hỗ trợ: nguồn ≤, cầu =."
        )

    m = len(supply)
    n = len(demand)
    total_supply = sum(supply)
    total_demand = sum(demand)

    src_names = source_names or [f"S{i+1}" for i in range(m)]
    dst_names = destination_names or [f"D{j+1}" for j in range(n)]

    if supply_constraint == "less_or_equal" and demand_constraint == "equal":
        if total_supply < total_demand:
            raise ValueError(
                f"Bài toán không khả thi: tổng cung ({total_supply}) < tổng cầu ({total_demand}). "
                f"Với ràng buộc nguồn ≤ và cầu =, cần tổng cung ≥ tổng cầu."
            )

        if abs(total_supply - total_demand) < 1e-9:
            # Đã cân bằng — không cần thêm dummy
            return InequalityTransformResult(
                transformed_cost_matrix=cost_matrix,
                transformed_supply=supply,
                transformed_demand=demand,
                transformed_source_names=src_names,
                transformed_destination_names=dst_names,
                added_dummy_destination=False,
                dummy_destination_index=None,
                dummy_amount=0.0,
                supply_constraint=supply_constraint,
                demand_constraint=demand_constraint,
            )

        # Thêm dummy destination
        dummy_amount = total_supply - total_demand
        new_demand = demand + [dummy_amount]
        new_cost_matrix = [row + [0.0] for row in cost_matrix]
        new_dst_names = dst_names + ["Không sử dụng"]

        return InequalityTransformResult(
            transformed_cost_matrix=new_cost_matrix,
            transformed_supply=supply,
            transformed_demand=new_demand,
            transformed_source_names=src_names,
            transformed_destination_names=new_dst_names,
            added_dummy_destination=True,
            dummy_destination_index=n,  # index sau cùng
            dummy_amount=dummy_amount,
            supply_constraint=supply_constraint,
            demand_constraint=demand_constraint,
        )

    raise NotImplementedError("Tổ hợp ràng buộc chưa được hỗ trợ.")


def compute_unused_supply_by_source(
    allocation_matrix: list[list[float]],
    dummy_destination_index: int | None,
) -> list[float]:
    """
    Lấy lượng cung không dùng theo từng nguồn (từ cột dummy).
    Nếu không có dummy, trả về mảng toàn 0.
    """
    m = len(allocation_matrix)
    if dummy_destination_index is None:
        return [0.0] * m
    return [allocation_matrix[i][dummy_destination_index] for i in range(m)]
