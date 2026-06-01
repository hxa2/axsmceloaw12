"""
backend/app/schemas/response.py
==================================
Pydantic schemas cho response đầu ra.
"""

from typing import Optional
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
