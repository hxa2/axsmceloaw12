"""
backend/core/algorithms/initial_solution/vogel.py
===================================================
Phương pháp Xấp xỉ Vogel (Vogel Approximation Method – VAM).

Trạng thái: CHƯA TRIỂN KHAI.
TODO: Implement VAM khi có đủ thông tin kiểm thử.
"""

from backend.core.algorithms.base import InitialSolutionAlgorithm
from backend.core.models.problem import TransportationProblem
from backend.core.models.solution import TransportationSolution


class VogelApproximationMethod(InitialSolutionAlgorithm):
    """
    Phương pháp Xấp xỉ Vogel.

    Thường cho nghiệm ban đầu tốt hơn Least Cost và Northwest Corner,
    nhưng phức tạp hơn khi cài đặt.

    Trạng thái: CHƯA TRIỂN KHAI.
    """

    @property
    def name(self) -> str:
        return "Vogel Approximation"

    @property
    def description(self) -> str:
        return "Phương pháp xấp xỉ Vogel (VAM). Thường cho nghiệm ban đầu tốt nhất. (Chưa triển khai)"

    def solve(self, problem: TransportationProblem) -> TransportationSolution:
        """
        Tìm phương án cực biên bằng Vogel Approximation Method.

        Raises
        ------
        NotImplementedError
            Phương pháp này chưa được triển khai.
        """
        raise NotImplementedError(
            "Vogel Approximation Method chưa được triển khai. "
            "Vui lòng sử dụng Least Cost hoặc Northwest Corner."
        )
