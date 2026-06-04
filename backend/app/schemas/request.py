"""
backend/app/schemas/request.py
================================
Pydantic schemas cho request đầu vào.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SolveRequest(BaseModel):
    """Schema cho POST /api/transportation/solve."""

    costMatrix: list[list[float]] = Field(
        ...,
        description="Ma trận cước phí C (m × n)",
        examples=[[[2, 3, 1], [5, 4, 8]]],
    )
    supply: list[float] = Field(
        ...,
        description="Vectơ lượng phát A (m,)",
        examples=[[20, 30]],
    )
    demand: list[float] = Field(
        ...,
        description="Vectơ lượng thu B (n,)",
        examples=[[10, 25, 15]],
    )
    initialMethod: str = Field(
        default="least_cost",
        description="Phương pháp tìm phương án ban đầu",
        examples=["least_cost"],
    )
    optimizationMethod: str = Field(
        default="potential",
        description="Phương pháp tối ưu hóa",
        examples=["potential"],
    )
    sourceNames: Optional[list[str]] = Field(
        default=None,
        description="Tên trạm phát (tuỳ chọn)",
    )
    destinationNames: Optional[list[str]] = Field(
        default=None,
        description="Tên trạm thu (tuỳ chọn)",
    )
    includeIterations: bool = Field(
        default=True,
        description="Có trả về chi tiết từng vòng lặp không",
    )

    @field_validator("initialMethod")
    @classmethod
    def validate_initial_method(cls, v: str) -> str:
        allowed = {"least_cost", "northwest_corner", "vogel"}
        if v not in allowed:
            raise ValueError(
                f"Phương pháp khởi tạo '{v}' không hợp lệ. "
                f"Chỉ chấp nhận: {', '.join(sorted(allowed))}."
            )
        return v

    @field_validator("optimizationMethod")
    @classmethod
    def validate_optimization_method(cls, v: str) -> str:
        allowed = {"potential", "none"}
        if v not in allowed:
            raise ValueError(
                f"Phương pháp tối ưu '{v}' không hợp lệ. "
                f"Chỉ chấp nhận: {', '.join(sorted(allowed))}."
            )
        return v


class FileUploadOptions(BaseModel):
    """Schema cho tùy chọn kèm file upload."""

    initialMethod: str = Field(default="least_cost")
    optimizationMethod: str = Field(default="potential")
    includeIterations: bool = Field(default=True)


# ── Extended Problem Request Schemas ─────────────────────────────────────────

class MaxTransportRequest(BaseModel):
    """POST /api/transportation/max — Bài toán vận tải dạng Max."""
    profitMatrix: list[list[float]] = Field(..., description="Ma trận lợi nhuận P (m × n)")
    supply: list[float] = Field(..., description="Lượng phát (m,)")
    demand: list[float] = Field(..., description="Lượng thu (n,)")
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None
    initialMethod: str = Field(default="least_cost")
    optimizationMethod: str = Field(default="potential")


class ForbiddenCell(BaseModel):
    row: int
    col: int


class ForbiddenCellsRequest(BaseModel):
    """POST /api/transportation/forbidden — Vận tải có ô cấm."""
    costMatrix: list[list[float]] = Field(..., description="Ma trận chi phí gốc")
    supply: list[float]
    demand: list[float]
    forbiddenCells: list[ForbiddenCell] = Field(..., description="Danh sách ô bị cấm")
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None
    initialMethod: str = Field(default="least_cost")
    optimizationMethod: str = Field(default="potential")


class InequalityRequest(BaseModel):
    """POST /api/transportation/inequality — Ràng buộc bất đẳng thức."""
    costMatrix: list[list[float]]
    supply: list[float]
    demand: list[float]
    supplyConstraint: str = Field(
        default="equal",
        description="'equal' hoặc 'less_or_equal'",
    )
    demandConstraint: str = Field(
        default="equal",
        description="'equal', 'greater_or_equal', hoặc 'less_or_equal'",
    )
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None
    initialMethod: str = Field(default="least_cost")
    optimizationMethod: str = Field(default="potential")


class WarehouseSpec(BaseModel):
    """Thông tin một kho nhận hàng mới."""
    name: str
    demandMode: str = Field(default="fixed", description="'fixed' hoặc 'max_capacity'")
    amount: float
    costsFromSources: list[float] = Field(..., description="Chi phí từ từng nguồn đến kho")
    storageCostPerUnit: float = Field(default=0.0)


class WarehouseRequest(BaseModel):
    """POST /api/transportation/warehouse — Lập kho nhận hàng."""
    baseCostMatrix: list[list[float]]
    supply: list[float]
    demand: list[float]
    warehouses: list[WarehouseSpec]
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None
    initialMethod: str = Field(default="least_cost")
    optimizationMethod: str = Field(default="potential")


class AssignmentRequest(BaseModel):
    """POST /api/assignment/solve — Bài toán phân việc (Hungarian)."""
    matrix: list[list[float]] = Field(..., description="Ma trận chi phí / lợi nhuận")
    objective: str = Field(default="minimize", description="'minimize' hoặc 'maximize'")
    workerNames: Optional[list[str]] = None
    jobNames: Optional[list[str]] = None
