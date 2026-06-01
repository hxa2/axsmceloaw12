"""
backend/core/algorithms/base.py
==================================
Abstract base classes cho các thuật toán bài toán vận tải.

Dependency direction:
  core/algorithms → core/models
  (Không được import từ app, FastAPI, tkinter, hay bất kỳ framework nào)
"""

from abc import ABC, abstractmethod

from backend.core.models.problem import TransportationProblem
from backend.core.models.solution import TransportationSolution


class InitialSolutionAlgorithm(ABC):
    """
    Base class cho thuật toán tìm phương án cực biên xuất phát.

    Subclass phải implement phương thức `solve()`.
    """

    @abstractmethod
    def solve(self, problem: TransportationProblem) -> TransportationSolution:
        """
        Tìm phương án cực biên xuất phát x^0.

        Parameters
        ----------
        problem : TransportationProblem
            Bài toán vận tải đầu vào.

        Returns
        -------
        TransportationSolution
            Lời giải ban đầu (chưa tối ưu).

        Raises
        ------
        RuntimeError
            Nếu không thể hoàn chỉnh tập cơ sở.
        """
        ...

    @property
    def name(self) -> str:
        """Tên hiển thị của thuật toán."""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """Mô tả ngắn của thuật toán."""
        return ""


class OptimizationAlgorithm(ABC):
    """
    Base class cho thuật toán tối ưu hóa phương án vận tải.

    Subclass phải implement phương thức `optimize()`.
    """

    @abstractmethod
    def optimize(
        self,
        problem: TransportationProblem,
        initial_solution: TransportationSolution,
    ) -> TransportationSolution:
        """
        Tối ưu hóa phương án xuất phát.

        Parameters
        ----------
        problem : TransportationProblem
            Bài toán vận tải đầu vào.
        initial_solution : TransportationSolution
            Phương án xuất phát (từ InitialSolutionAlgorithm).

        Returns
        -------
        TransportationSolution
            Lời giải tối ưu (hoặc tốt hơn) với danh sách iterations.

        Raises
        ------
        RuntimeError
            Nếu không tìm được chu trình hoặc tập cơ sở bị lỗi.
        """
        ...

    @property
    def name(self) -> str:
        """Tên hiển thị của thuật toán."""
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """Mô tả ngắn của thuật toán."""
        return ""
