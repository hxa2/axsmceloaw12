"""
backend/app/repositories/json_repository.py
=============================================
Repository đọc dữ liệu bài toán vận tải từ file JSON.

Format JSON:
{
  "costMatrix": [[...], [...], ...],
  "supply": [...],
  "demand": [...],
  "sourceNames": [...],     (tuỳ chọn)
  "destinationNames": [...]  (tuỳ chọn)
}
"""

import json
import logging

from backend.core.models.problem import TransportationProblem

logger = logging.getLogger(__name__)


class JsonRepository:
    """Đọc dữ liệu bài toán vận tải từ file JSON."""

    def load_from_bytes(self, content: bytes) -> TransportationProblem:
        """
        Đọc dữ liệu từ bytes của file JSON.

        Raises
        ------
        ValueError  Nếu file không đúng cấu trúc.
        """
        try:
            data = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"File JSON không hợp lệ: {exc}") from exc

        required = {"costMatrix", "supply", "demand"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"File JSON thiếu các trường: {', '.join(sorted(missing))}.")

        try:
            cost_matrix = [[float(v) for v in row] for row in data["costMatrix"]]
            supply = [float(v) for v in data["supply"]]
            demand = [float(v) for v in data["demand"]]
            source_names = data.get("sourceNames")
            destination_names = data.get("destinationNames")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Dữ liệu JSON không hợp lệ: {exc}") from exc

        logger.info(f"Đọc JSON thành công: {len(cost_matrix)}×{len(cost_matrix[0]) if cost_matrix else 0}")

        return TransportationProblem(
            cost_matrix=cost_matrix,
            supply=supply,
            demand=demand,
            source_names=source_names,
            destination_names=destination_names,
        )
