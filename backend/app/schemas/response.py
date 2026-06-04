"""
backend/app/schemas/response.py
==================================
Pydantic schemas cho response đầu ra.
"""

from typing import Any, Optional
from pydantic import BaseModel



class IterationResponse(BaseModel):
    """Schema cho một vòng lặp tối ưu."""

    step: int
    allocationMatrix: list[list[float]]
    totalCost: Optional[float] = None
    potentialsU: Optional[list[Optional[float]]] = None
    potentialsV: Optional[list[Optional[float]]] = None
    reducedCosts: Optional[list[list[Optional[float]]]] = None
    enteringCell: Optional[tuple[int, int]] = None
    leavingCell: Optional[tuple[int, int]] = None
    cycle: Optional[list[tuple[int, int]]] = None
    theta: Optional[float] = None
    costDelta: Optional[float] = None
    isOptimal: Optional[bool] = None
    description: str = ""


class SolveResponse(BaseModel):
    """Schema cho response của POST /api/transportation/solve."""

    allocationMatrix: list[list[float]]
    totalCost: float
    isOptimal: bool
    iterations: list[IterationResponse] = []
    message: str = ""
    warnings: list[str] = []
    initialCost: Optional[float] = None
    numIterations: int = 0
    basisCells: list[tuple[int, int]] = []
    costMatrix: Optional[list[list[float]]] = None
    supply: Optional[list[float]] = None
    demand: Optional[list[float]] = None
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None

    # Metadata cân bằng
    isBalancedOriginal: bool = True
    balanceType: str = "none"  # "none" | "dummy_source" | "dummy_destination"
    dummySourceIndex: Optional[int] = None
    dummyDestinationIndex: Optional[int] = None
    originalSupplyTotal: Optional[float] = None
    originalDemandTotal: Optional[float] = None


class MethodInfo(BaseModel):
    """Thông tin một thuật toán."""

    id: str
    name: str
    description: str
    isAvailable: bool = True


class MethodsResponse(BaseModel):
    """Danh sách các thuật toán có thể dùng."""

    initialMethods: list[MethodInfo]
    optimizationMethods: list[MethodInfo]


class SampleProblemResponse(BaseModel):
    """Một bài toán mẫu."""

    name: str
    description: str
    costMatrix: list[list[float]]
    supply: list[float]
    demand: list[float]
    optimalCost: Optional[float] = None
    sourceNames: Optional[list[str]] = None
    destinationNames: Optional[list[str]] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    message: str


# ── Extended Problem Schemas ──────────────────────────────────────────────────

class TransformationInfo(BaseModel):
    """Mô tả một bước biến đổi bài toán."""
    type: str
    description: str
    formula: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class StepInfo(BaseModel):
    """Một bước trong quá trình giải (walkthrough)."""
    type: str
    description: str
    matrixBefore: Optional[list[list[Any]]] = None
    matrixAfter: Optional[list[list[Any]]] = None
    details: Optional[dict[str, Any]] = None


class ExtendedSolveResponse(BaseModel):
    """Schema response chung cho bài toán mở rộng."""
    problemType: str          # "transportation" | "assignment"
    variant: str              # "max_profit" | "forbidden_cells" | "inequality" | "warehouse" | "assignment"

    originalProblem: dict[str, Any]
    transformedProblem: dict[str, Any]
    transformations: list[TransformationInfo] = []

    solution: dict[str, Any]
    interpretation: dict[str, Any] = {}
    steps: list[StepInfo] = []

    warnings: list[str] = []
    isOptimal: bool = True
    isFeasible: bool = True
    infeasibilityReason: Optional[str] = None
