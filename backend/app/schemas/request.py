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
