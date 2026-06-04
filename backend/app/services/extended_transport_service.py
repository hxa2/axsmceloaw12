"""
backend/app/services/extended_transport_service.py
====================================================
Service điều phối các bài toán vận tải mở rộng.

Tái sử dụng solver vận tải hiện tại thông qua SolverService.
"""

import logging
from fastapi import HTTPException, status

from backend.app.schemas.request import (
    MaxTransportRequest,
    ForbiddenCellsRequest,
    ForbiddenCell,
    InequalityRequest,
    WarehouseRequest,
    SolveRequest,
)
from backend.app.schemas.response import ExtendedSolveResponse, TransformationInfo, StepInfo
from backend.app.services.solver_service import SolverService
from backend.core.transformers.max_to_min_transformer import (
    transform_max_to_min,
    compute_total_profit,
)
from backend.core.transformers.forbidden_cells_transformer import (
    ForbiddenCellInfo,
    transform_forbidden_cells,
    check_forbidden_cell_usage,
)
from backend.core.transformers.inequality_transformer import (
    transform_inequality,
    compute_unused_supply_by_source,
)
from backend.core.transformers.warehouse_transformer import (
    WarehouseInfo,
    transform_warehouse,
    build_warehouse_interpretation,
)

logger = logging.getLogger(__name__)

_solver = SolverService()


# ── Max Transportation ────────────────────────────────────────────────────────

def solve_max_transportation(req: MaxTransportRequest) -> ExtendedSolveResponse:
    """Giải bài toán vận tải dạng Max."""

    # 1. Transform
    transform_result = transform_max_to_min(req.profitMatrix)

    # 2. Dùng SolverService hiện tại
    solve_req = SolveRequest(
        costMatrix=transform_result.transformed_cost_matrix,
        supply=req.supply,
        demand=req.demand,
        sourceNames=req.sourceNames,
        destinationNames=req.destinationNames,
        initialMethod=req.initialMethod,
        optimizationMethod=req.optimizationMethod,
        includeIterations=True,
    )
    base_response = _solver.solve(solve_req)

    # 3. Tính lại totalProfit từ profitMatrix gốc
    total_profit = compute_total_profit(
        req.profitMatrix,
        base_response.allocationMatrix,
    )
    transformed_total_cost = base_response.totalCost

    m = len(req.supply)
    n = len(req.demand)
    src_names = req.sourceNames or [f"S{i+1}" for i in range(m)]
    dst_names = req.destinationNames or [f"D{j+1}" for j in range(n)]

    # 4. Build steps từ iterations
    steps = _build_transport_steps(base_response)

    return ExtendedSolveResponse(
        problemType="transportation",
        variant="max_profit",
        originalProblem={
            "profitMatrix": req.profitMatrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": src_names,
            "destinationNames": dst_names,
        },
        transformedProblem={
            "costMatrix": transform_result.transformed_cost_matrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": src_names,
            "destinationNames": dst_names,
        },
        transformations=[
            TransformationInfo(
                type="max_to_min",
                description="Chuyển bài toán tối đa lợi nhuận thành tối thiểu chi phí quy đổi.",
                formula="c'_ij = P_max - p_ij",
                details={
                    "pMax": transform_result.p_max,
                    "transformedCostMatrix": transform_result.transformed_cost_matrix,
                },
            )
        ],
        solution={
            "allocationMatrix": base_response.allocationMatrix,
            "totalProfit": total_profit,
            "transformedTotalCost": transformed_total_cost,
            "objectiveValue": total_profit,
            "isOptimal": base_response.isOptimal,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "supply": req.supply,
            "demand": req.demand,
        },
        interpretation={
            "note": f"Tổng lợi nhuận tối đa = {total_profit}. Tổng chi phí quy đổi = {transformed_total_cost} (chỉ để tham khảo).",
        },
        steps=steps,
        isOptimal=base_response.isOptimal,
    )


# ── Forbidden Cells ───────────────────────────────────────────────────────────

def solve_forbidden_cells(req: ForbiddenCellsRequest) -> ExtendedSolveResponse:
    """Giải bài toán vận tải có ô cấm bằng Big-M."""

    forbidden = [ForbiddenCellInfo(row=fc.row, col=fc.col) for fc in req.forbiddenCells]

    # 1. Transform
    transform_result = transform_forbidden_cells(
        req.costMatrix,
        req.supply,
        forbidden,
    )

    # 2. Solve
    solve_req = SolveRequest(
        costMatrix=transform_result.transformed_cost_matrix,
        supply=req.supply,
        demand=req.demand,
        sourceNames=req.sourceNames,
        destinationNames=req.destinationNames,
        initialMethod=req.initialMethod,
        optimizationMethod=req.optimizationMethod,
        includeIterations=True,
    )
    base_response = _solver.solve(solve_req)

    # 3. Kiểm tra ô cấm
    usage_check = check_forbidden_cell_usage(base_response.allocationMatrix, forbidden)
    is_feasible = all(u["valid"] for u in usage_check)

    warnings = []
    if not is_feasible:
        warnings.append(
            "Nghiệm có allocation dương tại ô cấm. Bài toán có thể không khả thi hoặc Big-M chưa đủ lớn."
        )

    m = len(req.supply)
    n = len(req.demand)
    src_names = req.sourceNames or [f"S{i+1}" for i in range(m)]
    dst_names = req.destinationNames or [f"D{j+1}" for j in range(n)]

    # Render Big-M as "M" trong transformed matrix display
    big_m_display = transform_result.big_m_value
    steps = _build_transport_steps(base_response)

    return ExtendedSolveResponse(
        problemType="transportation",
        variant="forbidden_cells",
        originalProblem={
            "costMatrix": req.costMatrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "forbiddenCells": [{"row": fc.row, "col": fc.col} for fc in forbidden],
        },
        transformedProblem={
            "costMatrix": transform_result.transformed_cost_matrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "bigMValue": big_m_display,
            "forbiddenCells": [{"row": fc.row, "col": fc.col} for fc in forbidden],
        },
        transformations=[
            TransformationInfo(
                type="forbidden_cells_big_m",
                description=f"Thay các ô cấm bằng chi phí M rất lớn (M = {big_m_display:.0f}) để thuật toán tránh chọn.",
                formula="c_ij = M  với ô cấm (i,j)",
                details={
                    "bigMValue": big_m_display,
                    "cells": [{"row": fc.row, "col": fc.col} for fc in forbidden],
                },
            )
        ],
        solution={
            "allocationMatrix": base_response.allocationMatrix,
            "totalCost": base_response.totalCost,
            "objectiveValue": base_response.totalCost,
            "isOptimal": base_response.isOptimal,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "supply": req.supply,
            "demand": req.demand,
        },
        interpretation={
            "forbiddenCellUsage": usage_check,
            "isFeasibleRespectingForbiddenCells": is_feasible,
        },
        steps=steps,
        warnings=warnings,
        isOptimal=base_response.isOptimal,
        isFeasible=is_feasible,
    )


# ── Inequality Constraints ────────────────────────────────────────────────────

def solve_inequality(req: InequalityRequest) -> ExtendedSolveResponse:
    """Giải bài toán vận tải với ràng buộc bất đẳng thức."""

    # 1. Transform
    try:
        transform_result = transform_inequality(
            cost_matrix=req.costMatrix,
            supply=req.supply,
            demand=req.demand,
            supply_constraint=req.supplyConstraint,
            demand_constraint=req.demandConstraint,
            source_names=req.sourceNames,
            destination_names=req.destinationNames,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Solve
    solve_req = SolveRequest(
        costMatrix=transform_result.transformed_cost_matrix,
        supply=transform_result.transformed_supply,
        demand=transform_result.transformed_demand,
        sourceNames=transform_result.transformed_source_names,
        destinationNames=transform_result.transformed_destination_names,
        initialMethod=req.initialMethod,
        optimizationMethod=req.optimizationMethod,
        includeIterations=True,
    )
    base_response = _solver.solve(solve_req)

    # 3. Interpret
    unused_supply = compute_unused_supply_by_source(
        base_response.allocationMatrix,
        transform_result.dummy_destination_index,
    )

    m = len(req.supply)
    n = len(req.demand)
    src_names = transform_result.transformed_source_names
    dst_names = transform_result.transformed_destination_names

    transformations = []
    if transform_result.added_dummy_destination:
        transformations.append(TransformationInfo(
            type="inequality_to_balanced",
            description=f"Thêm cột 'Không sử dụng' với nhu cầu {transform_result.dummy_amount} để cân bằng bài toán.",
            formula="Σ_j x_ij ≤ a_i  →  thêm D_dummy có b_dummy = Σa_i - Σb_j",
            details={
                "addedDummyDestination": True,
                "dummyAmount": transform_result.dummy_amount,
                "dummyDestinationIndex": transform_result.dummy_destination_index,
            },
        ))

    steps = _build_transport_steps(base_response)

    return ExtendedSolveResponse(
        problemType="transportation",
        variant="inequality_constraints",
        originalProblem={
            "costMatrix": req.costMatrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": req.sourceNames or [f"S{i+1}" for i in range(m)],
            "destinationNames": req.destinationNames or [f"D{j+1}" for j in range(n)],
            "supplyConstraint": req.supplyConstraint,
            "demandConstraint": req.demandConstraint,
        },
        transformedProblem={
            "costMatrix": transform_result.transformed_cost_matrix,
            "supply": transform_result.transformed_supply,
            "demand": transform_result.transformed_demand,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "dummyDestinationIndex": transform_result.dummy_destination_index,
        },
        transformations=transformations,
        solution={
            "allocationMatrix": base_response.allocationMatrix,
            "totalCost": base_response.totalCost,
            "objectiveValue": base_response.totalCost,
            "isOptimal": base_response.isOptimal,
            "sourceNames": src_names,
            "destinationNames": dst_names,
            "supply": transform_result.transformed_supply,
            "demand": transform_result.transformed_demand,
        },
        interpretation={
            "unusedSupplyBySource": [
                {"sourceName": src_names[i], "unusedAmount": unused_supply[i]}
                for i in range(m)
            ],
            "dummyDestinationIndex": transform_result.dummy_destination_index,
        },
        steps=steps,
        isOptimal=base_response.isOptimal,
    )


# ── Warehouse Receiving ───────────────────────────────────────────────────────

def solve_warehouse(req: WarehouseRequest) -> ExtendedSolveResponse:
    """Giải bài toán lập kho nhận hàng."""

    warehouses = [
        WarehouseInfo(
            name=w.name,
            demand_mode=w.demandMode,
            amount=w.amount,
            costs_from_sources=w.costsFromSources,
            storage_cost_per_unit=w.storageCostPerUnit,
        )
        for w in req.warehouses
    ]

    # 1. Transform
    try:
        transform_result = transform_warehouse(
            base_cost_matrix=req.baseCostMatrix,
            supply=req.supply,
            demand=req.demand,
            warehouses=warehouses,
            source_names=req.sourceNames,
            destination_names=req.destinationNames,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Solve
    solve_req = SolveRequest(
        costMatrix=transform_result.transformed_cost_matrix,
        supply=transform_result.transformed_supply,
        demand=transform_result.transformed_demand,
        sourceNames=transform_result.transformed_source_names,
        destinationNames=transform_result.transformed_destination_names,
        initialMethod=req.initialMethod,
        optimizationMethod=req.optimizationMethod,
        includeIterations=True,
    )
    base_response = _solver.solve(solve_req)

    # 3. Interpret
    src_names = transform_result.transformed_source_names
    warehouse_usage = build_warehouse_interpretation(
        base_response.allocationMatrix,
        transform_result,
        src_names,
    )

    transformations = [
        TransformationInfo(
            type="add_warehouse_as_destination",
            description=f"Kho '{wh.name}' được thêm vào như điểm thu với nhu cầu {wh.amount}.",
            formula="warehouseCost_i = transportCost_i + storageCostPerUnit",
            details={
                "warehouseName": wh.name,
                "demandMode": wh.demand_mode,
                "amount": wh.amount,
                "storageCostPerUnit": wh.storage_cost_per_unit,
                "destinationIndex": transform_result.warehouse_destination_indices[idx],
            },
        )
        for idx, wh in enumerate(warehouses)
    ]

    steps = _build_transport_steps(base_response)
    m = len(req.supply)
    n = len(req.demand)

    return ExtendedSolveResponse(
        problemType="transportation",
        variant="warehouse_receiving",
        originalProblem={
            "baseCostMatrix": req.baseCostMatrix,
            "supply": req.supply,
            "demand": req.demand,
            "sourceNames": req.sourceNames or [f"S{i+1}" for i in range(m)],
            "destinationNames": req.destinationNames or [f"D{j+1}" for j in range(n)],
            "warehouses": [
                {
                    "name": w.name,
                    "demandMode": w.demand_mode,
                    "amount": w.amount,
                    "costsFromSources": w.costs_from_sources,
                    "storageCostPerUnit": w.storage_cost_per_unit,
                }
                for w in warehouses
            ],
        },
        transformedProblem={
            "costMatrix": transform_result.transformed_cost_matrix,
            "supply": transform_result.transformed_supply,
            "demand": transform_result.transformed_demand,
            "sourceNames": transform_result.transformed_source_names,
            "destinationNames": transform_result.transformed_destination_names,
            "warehouseDestinationIndices": transform_result.warehouse_destination_indices,
        },
        transformations=transformations,
        solution={
            "allocationMatrix": base_response.allocationMatrix,
            "totalCost": base_response.totalCost,
            "objectiveValue": base_response.totalCost,
            "isOptimal": base_response.isOptimal,
            "sourceNames": transform_result.transformed_source_names,
            "destinationNames": transform_result.transformed_destination_names,
            "supply": transform_result.transformed_supply,
            "demand": transform_result.transformed_demand,
        },
        interpretation={
            "warehouseUsage": warehouse_usage,
            "warehouseDestinationIndices": transform_result.warehouse_destination_indices,
            "nOriginalDestinations": n,
        },
        steps=steps,
        isOptimal=base_response.isOptimal,
    )


# ── Shared helper ─────────────────────────────────────────────────────────────

def _build_transport_steps(base_response) -> list[StepInfo]:
    """Chuyển iterations của solver cơ bản thành StepInfo cho extended response."""
    steps = []
    for it in (base_response.iterations or []):
        steps.append(StepInfo(
            type="iteration",
            description=it.description or f"Bước {it.step}",
            matrixBefore=None,
            matrixAfter=it.allocationMatrix,
            details={
                "step": it.step,
                "totalCost": it.totalCost,
                "potentialsU": it.potentialsU,
                "potentialsV": it.potentialsV,
                "reducedCosts": it.reducedCosts,
                "enteringCell": it.enteringCell,
                "leavingCell": it.leavingCell,
                "cycle": it.cycle,
            },
        ))
    return steps
