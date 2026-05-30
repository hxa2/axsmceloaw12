"""
Module: data_loader.py
======================
Đọc và kiểm tra tính hợp lệ của dữ liệu đầu vào từ file Excel.

Cấu trúc file Excel (3 sheet, dữ liệu thuần số):
  - Sheet 0: Ma trận cước phí C  (m hàng × n cột)
  - Sheet 1: Vectơ lượng phát A  (1 hàng × m cột  hoặc  m hàng × 1 cột)
  - Sheet 2: Vectơ lượng thu  B  (1 hàng × n cột  hoặc  n hàng × 1 cột)

Cấu trúc dữ liệu nội bộ:
  - C  → np.ndarray 2D (m × n)   : Ma trận cước phí
  - A  → np.ndarray 1D (m,)      : Vectơ lượng phát
  - B  → np.ndarray 1D (n,)      : Vectơ lượng thu
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# Logger riêng cho module này
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hàm công khai chính
# ---------------------------------------------------------------------------

def load_transportation_data(
    filepath: str,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Đọc toàn bộ dữ liệu bài toán vận tải từ file Excel.

    Parameters
    ----------
    filepath : str
        Đường dẫn đến file Excel đầu vào.

    Returns
    -------
    C : np.ndarray, shape (m, n)
        Ma trận cước phí vận chuyển (giá trị không âm).
    A : np.ndarray, shape (m,)
        Vectơ lượng phát – trữ lượng tại mỗi trạm phát.
    B : np.ndarray, shape (n,)
        Vectơ lượng thu  – nhu cầu tại mỗi trạm thu.

    Raises
    ------
    FileNotFoundError
        Nếu file Excel không tồn tại tại đường dẫn đã cho.
    ValueError
        Nếu dữ liệu không đủ sheet, sai kích thước, chứa giá trị âm,
        hoặc vi phạm điều kiện cân bằng thu phát.
    """
    path = Path(filepath)

    # ── Kiểm tra sự tồn tại của file ────────────────────────────────────
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu: '{filepath}'. "
            f"Hãy chạy 'generate_sample_data.py' để tạo file mẫu."
        )

    logger.info(f"Đang đọc dữ liệu từ: {filepath}")

    try:
        xl = pd.ExcelFile(filepath, engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Không thể mở file Excel: {exc}") from exc

    # ── Kiểm tra số lượng sheet tối thiểu ───────────────────────────────
    if len(xl.sheet_names) < 3:
        raise ValueError(
            f"File Excel phải có ít nhất 3 sheet "
            f"(tìm thấy {len(xl.sheet_names)} sheet). "
            f"Sheet 0: cước phí C, Sheet 1: lượng phát A, Sheet 2: lượng thu B."
        )

    # ── Đọc từng sheet ───────────────────────────────────────────────────
    try:
        # Sheet 0: Ma trận cước phí C (hoàn toàn số, không có header)
        df_cost = pd.read_excel(filepath, sheet_name=0, header=None, engine="openpyxl")
        C = df_cost.to_numpy(dtype=float)

        # Sheet 1: Vectơ lượng phát A (1D)
        df_supply = pd.read_excel(filepath, sheet_name=1, header=None, engine="openpyxl")
        A = _extract_1d_vector(df_supply, name="lượng phát A")

        # Sheet 2: Vectơ lượng thu B (1D)
        df_demand = pd.read_excel(filepath, sheet_name=2, header=None, engine="openpyxl")
        B = _extract_1d_vector(df_demand, name="lượng thu B")

    except ValueError:
        raise  # Giữ nguyên ValueError để caller xử lý
    except Exception as exc:
        raise ValueError(f"Lỗi khi đọc nội dung file Excel: {exc}") from exc

    # ── Kiểm tra kích thước tương thích ──────────────────────────────────
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

    # ── Kiểm tra kích thước tối thiểu (m ≥ 2, n ≥ 2) ────────────────────
    if m < 2 or n < 2:
        raise ValueError(
            f"Bài toán vận tải cần ít nhất 2 trạm phát và 2 trạm thu "
            f"(hiện tại m={m}, n={n})."
        )

    # ── Kiểm tra ràng buộc phi âm ────────────────────────────────────────
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

    # ── Kiểm tra điều kiện cân bằng thu phát (bắt buộc) ─────────────────
    total_supply = float(np.sum(A))
    total_demand = float(np.sum(B))
    if not np.isclose(total_supply, total_demand, rtol=1e-9, atol=1e-9):
        raise ValueError(
            f"Vi phạm điều kiện cân bằng thu phát: "
            f"Tổng lượng phát = {total_supply:.6g} ≠ "
            f"Tổng lượng thu = {total_demand:.6g}. "
            f"Chênh lệch = {abs(total_supply - total_demand):.6g}."
        )

    # ── Ghi log thông tin tổng quan ──────────────────────────────────────
    logger.info(
        f"Đọc dữ liệu thành công: {m} trạm phát × {n} trạm thu | "
        f"Tổng lượng hàng = {total_supply:.6g}"
    )
    logger.debug(f"Ma trận cước phí C ({m}×{n}):\n{C}")
    logger.debug(f"Vectơ lượng phát A: {A}")
    logger.debug(f"Vectơ lượng thu  B: {B}")

    return C, A, B


# ---------------------------------------------------------------------------
# Hàm hỗ trợ nội bộ
# ---------------------------------------------------------------------------

def _extract_1d_vector(df: pd.DataFrame, name: str) -> np.ndarray:
    """
    Trích xuất vectơ 1D từ DataFrame (chấp nhận cả dạng hàng ngang lẫn cột dọc).

    Parameters
    ----------
    df   : pd.DataFrame  DataFrame chứa dữ liệu vectơ.
    name : str           Tên vectơ – dùng trong thông báo lỗi.

    Returns
    -------
    np.ndarray, shape (k,)
        Vectơ 1D đã được trích xuất.

    Raises
    ------
    ValueError
        Nếu DataFrame không có dạng 1 hàng hoặc 1 cột.
    """
    rows, cols = df.shape

    if rows == 1:
        # Vectơ hàng ngang: (1 × k)
        vec = df.iloc[0].to_numpy(dtype=float)
    elif cols == 1:
        # Vectơ cột dọc: (k × 1)
        vec = df.iloc[:, 0].to_numpy(dtype=float)
    else:
        raise ValueError(
            f"Vectơ {name} phải có dạng 1 hàng hoặc 1 cột "
            f"(tìm thấy shape {rows}×{cols})."
        )

    # Loại bỏ NaN nếu có (do ô Excel trống ở cuối)
    vec = vec[~np.isnan(vec)]
    if vec.size == 0:
        raise ValueError(f"Vectơ {name} rỗng hoặc toàn NaN sau khi đọc từ Excel.")

    return vec
