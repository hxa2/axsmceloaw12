"""
backend/core/models/problem.py
================================
Mô hình dữ liệu thuần cho bài toán vận tải.

Không phụ thuộc bất kỳ framework nào (FastAPI, tkinter, pandas UI, v.v).
Có thể serialize ra JSON thông qua dataclass.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TransportationProblem:
    """
    Mô hình bài toán vận tải.

    Attributes
    ----------
    cost_matrix : list[list[float]]
        Ma trận cước phí C (m × n).
    supply : list[float]
        Vectơ lượng phát A (m,) – trữ lượng tại mỗi trạm phát.
    demand : list[float]
        Vectơ lượng thu B (n,) – nhu cầu tại mỗi trạm thu.
    source_names : Optional[list[str]]
        Tên trạm phát (mặc định S1, S2, ...).
    destination_names : Optional[list[str]]
        Tên trạm thu (mặc định D1, D2, ...).
    """

    cost_matrix: list[list[float]]
    supply: list[float]
    demand: list[float]
    source_names: Optional[list[str]] = None
    destination_names: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Tự động gán tên mặc định nếu không cung cấp."""
        m = len(self.supply)
        n = len(self.demand)
        if self.source_names is None:
            self.source_names = [f"S{i + 1}" for i in range(m)]
        if self.destination_names is None:
            self.destination_names = [f"D{j + 1}" for j in range(n)]

    @property
    def num_sources(self) -> int:
        """Số trạm phát m."""
        return len(self.supply)

    @property
    def num_destinations(self) -> int:
        """Số trạm thu n."""
        return len(self.demand)

    @property
    def total_supply(self) -> float:
        """Tổng lượng phát."""
        return sum(self.supply)

    @property
    def total_demand(self) -> float:
        """Tổng lượng thu."""
        return sum(self.demand)

    @property
    def is_balanced(self) -> bool:
        """Kiểm tra bài toán có cân bằng không (tổng cung = tổng cầu)."""
        return abs(self.total_supply - self.total_demand) < 1e-9

    def to_dict(self) -> dict:
        """Serialize sang dict Python thuần (JSON-compatible)."""
        return {
            "costMatrix": self.cost_matrix,
            "supply": self.supply,
            "demand": self.demand,
            "sourceNames": self.source_names,
            "destinationNames": self.destination_names,
        }
