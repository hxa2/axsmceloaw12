"""
backend/core/models/solution.py
===================================
Mô hình dữ liệu thuần cho lời giải bài toán vận tải.

Bao gồm:
  - IterationResult: kết quả từng bước lặp của thuật toán tối ưu.
  - TransportationSolution: lời giải cuối cùng (có thể gồm nhiều iteration).

Không phụ thuộc framework nào. Serialize được sang JSON.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IterationResult:
    """
    Kết quả một bước lặp trong quá trình tối ưu hóa.

    Attributes
    ----------
    step : int
        Số thứ tự bước (0 = phương án khởi tạo, 1, 2, ... = các vòng lặp tối ưu).
    allocation_matrix : list[list[float]]
        Ma trận phân phối X tại bước này.
    total_cost : float | None
        Tổng chi phí tại bước này. None nếu chưa tính.
    potentials_u : list[float | None] | None
        Thế vị hàng u_i. None nếu là bước khởi tạo.
    potentials_v : list[float | None] | None
        Thế vị cột v_j. None nếu là bước khởi tạo.
    reduced_costs : list[list[float | None]] | None
        Ma trận ước lượng Δ_ij. None tại ô cơ sở.
    entering_cell : tuple[int, int] | None
        Ô vào (pivot) nếu có.
    leaving_cell : tuple[int, int] | None
        Ô ra nếu có.
    cycle : list[tuple[int, int]] | None
        Chu trình điều chỉnh nếu có.
    description : str
        Mô tả ngắn bước này (dùng để hiển thị).
    """

    step: int
    allocation_matrix: list[list[float]]
    total_cost: Optional[float] = None
    potentials_u: Optional[list[Optional[float]]] = None
    potentials_v: Optional[list[Optional[float]]] = None
    reduced_costs: Optional[list[list[Optional[float]]]] = None
    entering_cell: Optional[tuple[int, int]] = None
    leaving_cell: Optional[tuple[int, int]] = None
    cycle: Optional[list[tuple[int, int]]] = None
    theta: Optional[float] = None
    cost_delta: Optional[float] = None
    is_optimal: Optional[bool] = None
    description: str = ""

    def to_dict(self) -> dict:
        """Serialize sang dict Python thuần (JSON-compatible)."""
        return {
            "step": self.step,
            "allocationMatrix": self.allocation_matrix,
            "totalCost": self.total_cost,
            "potentialsU": self.potentials_u,
            "potentialsV": self.potentials_v,
            "reducedCosts": self.reduced_costs,
            "enteringCell": list(self.entering_cell) if self.entering_cell else None,
            "leavingCell": list(self.leaving_cell) if self.leaving_cell else None,
            "cycle": [list(c) for c in self.cycle] if self.cycle else None,
            "theta": self.theta,
            "costDelta": self.cost_delta,
            "isOptimal": self.is_optimal,
            "description": self.description,
        }


@dataclass
class TransportationSolution:
    """
    Lời giải bài toán vận tải (sau khi chạy xong).

    Attributes
    ----------
    allocation_matrix : list[list[float]]
        Ma trận phân phối X* tối ưu (m × n).
    total_cost : float
        Tổng chi phí tối ưu f(X*).
    is_optimal : bool
        True nếu lời giải đã đạt tối ưu.
    iterations : list[IterationResult]
        Danh sách từng bước lặp (có thể rỗng).
    message : str
        Thông báo tóm tắt.
    warnings : list[str]
        Danh sách cảnh báo (vd: suy biến, cân bằng giả).
    initial_cost : float | None
        Chi phí phương án khởi tạo (trước khi tối ưu hóa).
    num_iterations : int
        Số vòng lặp tối ưu đã thực hiện.
    basis_cells : list[tuple[int, int]]
        Danh sách ô cơ sở trong lời giải tối ưu.
    """

    allocation_matrix: list[list[float]]
    total_cost: float
    is_optimal: bool
    iterations: list[IterationResult] = field(default_factory=list)
    message: str = ""
    warnings: list[str] = field(default_factory=list)
    initial_cost: Optional[float] = None
    num_iterations: int = 0
    basis_cells: list[tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize sang dict Python thuần (JSON-compatible)."""
        return {
            "allocationMatrix": self.allocation_matrix,
            "totalCost": self.total_cost,
            "isOptimal": self.is_optimal,
            "iterations": [it.to_dict() for it in self.iterations],
            "message": self.message,
            "warnings": self.warnings,
            "initialCost": self.initial_cost,
            "numIterations": self.num_iterations,
            "basisCells": [list(c) for c in self.basis_cells],
        }
