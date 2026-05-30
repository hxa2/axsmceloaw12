"""
generate_sample_data.py
========================
Tạo file Excel mẫu (data/input_data.xlsx) cho kiểm thử pipeline.

Cung cấp hai bài toán mẫu có lời giải đã biết:
  - Mẫu A (3×4): Bài toán cổ điển, lời giải tối ưu f* = 53.
  - Mẫu B (4×5): Bài toán lớn hơn có trường hợp suy biến nhẹ.

Chạy:
  $ python generate_sample_data.py          → tạo Mẫu A (mặc định)
  $ python generate_sample_data.py --B      → tạo Mẫu B
"""

import argparse
import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent

import numpy as np
import pandas as pd


# ===========================================================================
# Định nghĩa các bài toán mẫu
# ===========================================================================

def _sample_A() -> tuple:
    """
    Bài toán vận tải 3 trạm phát × 4 trạm thu.

    Ma trận cước phí C:
        |  2   3   1   5 |
        |  7   3   4   6 |
        |  3   8   2   4 |

    Lượng phát A = [7, 5, 7]
    Lượng thu  B = [5, 4, 6, 4]
    Tổng = 19 (cân bằng)

    Lời giải tối ưu đã biết: f* = 53
    Phương án:
        x_13 = 6, x_14 = 1   (Phat 1)
        x_22 = 4, x_23 = 1   (Phat 2) – một số lời giải thay thế có thể
        x_31 = 5, x_33 = 2   (Phat 3)
    """
    C = np.array([
        [2, 3, 1, 5],
        [7, 3, 4, 6],
        [3, 8, 2, 4],
    ], dtype=float)
    A = np.array([7, 5, 7], dtype=float)
    B = np.array([5, 4, 6, 4], dtype=float)
    name = "3x4_classic"
    return C, A, B, name


def _sample_B() -> tuple:
    """
    Bài toán vận tải 4 trạm phát × 5 trạm thu (có khả năng suy biến).

    Ma trận cước phí C:
        |  4   8   1   2   6 |
        |  7   2   3   9   4 |
        |  3   5   7   1   5 |
        |  6   1   4   3   2 |

    Lượng phát A = [10, 8, 12, 10]
    Lượng thu  B = [8,  9,  6,  9,  8]
    Tổng = 40 (cân bằng)
    """
    C = np.array([
        [4, 8, 1, 2, 6],
        [7, 2, 3, 9, 4],
        [3, 5, 7, 1, 5],
        [6, 1, 4, 3, 2],
    ], dtype=float)
    A = np.array([10, 8, 12, 10], dtype=float)
    B = np.array([ 8,  9,  6,  9,  8], dtype=float)
    name = "4x5_with_degeneracy"
    return C, A, B, name


# ===========================================================================
# Hàm tạo file Excel
# ===========================================================================

def create_excel(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    output_path: str = None,
) -> None:
    """
    Ghi dữ liệu bài toán vận tải vào file Excel 3 sheet.

    Cấu trúc sheet:
        Sheet 0 (Chi_phi)  : Ma trận cước phí C (m × n, không có header)
        Sheet 1 (Luong_phat): Vectơ lượng phát A (1 hàng × m cột)
        Sheet 2 (Luong_thu) : Vectơ lượng thu  B (1 hàng × n cột)

    Dữ liệu thuần số (không có nhãn hàng/cột).

    Parameters
    ----------
    C           : np.ndarray  Ma trận cước phí (m × n).
    A           : np.ndarray  Vectơ lượng phát (m,).
    B           : np.ndarray  Vectơ lượng thu  (n,).
    output_path : str         Đường dẫn file Excel đầu ra.
    """
    if output_path is None:
        output_path = str(_BASE.parent / "data_and_results" / "input_data.xlsx")

    # Kiểm tra điều kiện cân bằng
    assert np.isclose(A.sum(), B.sum()), (
        f"Loi du lieu mau: Tong phat ({A.sum()}) != Tong thu ({B.sum()})."
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

        # Sheet 0: Ma trận cước phí C
        pd.DataFrame(C).to_excel(
            writer, sheet_name="Chi_phi",
            index=False, header=False,
        )

        # Sheet 1: Vectơ lượng phát A (1 hàng ngang × m phần tử)
        pd.DataFrame(A.reshape(1, -1)).to_excel(
            writer, sheet_name="Luong_phat",
            index=False, header=False,
        )

        # Sheet 2: Vectơ lượng thu B (1 hàng ngang × n phần tử)
        pd.DataFrame(B.reshape(1, -1)).to_excel(
            writer, sheet_name="Luong_thu",
            index=False, header=False,
        )

    print(f"\nDa tao file Excel: {output_path}")


def _print_problem_summary(
    C: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    name: str,
) -> None:
    """In tóm tắt thông tin bài toán mẫu ra console."""
    m, n = C.shape
    print(f"\n{'═' * 56}")
    print(f"  Bai toan mau: {name}")
    print(f"  Kich thuoc : {m} tram phat x {n} tram thu")
    print(f"  Tong hang  : {A.sum():.4g}  (phat) = {B.sum():.4g}  (thu)  ✓")
    print(f"{'═' * 56}")

    # Ma trận cước phí
    print(f"\n  Ma tran cuoc phi C ({m}x{n}):")
    header = "        " + "".join(f"  T{j+1:>3}" for j in range(n))
    print(header)
    print("        " + "─" * (6 * n))
    for i in range(m):
        row = "".join(f"  {C[i, j]:>5.4g}" for j in range(n))
        print(f"  P{i+1:>2}  │{row}  │  a={A[i]:.4g}")
    print("        " + "─" * (6 * n))
    dem = "".join(f"  {B[j]:>5.4g}" for j in range(n))
    print(f"  b_j  │{dem}")
    print()


# ===========================================================================
# Entry point
# ===========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tao file Excel mau cho Thuat toan The vi.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Vi du su dung:\n"
            "  python generate_sample_data.py         # Mau A (3x4)\n"
            "  python generate_sample_data.py --B     # Mau B (4x5)\n"
            "  python generate_sample_data.py --output custom.xlsx"
        ),
    )
    parser.add_argument(
        "--B",
        action="store_true",
        help="Su dung bai toan mau B (4x5) thay vi mau A (3x4) mac dinh.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Duong dan file Excel dau ra (mac dinh: input_data.xlsx cung cap voi script).",
    )
    args = parser.parse_args()

    # Chọn bài toán mẫu
    if args.B:
        C, A, B, name = _sample_B()
    else:
        C, A, B, name = _sample_A()

    # In tóm tắt
    _print_problem_summary(C, A, B, name)

    # Tạo file Excel
    create_excel(C, A, B, output_path=args.output)

    print(f"\n  Cau truc file Excel da tao:")
    print(f"    Sheet 0 [Chi_phi]   : Ma tran cuoc phi C ({C.shape[0]}x{C.shape[1]})")
    print(f"    Sheet 1 [Luong_phat]: Luong phat A (1x{len(A)})")
    print(f"    Sheet 2 [Luong_thu] : Luong thu  B (1x{len(B)})")
    print(f"\n  Chay pipeline chinh:")
    print(f"    $ python ui/main.py")
    print()


if __name__ == "__main__":
    main()
