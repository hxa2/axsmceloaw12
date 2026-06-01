"""
backend/app/services/sample_data_service.py
=============================================
Service cung cấp dữ liệu mẫu cho bài toán vận tải.

Tách từ generate_sample_data.py cũ – chỉ cung cấp dữ liệu tĩnh,
không ghi file trực tiếp.
"""

import random
from typing import Optional

from backend.app.schemas.response import SampleProblemResponse


class SampleDataService:
    """
    Service cung cấp các bài toán vận tải mẫu.
    """

    def get_sample_problem(self, sample_id: str = "classic_3x4") -> SampleProblemResponse:
        """
        Trả một bài toán mẫu theo ID.

        Parameters
        ----------
        sample_id : str
            Mã nhận dạng bài toán mẫu.

        Returns
        -------
        SampleProblemResponse
        """
        samples = self._get_all_samples()
        problem = samples.get(sample_id)
        if problem is None:
            # Default: classic 3x4
            problem = samples["classic_3x4"]
        return problem

    def list_samples(self) -> list[SampleProblemResponse]:
        """Trả danh sách tất cả bài toán mẫu."""
        return list(self._get_all_samples().values())

    def get_random_problem(
        self,
        m: int = 3,
        n: int = 4,
        degenerate: bool = False,
    ) -> SampleProblemResponse:
        """
        Sinh bài toán ngẫu nhiên kích thước m × n.

        Parameters
        ----------
        m : int  Số trạm phát (2-10).
        n : int  Số trạm thu (2-10).
        degenerate : bool  Có muốn bài toán suy biến không.
        """
        m = max(2, min(10, m))
        n = max(2, min(10, n))
        rng = random.Random()

        # Ma trận chi phí ngẫu nhiên 1-19
        cost_matrix = [
            [float(rng.randint(1, 19)) for _ in range(n)]
            for _ in range(m)
        ]

        if degenerate:
            # Tạo suy biến: supply[0] = demand[0]
            shared_val = float(rng.randint(5, 15))
            supply = [float(rng.randint(6, 20)) for _ in range(m)]
            demand = [float(rng.randint(6, 20)) for _ in range(n)]
            supply[0] = shared_val
            demand[0] = shared_val
            # Cân bằng
            total_s = sum(supply)
            total_d = sum(demand)
            demand[-1] = max(1.0, demand[-1] + (total_s - total_d))
        else:
            supply = [float(rng.randint(8, 25)) for _ in range(m)]
            total_s = sum(supply)
            demand = []
            base = total_s / n
            for _ in range(n - 1):
                d = round(base + rng.uniform(-base * 0.3, base * 0.3))
                demand.append(max(1.0, float(d)))
            demand.append(max(1.0, total_s - sum(demand)))

        return SampleProblemResponse(
            name=f"Ngẫu nhiên {m}×{n}{'(suy biến)' if degenerate else ''}",
            description=f"Bài toán vận tải ngẫu nhiên {m} trạm phát × {n} trạm thu.",
            costMatrix=cost_matrix,
            supply=supply,
            demand=demand,
        )

    def _get_all_samples(self) -> dict[str, SampleProblemResponse]:
        return {
            "classic_3x4": SampleProblemResponse(
                name="Mẫu A: 3×4 Cổ điển",
                description="Bài toán vận tải 3 trạm phát × 4 trạm thu. Nghiệm tối ưu biết trước f* = 50.",
                costMatrix=[
                    [2.0, 3.0, 1.0, 5.0],
                    [7.0, 3.0, 4.0, 6.0],
                    [3.0, 8.0, 2.0, 4.0],
                ],
                supply=[7.0, 5.0, 7.0],
                demand=[5.0, 4.0, 6.0, 4.0],
                optimalCost=50.0,
                sourceNames=["S1", "S2", "S3"],
                destinationNames=["D1", "D2", "D3", "D4"],
            ),
            "medium_4x5": SampleProblemResponse(
                name="Mẫu B: 4×5 Trung bình",
                description="Bài toán vận tải 4 trạm phát × 5 trạm thu. Có khả năng suy biến nhẹ.",
                costMatrix=[
                    [4.0, 8.0, 1.0, 2.0, 6.0],
                    [7.0, 2.0, 3.0, 9.0, 4.0],
                    [3.0, 5.0, 7.0, 1.0, 5.0],
                    [6.0, 1.0, 4.0, 3.0, 2.0],
                ],
                supply=[10.0, 8.0, 12.0, 10.0],
                demand=[8.0, 9.0, 6.0, 9.0, 8.0],
                sourceNames=["S1", "S2", "S3", "S4"],
                destinationNames=["D1", "D2", "D3", "D4", "D5"],
            ),
            "simple_2x3": SampleProblemResponse(
                name="Mẫu C: 2×3 Đơn giản",
                description="Bài toán vận tải 2 trạm phát × 3 trạm thu. Phù hợp để học thuật toán.",
                costMatrix=[
                    [2.0, 3.0, 1.0],
                    [5.0, 4.0, 8.0],
                ],
                supply=[20.0, 30.0],
                demand=[10.0, 25.0, 15.0],
                sourceNames=["Kho Hà Nội", "Kho Đà Nẵng"],
                destinationNames=["TPHCM", "Cần Thơ", "Huế"],
            ),
        }
