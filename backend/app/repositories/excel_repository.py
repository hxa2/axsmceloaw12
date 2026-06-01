"""
backend/app/repositories/excel_repository.py
=============================================
Repository đọc dữ liệu bài toán vận tải từ file Excel.

Tách từ data_loader.py cũ.
Chỉ đọc file, không chứa logic thuật toán.
"""

import logging
from io import BytesIO
from typing import Tuple

import numpy as np
import pandas as pd

from backend.core.models.problem import TransportationProblem

logger = logging.getLogger(__name__)


class ExcelRepository:
    """
    Đọc dữ liệu bài toán vận tải từ file Excel.

    Cấu trúc file Excel (3 sheet):
      - Sheet 0: Ma trận cước phí C (m hàng × n cột, thuần số, không header).
      - Sheet 1: Vectơ lượng phát A (1 hàng hoặc 1 cột).
      - Sheet 2: Vectơ lượng thu B (1 hàng hoặc 1 cột).
    """

    def load_xlsx_from_bytes(self, content: bytes) -> TransportationProblem:
        """Đọc từ file .xlsx (dùng openpyxl)."""
        return self._load_excel_with_engine(content, engine="openpyxl")

    def load_xls_from_bytes(self, content: bytes) -> TransportationProblem:
        """Đọc từ file .xls cũ (dùng xlrd)."""
        return self._load_excel_with_engine(content, engine="xlrd")

    def _load_excel_with_engine(self, content: bytes, engine: str) -> TransportationProblem:
        """Đọc dữ liệu từ bytes của file Excel với engine chỉ định."""
        try:
            xl = pd.ExcelFile(BytesIO(content), engine=engine)
        except Exception as exc:
            raise ValueError(f"Không thể mở file Excel bằng {engine}: {exc}") from exc

        if len(xl.sheet_names) < 3:
            raise ValueError(
                f"File Excel phải có ít nhất 3 sheet "
                f"(tìm thấy {len(xl.sheet_names)} sheet). "
                f"Sheet 0: cước phí C, Sheet 1: lượng phát A, Sheet 2: lượng thu B."
            )

        try:
            df_cost = pd.read_excel(xl, sheet_name=0, header=None)
            C = df_cost.to_numpy(dtype=float)

            df_supply = pd.read_excel(xl, sheet_name=1, header=None)
            A = _extract_1d_vector(df_supply, "lượng phát A")

            df_demand = pd.read_excel(xl, sheet_name=2, header=None)
            B = _extract_1d_vector(df_demand, "lượng thu B")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Lỗi đọc nội dung file Excel: {exc}") from exc

        # Kiểm tra kích thước
        m, n = C.shape
        if A.shape[0] != m:
            raise ValueError(
                f"Số hàng ma trận cước phí = {m} nhưng vectơ lượng phát có {A.shape[0]} phần tử. "
                f"Hai giá trị này phải bằng nhau."
            )
        if B.shape[0] != n:
            raise ValueError(
                f"Số cột ma trận cước phí = {n} nhưng vectơ lượng thu có {B.shape[0]} phần tử. "
                f"Hai giá trị này phải bằng nhau."
            )
        if m < 2 or n < 2:
            raise ValueError(f"Bài toán vận tải cần ít nhất 2 trạm phát và 2 trạm thu (hiện tại m={m}, n={n}).")

        # Kiểm tra ràng buộc phi âm
        if np.any(C < 0):
            bad = list(zip(*np.where(C < 0)))
            raise ValueError(
                f"Ma trận cước phí C chứa giá trị âm tại các ô: "
                f"{[(r+1, c+1) for r, c in bad[:5]]}."
            )
        if np.any(A < 0):
            raise ValueError(f"Vectơ lượng phát A chứa giá trị âm: {A[A < 0]}.")
        if np.any(B < 0):
            raise ValueError(f"Vectơ lượng thu B chứa giá trị âm: {B[B < 0]}.")

        # Kiểm tra điều kiện cân bằng thu phát
        total_supply = float(np.sum(A))
        total_demand = float(np.sum(B))
        if not np.isclose(total_supply, total_demand, rtol=1e-9, atol=1e-9):
            raise ValueError(
                f"Vi phạm điều kiện cân bằng thu phát: "
                f"Tổng lượng phát = {total_supply:.6g} ≠ "
                f"Tổng lượng thu = {total_demand:.6g}. "
                f"Chênh lệch = {abs(total_supply - total_demand):.6g}."
            )

        logger.info(f"Đọc Excel thành công: {m}×{n}, tổng = {total_supply:.6g}")

        return TransportationProblem(
            cost_matrix=C.tolist(),
            supply=A.tolist(),
            demand=B.tolist(),
        )

    def load_from_path(self, filepath: str) -> TransportationProblem:
        """Đọc từ đường dẫn file."""
        with open(filepath, "rb") as f:
            if filepath.lower().endswith(".xls"):
                return self.load_xls_from_bytes(f.read())
            return self.load_xlsx_from_bytes(f.read())


def _extract_1d_vector(df: pd.DataFrame, name: str) -> np.ndarray:
    """Trích xuất vectơ 1D từ DataFrame (chấp nhận hàng hoặc cột)."""
    rows, cols = df.shape
    if rows == 1:
        vec = df.iloc[0].to_numpy(dtype=float)
    elif cols == 1:
        vec = df.iloc[:, 0].to_numpy(dtype=float)
    else:
        raise ValueError(
            f"Vectơ {name} phải có dạng 1 hàng hoặc 1 cột "
            f"(tìm thấy shape {rows}×{cols})."
        )
    vec = vec[~np.isnan(vec)]
    if vec.size == 0:
        raise ValueError(f"Vectơ {name} rỗng hoặc toàn NaN.")
    return vec
