"""
main.py – Điểm vào chính của chương trình mô phỏng Thuật toán Thế vị.
========================================================================

Pipeline đầy đủ (5 bước):

  Bước 1 ── Đọc & kiểm tra dữ liệu          (data_loader.py)
  Bước 2 ── Phương án cực biên ban đầu       (initial_solution.py)
  Bước 3 ── Tối ưu hóa Thuật toán Thế vị    (potential_method.py)
  Bước 4 ── In tóm tắt kết quả              (console + log file)
  Bước 5 ── Trực quan hóa & lưu PNG         (visualizer.py)

Cấu hình (hardcoded trong CONFIG):
  - input_file       : Đường dẫn file Excel đầu vào.
  - output_dir       : Thư mục lưu kết quả và log.
  - log_file         : File log chi tiết từng vòng lặp.
  - table_plot_file  : File PNG bảng ma trận kết quả.
  - graph_plot_file  : File PNG đồ thị lưỡng phân mạng vận tải.
  - max_iterations   : Giới hạn số vòng lặp (bảo vệ khi suy biến).

Chạy chương trình:
  $ python main.py
  (Nếu chưa có file Excel mẫu: chạy generate_sample_data.py trước)
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Tuple

import numpy as np

# Thêm thư mục gốc vào path để import module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logic.data_loader      import load_transportation_data
from logic.initial_solution import BasisSet, least_cost_method, northwest_corner_method
from logic.potential_method import optimize
from logic.visualizer       import plot_solution_table


# ===========================================================================
# Cấu hình hardcoded
# ===========================================================================

_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _ROOT / "data_and_results"

CONFIG = {
    # ── Đường dẫn I/O ───────────────────────────────────────────────────
    "input_file"      : str(_DATA_DIR / "input_data.xlsx"),
    "output_dir"      : str(_DATA_DIR),
    "log_file"        : str(_DATA_DIR / "optimization_log.txt"),
    "table_plot_file" : str(_DATA_DIR / "solution_table.png"),
    "graph_plot_file" : str(_DATA_DIR / "bipartite_graph.png"),

    # ── Tham số thuật toán ───────────────────────────────────────────────
    "max_iterations"  : 1000,
}


# ===========================================================================
# Thiết lập hệ thống logging
# ===========================================================================

def setup_logging(log_file: str) -> None:
    """
    Cấu hình hai handler logging:
      - FileHandler  : Ghi TOÀN BỘ log chi tiết vào file (level DEBUG).
                       Bao gồm từng vòng lặp, ma trận Δ, chu trình, θ.
      - StreamHandler: Hiển thị log ĐẦY ĐỦ ra console (level INFO).

    Parameters
    ----------
    log_file : str  Đường dẫn file log đầu ra.
    """
    os.makedirs(Path(log_file).parent, exist_ok=True)

    # Định dạng log: thời gian | level | tên module | nội dung
    fmt = logging.Formatter(
        fmt     = "%(asctime)s [%(levelname)-8s] %(name)-22s │ %(message)s",
        datefmt = "%H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # ── File handler (DEBUG → ghi hết chi tiết) ──────────────────────────
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # ── Console handler (INFO → tóm tắt ngắn gọn) ────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)


# ===========================================================================
# In tóm tắt kết quả cuối
# ===========================================================================

def print_final_summary(
    C       : np.ndarray,
    X_init  : np.ndarray,
    X_opt   : np.ndarray,
    A       : np.ndarray,
    B       : np.ndarray,
    basis   : BasisSet,
    cost_init  : float,
    cost_opt   : float,
    iterations : int,
) -> None:
    """
    In bảng tóm tắt kết quả ra console và file log.

    Bao gồm:
      - Thông số bài toán (kích thước, số ô cơ sở, số vòng lặp).
      - So sánh chi phí ban đầu vs chi phí tối ưu.
      - Ma trận X* được định dạng theo bảng, ô cơ sở được đánh dấu (*).

    Parameters
    ----------
    C, X_init, X_opt : np.ndarray   Ma trận cước phí, phương án ban đầu và tối ưu.
    A, B             : np.ndarray   Vectơ cung / cầu.
    basis            : BasisSet     Tập cơ sở tối ưu.
    cost_init        : float        Chi phí phương án ban đầu.
    cost_opt         : float        Chi phí phương án tối ưu.
    iterations       : int          Số vòng lặp thế vị đã thực hiện.
    """
    log = logging.getLogger(__name__)
    m, n = C.shape
    sep  = "═" * 68

    log.info(f"\n{sep}")
    log.info("KET QUA CUOI CUNG – THUAT TOAN THE VI")
    log.info(sep)

    # ── Thông số bài toán ─────────────────────────────────────────────────
    log.info(f"  Kich thuoc bai toan : {m} tram phat  x  {n} tram thu")
    log.info(f"  So o co so          : {len(basis)} = m + n - 1 = {m + n - 1}")
    log.info(f"  So vong lap the vi  : {iterations}")

    # ── So sánh chi phí ───────────────────────────────────────────────────
    pct = (cost_init - cost_opt) / cost_init * 100 if cost_init > 1e-9 else 0.0
    log.info(f"  Chi phi ban dau (CTC) : {cost_init:.6g}")
    log.info(f"  Chi phi toi uu  (TW)  : {cost_opt:.6g}")
    log.info(f"  Cai thien              : {pct:.2f}%")

    # ── Ma trận X* ────────────────────────────────────────────────────────
    log.info(f"\n  Phuong an toi uu X* (o co so danh dau *):")

    # Header
    col_w = 9
    hdr_parts = [f"{'':>6}"]
    for j in range(n):
        hdr_parts.append(f"  T{j+1:>{col_w - 3}}")
    hdr_parts.append(f"  {'a_i':>{col_w - 2}}")
    log.info("  " + "".join(hdr_parts))
    log.info("  " + "─" * (6 + (col_w + 1) * (n + 1)))

    for i in range(m):
        row_parts = [f"  P{i+1:>2} │"]
        for j in range(n):
            val    = X_opt[i, j]
            mark   = "*" if (i, j) in basis else " "
            cell   = f"{val:.4g}{mark}"
            row_parts.append(f"  {cell:>{col_w}}")
        row_parts.append(f"  {A[i]:>{col_w}.4g}")
        log.info("".join(row_parts))

    log.info("  " + "─" * (6 + (col_w + 1) * (n + 1)))

    # Hàng b_j
    dem_parts = [f"  {'b_j':>4} │"]
    for j in range(n):
        dem_parts.append(f"  {B[j]:>{col_w}.4g}")
    dem_parts.append(f"  {'Tong':>{col_w}}")
    log.info("".join(dem_parts))

    log.info(f"\n  (* = o co so   |  Tong chi phi toi uu: f(X*) = {cost_opt:.6g})")
    log.info(sep)


# ===========================================================================
# Hàm chính
# ===========================================================================

def main() -> None:
    """
    Hàm điều phối toàn bộ pipeline Thuật toán Thế vị.

    Exit codes:
        0  – Thành công.
        1  – Lỗi dữ liệu (file không tồn tại, dữ liệu không hợp lệ).
        2  – Lỗi thuật toán (không tìm được chu trình, tập cơ sở lỗi).
        3  – Lỗi không xác định.
    """
    # ── Bước 0: Người dùng chọn phương pháp xuất phát ───────────────────
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║   CHỌN PHƯƠNG PHÁP TÌM PHƯƠNG ÁN CỰC BIÊN XUẤT PHÁT      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║   1. Phương pháp Cực tiểu Chi phí (Least Cost Method)      ║")
    print("║   2. Phương pháp Góc Tây Bắc (Northwest Corner Method)     ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    while True:
        choice = input("  ▸ Nhập lựa chọn (1 hoặc 2): ").strip()
        if choice in ("1", "2"):
            method_id = int(choice)
            break
        print("    ⚠ Vui lòng nhập 1 hoặc 2.")

    # ── Bước 0b: Khởi tạo logging ─────────────────────────────────────────
    setup_logging(CONFIG["log_file"])
    log = logging.getLogger(__name__)

    log.info("╔══════════════════════════════════════════════════════════════╗")
    log.info("║        THUẬT TOÁN THẾ VỊ – BÀI TOÁN VẬN TẢI                  ║")
    log.info("╚══════════════════════════════════════════════════════════════╝")

    start = time.perf_counter()

    try:
        # ── Bước 1: Đọc & kiểm tra dữ liệu ──────────────────────────────
        log.info(f"\n[BUOC 1] Doc du lieu tu: {CONFIG['input_file']}")
        C, A, B = load_transportation_data(CONFIG["input_file"])
        m, n    = C.shape
        log.info(f"         Bai toan: {m} tram phat x {n} tram thu | "
                 f"Tong hang hoa = {np.sum(A):.6g}")

        # ── Bước 2: Tìm phương án cực biên ban đầu (Giai đoạn 1) ─────────
        if method_id == 2:
            method_name = "Góc Tây Bắc"
            log.info("\n[BUOC 2] Tim phuong an cuc bien (Phuong phap Goc Tay Bac)...")
            X_init, basis_init = northwest_corner_method(C, A, B)
        else:
            method_name = "Cực tiểu Chi phí"
            log.info("\n[BUOC 2] Tim phuong an cuc bien (Phuong phap Cuc tieu Chi phi)...")
            X_init, basis_init = least_cost_method(C, A, B)
        cost_init = float(np.sum(C * X_init))
        log.info(f"         Hoan thanh Giai doan 1 | Chi phi ban dau = {cost_init:.6g}")

        # ── Bước 3: Tối ưu hóa Thuật toán Thế vị (Giai đoạn 2) ──────────
        log.info("\n[BUOC 3] Toi uu hoa bang Thuat toan The vi...")
        X_opt, basis_opt, cost_opt, iterations = optimize(
            C           = C,
            X_init      = X_init,
            basis_init  = basis_init,
            A           = A,
            B           = B,
            max_iterations = CONFIG["max_iterations"],
        )
        log.info(f"         Hoan thanh Giai doan 2 | "
                 f"So vong lap = {iterations} | "
                 f"Chi phi toi uu = {cost_opt:.6g}")

        # ── Bước 4: Tóm tắt kết quả ───────────────────────────────────────
        log.info("\n[BUOC 4] Tom tat ket qua:")
        print_final_summary(
            C=C, X_init=X_init, X_opt=X_opt,
            A=A, B=B, basis=basis_opt,
            cost_init=cost_init, cost_opt=cost_opt,
            iterations=iterations,
        )

        # ── Bước 5: Trực quan hóa & lưu PNG ──────────────────────────────
        log.info("\n[BUOC 5] Tao bieu do truc quan hoa...")

        plot_solution_table(
            C           = C,
            X           = X_opt,
            A           = A,
            B           = B,
            basis       = basis_opt,
            total_cost  = cost_opt,
            output_path = CONFIG["table_plot_file"],
            title       = "Phương án vận tải tối ưu",
            init_method_name = method_name,
        )


        # ── Tổng kết thời gian thực thi ───────────────────────────────────
        elapsed = time.perf_counter() - start
        log.info(f"\n{'═' * 68}")
        log.info(f"CHUONG TRINH HOAN THANH TRONG {elapsed:.3f} GIAY")
        log.info(f"  File log chi tiet : {CONFIG['log_file']}")
        log.info(f"  Bang ket qua (PNG): {CONFIG['table_plot_file']}")
        log.info(f"{'═' * 68}")

        sys.exit(0)

    except FileNotFoundError as exc:
        logging.getLogger(__name__).error(
            f"[LOI FILE] {exc}\n"
            f"  → Hay chay 'python generate_sample_data.py' de tao file mau."
        )
        sys.exit(1)

    except ValueError as exc:
        logging.getLogger(__name__).error(f"[LOI DU LIEU] {exc}")
        sys.exit(1)

    except RuntimeError as exc:
        logging.getLogger(__name__).error(f"[LOI THUAT TOAN] {exc}")
        sys.exit(2)

    except Exception as exc:
        logging.getLogger(__name__).exception(f"[LOI KHONG XAC DINH] {exc}")
        sys.exit(3)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    main()