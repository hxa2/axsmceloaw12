"""
backend/core/transformers/warehouse_transformer.py
====================================================
Chuyển bài toán lập kho nhận hàng thành bài toán vận tải chuẩn.

Mode fixed: kho mới được xem như điểm thu thông thường với nhu cầu cố định.
  warehouseCost_i = costsFromSources[i] + storageCostPerUnit

Mode max_capacity: chưa hỗ trợ.
"""

from dataclasses import dataclass


@dataclass
class WarehouseInfo:
    name: str
    demand_mode: str  # "fixed" | "max_capacity"
    amount: float
    costs_from_sources: list[float]
    storage_cost_per_unit: float = 0.0


@dataclass
class WarehouseTransformResult:
    """Kết quả transform warehouse → destination."""
    transformed_cost_matrix: list[list[float]]
    transformed_supply: list[float]
    transformed_demand: list[float]
    transformed_source_names: list[str]
    transformed_destination_names: list[str]
    warehouse_destination_indices: list[int]   # indices của warehouses trong transformed
    warehouse_specs: list[WarehouseInfo]


def transform_warehouse(
    base_cost_matrix: list[list[float]],
    supply: list[float],
    demand: list[float],
    warehouses: list[WarehouseInfo],
    source_names: list[str] | None = None,
    destination_names: list[str] | None = None,
) -> WarehouseTransformResult:
    """
    Thêm các kho vào bài toán như các điểm thu.

    Args:
        base_cost_matrix: Ma trận chi phí gốc m×n (nguồn → điểm thu hiện tại).
        supply: Vectơ lượng phát.
        demand: Vectơ nhu cầu hiện tại.
        warehouses: Danh sách kho mới.
        source_names: Tên nguồn.
        destination_names: Tên điểm thu hiện tại.

    Raises:
        NotImplementedError: Nếu warehouse dùng mode 'max_capacity'.
        ValueError: Nếu costsFromSources không khớp số nguồn.
    """
    m = len(supply)
    n_orig = len(demand)

    src_names = source_names or [f"S{i+1}" for i in range(m)]
    dst_names = list(destination_names or [f"D{j+1}" for j in range(n_orig)])

    # Validate và build extended matrix
    new_cost_matrix = [row[:] for row in base_cost_matrix]
    new_demand = list(demand)
    warehouse_indices = []

    for wh in warehouses:
        if wh.demand_mode == "max_capacity":
            raise NotImplementedError(
                f"Kho '{wh.name}' dùng mode 'max_capacity' chưa được hỗ trợ. "
                f"Vui lòng dùng mode 'fixed'."
            )

        if len(wh.costs_from_sources) != m:
            raise ValueError(
                f"Kho '{wh.name}': costsFromSources có {len(wh.costs_from_sources)} phần tử, "
                f"nhưng cần {m} (bằng số nguồn)."
            )

        # Chi phí kho = vận chuyển + lưu kho
        warehouse_cost_col = [
            wh.costs_from_sources[i] + wh.storage_cost_per_unit
            for i in range(m)
        ]

        # Thêm cột mới vào từng hàng
        for i in range(m):
            new_cost_matrix[i].append(warehouse_cost_col[i])

        warehouse_idx = n_orig + len(warehouse_indices)
        warehouse_indices.append(warehouse_idx)
        new_demand.append(wh.amount)
        dst_names.append(wh.name)

    return WarehouseTransformResult(
        transformed_cost_matrix=new_cost_matrix,
        transformed_supply=supply,
        transformed_demand=new_demand,
        transformed_source_names=src_names,
        transformed_destination_names=dst_names,
        warehouse_destination_indices=warehouse_indices,
        warehouse_specs=warehouses,
    )


def build_warehouse_interpretation(
    allocation_matrix: list[list[float]],
    warehouse_result: WarehouseTransformResult,
    source_names: list[str],
) -> list[dict]:
    """
    Tạo interpretation cho từng kho: nhận bao nhiêu, từ nguồn nào, cost.
    """
    usages = []
    for idx, wh in enumerate(warehouse_result.warehouse_specs):
        dest_col = warehouse_result.warehouse_destination_indices[idx]
        received_amount = sum(
            allocation_matrix[i][dest_col]
            for i in range(len(allocation_matrix))
        )
        incoming_by_source = []
        for i in range(len(allocation_matrix)):
            amount = allocation_matrix[i][dest_col]
            if amount > 1e-9:
                unit_cost = (
                    wh.costs_from_sources[i] + wh.storage_cost_per_unit
                    if i < len(wh.costs_from_sources)
                    else 0.0
                )
                incoming_by_source.append({
                    "sourceName": source_names[i] if i < len(source_names) else f"S{i+1}",
                    "amount": amount,
                    "unitCost": unit_cost,
                    "totalCost": unit_cost * amount,
                })

        usages.append({
            "name": wh.name,
            "receivedAmount": received_amount,
            "targetAmount": wh.amount,
            "unusedCapacity": max(0.0, wh.amount - received_amount),
            "incomingBySource": incoming_by_source,
        })
    return usages
