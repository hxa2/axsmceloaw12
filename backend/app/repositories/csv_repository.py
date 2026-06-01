"""
backend/app/repositories/csv_repository.py
=============================================
Repository đọc dữ liệu bài toán vận tải từ file CSV.

Format CSV:
  - Dòng 1: "cost_matrix"
  - Dòng 2 đến m+1: các hàng của ma trận chi phí (ngăn cách bằng dấu phẩy)
  - Dòng m+2: "supply"
  - Dòng m+3: giá trị supply (ngăn cách bằng dấu phẩy)
  - Dòng m+4: "demand"
  - Dòng m+5: giá trị demand (ngăn cách bằng dấu phẩy)
"""

import csv
import io
import logging

from backend.core.models.problem import TransportationProblem

logger = logging.getLogger(__name__)


class CsvRepository:
    """Đọc dữ liệu bài toán vận tải từ file CSV."""

    def load_from_bytes(self, content: bytes) -> TransportationProblem:
        """
        Đọc dữ liệu từ bytes của file CSV.

        Raises
        ------
        ValueError  Nếu file không đúng cấu trúc.
        """
        text = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        rows = [row for row in reader if any(cell.strip() for cell in row)]

        if len(rows) < 5:
            raise ValueError(
                "File CSV cần ít nhất 5 dòng: "
                "'cost_matrix', [các hàng ma trận], 'supply', [supply], 'demand', [demand]."
            )

        try:
            cost_matrix = []
            supply = []
            demand = []
            section = None

            for row in rows:
                if not row:
                    continue
                first = row[0].strip().lower()
                if first == "cost_matrix":
                    section = "cost"
                    continue
                elif first == "supply":
                    section = "supply"
                    continue
                elif first == "demand":
                    section = "demand"
                    continue

                values = [float(cell.strip()) for cell in row if cell.strip()]
                if section == "cost":
                    cost_matrix.append(values)
                elif section == "supply":
                    supply.extend(values)
                elif section == "demand":
                    demand.extend(values)

        except ValueError as exc:
            raise ValueError(f"Lỗi parse CSV: {exc}") from exc

        if not cost_matrix:
            raise ValueError("Không tìm thấy ma trận chi phí trong file CSV.")
        if not supply:
            raise ValueError("Không tìm thấy lượng phát (supply) trong file CSV.")
        if not demand:
            raise ValueError("Không tìm thấy lượng thu (demand) trong file CSV.")

        logger.info(f"Đọc CSV thành công: {len(cost_matrix)}×{len(cost_matrix[0])}")

        return TransportationProblem(
            cost_matrix=cost_matrix,
            supply=supply,
            demand=demand,
        )
