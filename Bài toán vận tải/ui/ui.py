"""
ui.py – Giao diện đồ họa (GUI) cho Bài toán vận tải – Thuật toán Thế vị
=========================================================================

Công nghệ: CustomTkinter (tkinter hiện đại) + tkinter.ttk (Treeview bảng X*)
Pipeline tích hợp toàn bộ logic từ:
    data_loader.py      → load_transportation_data()
    generate_sample_data.py → create_excel(), _sample_A(), _sample_B()
    initial_solution.py → least_cost_method(), northwest_corner_method()
    potential_method.py → optimize()
    visualizer.py       → plot_solution_table()
"""

import sys
import os
import io
import threading
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

# pyrefly: ignore [missing-import]
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

# ── Đảm bảo import được các module cùng thư mục ─────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from logic.data_loader import load_transportation_data
from logic.generate_sample_data import create_excel, _sample_A, _sample_B
from logic.initial_solution import least_cost_method, northwest_corner_method
from logic.potential_method import optimize
from logic.visualizer import plot_solution_table


# ── Cấu hình CustomTkinter ───────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Màu sắc chuẩn ───────────────────────────────────────────────────────────
CLR_LEFT_BG   = "#1a1a2e"   # Cột cấu hình – xanh đêm
CLR_ACCENT    = "#2563eb"   # Xanh dương nổi bật
CLR_ACCENT_HV = "#1d4ed8"   # Hover nút chính
CLR_BASIS_BG  = "#DBEAFE"   # Ô cơ sở trong bảng X*
CLR_CARD_BG   = "#F8FAFC"   # Nền card thống kê
CLR_OK        = "#22c55e"   # Xanh lá – trạng thái hợp lệ
CLR_ERR       = "#ef4444"   # Đỏ – trạng thái lỗi


# ===========================================================================
# Tiện ích – Capture log vào StringIO
# ===========================================================================

class _ListHandler(logging.Handler):
    """Ghi log vào một list để GUI đọc về sau."""
    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))

    def get_text(self) -> str:
        return "\n".join(self.records)

    def clear(self) -> None:
        self.records.clear()


# ===========================================================================
# Cửa sổ phụ – Hiển thị sơ đồ trong cửa sổ riêng
# ===========================================================================

class DiagramWindow(ctk.CTkToplevel):
    """Cửa sổ popup hiển thị sơ đồ bảng vận tải với zoom đầy đủ."""

    def __init__(self, master, img_pil: Image.Image):
        super().__init__(master)
        self.title("Sơ đồ Bảng Vận Tải – solution_table.png")
        self.geometry("1000x680")
        self.resizable(True, True)
        self.after(10, lambda: self.state("zoomed"))
        self.attributes("-topmost", True)
        self.focus_set()

        self._img_pil = img_pil
        self._zoom    = 1.0
        self._img_tk  = None

        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=CLR_ACCENT, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🗺  Sơ đồ Bảng Vận Tải",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(hdr, text="✕", width=32, height=28,
                      fg_color="transparent", hover_color="#1d4ed8",
                      text_color="white", font=ctk.CTkFont("Segoe UI", 14),
                      command=self.destroy).pack(side="right", padx=8, pady=8)

        # ── Canvas cuộn ───────────────────────────────────────────────────
        cv_frame = tk.Frame(self, bg="#f1f5f9")
        cv_frame.pack(fill="both", expand=True, padx=0, pady=0)
        cv_frame.rowconfigure(0, weight=1)
        cv_frame.columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(cv_frame, bg="#f1f5f9", highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(cv_frame, orient="vertical",
                             command=self._canvas.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(cv_frame, orient="horizontal",
                             command=self._canvas.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self._canvas.configure(yscrollcommand=sb_y.set,
                               xscrollcommand=sb_x.set)
        self._canvas.bind("<Configure>", lambda _e: self._render())

        # ── Thanh nút dưới ────────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=0)
        btn_bar.pack(fill="x", padx=0, pady=0)

        for text, cmd, fg, hv, tc in [
            ("🔍  Phóng to",    self._zoom_in,  "#e2e8f0", "#cbd5e1", "#1e293b"),
            ("⊖  Thu nhỏ",     self._zoom_out, "#e2e8f0", "#cbd5e1", "#1e293b"),
            ("⊡  Vừa khung",   self._fit,      "#e2e8f0", "#cbd5e1", "#1e293b"),
            ("💾  Lưu ảnh",    self._save,     CLR_ACCENT, CLR_ACCENT_HV, "white"),
        ]:
            ctk.CTkButton(btn_bar, text=text, width=120,
                          fg_color=fg, hover_color=hv, text_color=tc,
                          font=ctk.CTkFont("Segoe UI", 12),
                          command=cmd).pack(side="left", padx=(8, 0), pady=8)

        self._lbl_zoom = ctk.CTkLabel(btn_bar, text="100%",
                                      font=ctk.CTkFont("Segoe UI", 11),
                                      text_color="#64748b")
        self._lbl_zoom.pack(side="left", padx=12)

        # Render ngay khi cửa sổ hiển thị
        self.after(80, self._fit)

    def _render(self):
        if self._img_pil is None:
            return
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        ow, oh = self._img_pil.size
        nw = max(1, int(ow * self._zoom))
        nh = max(1, int(oh * self._zoom))
        resized = self._img_pil.resize((nw, nh), Image.LANCZOS)
        self._img_tk = ImageTk.PhotoImage(resized)
        self._canvas.delete("all")
        cx = max(nw, cw) // 2
        cy = max(nh, ch) // 2
        self._canvas.create_image(cx, cy, anchor="center", image=self._img_tk)
        self._canvas.configure(scrollregion=(0, 0, max(nw, cw), max(nh, ch)))
        self._lbl_zoom.configure(text=f"{int(self._zoom * 100)}%")

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 8.0)
        self._render()

    def _zoom_out(self):
        self._zoom = max(self._zoom * 0.8, 0.1)
        self._render()

    def _fit(self):
        """Tự động chỉnh zoom để ảnh vừa khung canvas."""
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        if cw < 10 or ch < 10 or self._img_pil is None:
            return
        ow, oh = self._img_pil.size
        self._zoom = min(cw / ow, ch / oh)
        self._render()

    def _save(self):
        path = filedialog.asksaveasfilename(
            title="Lưu sơ đồ",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("All files", "*.*")],
            initialfile="solution_table.png",
        )
        if path:
            self._img_pil.save(path, dpi=(150, 150))
            messagebox.showinfo("Đã lưu", f"Ảnh đã lưu:\n{path}")


# ===========================================================================
# Cửa sổ phụ – Nhật ký giải thuật từng bước
# ===========================================================================

class OptLogWindow(ctk.CTkToplevel):
    """Cửa sổ popup hiển thị nhật ký tối ưu hóa chi tiết."""

    def __init__(self, master, log_text: str):
        super().__init__(master)
        self.title("Nhật ký Tối ưu hóa – Chi tiết từng bước giải")
        self.geometry("760x500")
        self.resizable(True, True)
        self.grab_set()   # modal
        self.focus_set()

        self._log_text = log_text

        # ── Thanh tiêu đề ──────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=CLR_ACCENT, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="📋  Optimization Log",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(hdr, text="✕", width=32, height=28,
                      fg_color="transparent", hover_color="#1d4ed8",
                      text_color="white", font=ctk.CTkFont("Segoe UI", 14),
                      command=self.destroy).pack(side="right", padx=8, pady=8)

        # ── Vùng cuộn văn bản ──────────────────────────────────────────────
        frame_txt = ctk.CTkFrame(self, fg_color="#f1f5f9")
        frame_txt.pack(fill="both", expand=True, padx=12, pady=(10, 4))

        self._txt = tk.Text(frame_txt, wrap="none",
                            font=("Courier New", 10),
                            bg="#f8fafc", fg="#1e293b",
                            relief="flat", borderwidth=0,
                            selectbackground="#bfdbfe")
        self._txt.pack(side="left", fill="both", expand=True)

        sb_y = ttk.Scrollbar(frame_txt, orient="vertical",
                             command=self._txt.yview)
        sb_y.pack(side="right", fill="y")
        sb_x = ttk.Scrollbar(self, orient="horizontal",
                             command=self._txt.xview)
        sb_x.pack(fill="x", padx=12)
        self._txt.configure(yscrollcommand=sb_y.set,
                            xscrollcommand=sb_x.set)

        self._txt.insert("1.0", log_text if log_text else "(Chưa có nhật ký)")
        self._txt.configure(state="disabled")

        # ── Footer ─────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=8)

        ctk.CTkButton(footer, text="💾  Lưu Nhật Ký",
                      fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self._save_log).pack(side="right")

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            title="Lưu nhật ký",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            initialfile="optimization_log.txt",
        )
        if path:
            Path(path).write_text(self._log_text, encoding="utf-8")
            messagebox.showinfo("Đã lưu", f"Nhật ký đã được lưu:\n{path}")


# ===========================================================================
# Màn hình chính
# ===========================================================================

class TransportApp(ctk.CTk):
    """Giao diện chính – Bài toán vận tải."""

    # ── Trạng thái ──────────────────────────────────────────────────────────
    _C: Optional[np.ndarray]  = None
    _A: Optional[np.ndarray]  = None
    _B: Optional[np.ndarray]  = None
    _X_opt: Optional[np.ndarray] = None
    _basis_opt = None
    _cost_init: float = 0.0
    _cost_opt:  float = 0.0
    _iterations: int  = 0
    _log_text:  str   = ""
    _zoom: float = 1.0
    _img_pil: Optional[Image.Image] = None

    def __init__(self):
        super().__init__()

        self.title("Bài Toán Vận Tải – Thuật Toán Thế Vị")
        self.geometry("1150x750")
        self.minsize(900, 600)
        self.after(10, lambda: self.state("zoomed"))  # Maximize sau khi window hiển thị
        self.configure(fg_color="#e8eef7")

        # Thiết lập logging nội bộ (không ghi file)
        self._log_handler = _ListHandler()
        fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)-18s │ %(message)s",
                                datefmt="%H:%M:%S")
        self._log_handler.setFormatter(fmt)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self._log_handler)

        self._build_ui()

    # =========================================================================
    # XÂY DỰNG GIAO DIỆN
    # =========================================================================

    def _build_ui(self):
        # Chia màn hình: cột trái cố định 250px | cột phải mở rộng
        self.columnconfigure(0, minsize=250, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    # ── CỘT TRÁI ─────────────────────────────────────────────────────────────

    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color=CLR_LEFT_BG,
                            corner_radius=0, width=250)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        pad = dict(padx=18, pady=6)

        # ── Logo / tiêu đề ────────────────────────────────────────────────
        ctk.CTkLabel(left, text="CẤU HÌNH",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color="#e2e8f0").pack(anchor="w", padx=18, pady=(22, 4))

        sep0 = ctk.CTkFrame(left, height=1, fg_color="#334155")
        sep0.pack(fill="x", padx=18, pady=(0, 10))

        # ── Phần DỮ LIỆU ──────────────────────────────────────────────────
        ctk.CTkLabel(left, text="Dữ liệu",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#94a3b8").pack(anchor="w", **pad)

        # Dòng upload
        row_up = ctk.CTkFrame(left, fg_color="transparent")
        row_up.pack(fill="x", padx=18, pady=(2, 6))

        self._btn_upload = ctk.CTkButton(
            row_up,
            text="📁  Upload Excel",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color="#2d3748", hover_color="#4a5568",
            text_color="#e2e8f0",
            command=self._do_upload,
        )
        self._btn_upload.pack(side="left", expand=True, fill="x")

        # Đèn trạng thái
        self._status_dot = tk.Canvas(row_up, width=18, height=18,
                                     bg=CLR_LEFT_BG, highlightthickness=0)
        self._status_dot.pack(side="left", padx=(8, 0))
        self._dot_id = self._status_dot.create_oval(3, 3, 15, 15, fill="#4b5563")

        # Nhãn tên file đang nạp
        self._lbl_file = ctk.CTkLabel(left, text="Chưa chọn file",
                                       font=ctk.CTkFont("Segoe UI", 10),
                                       text_color="#64748b",
                                       wraplength=210, justify="left")
        self._lbl_file.pack(anchor="w", padx=18, pady=(0, 6))

        sep1 = ctk.CTkFrame(left, height=1, fg_color="#334155")
        sep1.pack(fill="x", padx=18, pady=(4, 8))

        # ── Phần TỰ SINH ──────────────────────────────────────────────────
        ctk.CTkLabel(left, text="Tự sinh",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#94a3b8").pack(anchor="w", **pad)

        # m và n – Entry nhập trực tiếp
        row_mn = ctk.CTkFrame(left, fg_color="transparent")
        row_mn.pack(fill="x", padx=18, pady=(0, 4))
        row_mn.columnconfigure(1, weight=1)
        row_mn.columnconfigure(3, weight=1)

        ctk.CTkLabel(row_mn, text="m =",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color="#cbd5e1", width=28
                     ).grid(row=0, column=0, sticky="w")
        self._m_entry = ctk.CTkEntry(
            row_mn, width=52,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="#2d3748", text_color="#e2e8f0",
            border_color="#4a5568",
            justify="center",
        )
        self._m_entry.insert(0, "3")
        self._m_entry.grid(row=0, column=1, sticky="w", padx=(2, 8))

        ctk.CTkLabel(row_mn, text="n =",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color="#cbd5e1", width=28
                     ).grid(row=0, column=2, sticky="w")
        self._n_entry = ctk.CTkEntry(
            row_mn, width=52,
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="#2d3748", text_color="#e2e8f0",
            border_color="#4a5568",
            justify="center",
        )
        self._n_entry.insert(0, "4")
        self._n_entry.grid(row=0, column=3, sticky="w", padx=(2, 0))

        ctk.CTkLabel(left, text="(m, n ∈ [2, 10])",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color="#475569").pack(anchor="w", padx=18, pady=(0, 4))

        # Lựa chọn suy biến
        ctk.CTkLabel(left, text="Kiểu bài toán:",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color="#cbd5e1").pack(anchor="w", padx=18, pady=(2, 2))

        self._degen_var = tk.IntVar(value=0)
        _rb_frame = ctk.CTkFrame(left, fg_color="transparent")
        _rb_frame.pack(anchor="w", padx=18, pady=(0, 4))
        ctk.CTkRadioButton(
            _rb_frame, text="Không suy biến",
            variable=self._degen_var, value=0,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color="#e2e8f0",
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
        ).pack(anchor="w", pady=(0, 2))
        ctk.CTkRadioButton(
            _rb_frame, text="Có suy biến",
            variable=self._degen_var, value=1,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color="#e2e8f0",
            fg_color="#7c3aed", hover_color="#6d28d9",
        ).pack(anchor="w")

        ctk.CTkButton(
            left, text="⚡  Generate",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="#374151", hover_color="#4b5563",
            text_color="#e2e8f0",
            command=self._do_generate,
        ).pack(fill="x", padx=18, pady=(6, 4))

        sep2 = ctk.CTkFrame(left, height=1, fg_color="#334155")
        sep2.pack(fill="x", padx=18, pady=(8, 8))

        # ── Phương pháp ───────────────────────────────────────────────────
        ctk.CTkLabel(left, text="Phương pháp",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#94a3b8").pack(anchor="w", **pad)

        self._method_var = tk.IntVar(value=1)
        ctk.CTkRadioButton(
            left, text="Cực tiểu Chi phí (Least Cost)",
            variable=self._method_var, value=1,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#e2e8f0",
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
        ).pack(anchor="w", padx=18, pady=(2, 4))
        ctk.CTkRadioButton(
            left, text="Góc Tây Bắc (Northwest Corner)",
            variable=self._method_var, value=2,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#e2e8f0",
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
        ).pack(anchor="w", padx=18, pady=(0, 8))

        sep3 = ctk.CTkFrame(left, height=1, fg_color="#334155")
        sep3.pack(fill="x", padx=18, pady=(4, 16))

        # ── Nút xem nhật ký ───────────────────────────────────────────────
        self._btn_log = ctk.CTkButton(
            left, text="📋  Xem Nhật Ký",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color="#374151", hover_color="#4b5563",
            text_color="#e2e8f0",
            state="disabled",
            command=self._show_log,
        )
        self._btn_log.pack(fill="x", padx=18, pady=(0, 8))

        # ── Nút GIẢI ─────────────────────────────────────────────────────
        self._btn_solve = ctk.CTkButton(
            left, text="▶  GIẢI BÀI TOÁN",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
            text_color="white",
            height=52,
            state="disabled",
            command=self._do_solve,
        )
        self._btn_solve.pack(fill="x", padx=18, pady=(0, 18), side="bottom")

    # ── CỘT PHẢI ─────────────────────────────────────────────────────────────

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color="#e8eef7", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=0)   # nghiệm X* – cố định, ĐẦU TIÊN
        right.rowconfigure(2, weight=1)   # Bảng ma trận giờ sẽ chiếm hết không gian còn lại
        right.rowconfigure(3, weight=0)   # Phần menu sơ đồ chỉ cao vừa đủ chứa nút
        right.columnconfigure(0, weight=1)

        # ── Hàng thống kê ─────────────────────────────────────────────────
        self._build_stats_row(right)

        # ── Nghiệm X* dạng văn bản – ĐẶT ĐẦU TIÊN ────────────────────────
        self._build_xstar_panel(right)

        # ── Bảng ma trận X* ───────────────────────────────────────────────
        self._build_table_panel(right)

        # ── Khung sơ đồ ảnh ───────────────────────────────────────────────
        self._build_diagram_panel(right)

    def _build_stats_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        row.columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("Tổng chi phí:",     "f(X*)",    "#1e40af"),
            ("Cải thiện:",        "–",         "#047857"),
            ("Vòng lặp:",         "–",         "#7c3aed"),
        ]
        self._stat_vals: list[ctk.CTkLabel] = []

        for idx, (label, init, color) in enumerate(cards):
            card = ctk.CTkFrame(row, fg_color="white",
                                corner_radius=12)
            card.grid(row=0, column=idx, sticky="ew",
                      padx=(0 if idx == 0 else 8, 0), pady=0)
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color="#64748b").pack(anchor="w", padx=16, pady=(12, 0))
            lv = ctk.CTkLabel(card, text=init,
                              font=ctk.CTkFont("Segoe UI", 30, "bold"),
                              text_color=color)
            lv.pack(anchor="w", padx=16, pady=(0, 12))
            self._stat_vals.append(lv)

    def _build_table_panel(self, parent):
        """Bảng Treeview hiển thị X* với ô cơ sở tô màu."""
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 6))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(frame,
                     text="Ma trận phân bổ hàng hóa tối ưu  X*",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#1e293b").grid(row=0, column=0,
                                                 sticky="w", padx=16, pady=(12, 4))

        # Treeview + scrollbars
        tv_frame = tk.Frame(frame, bg="white")
        tv_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        tv_frame.rowconfigure(0, weight=1)
        tv_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Trans.Treeview",
                        font=("Segoe UI", 11),
                        rowheight=28,
                        background="#f8fafc",
                        fieldbackground="#f8fafc")
        style.configure("Trans.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#dbeafe",
                        foreground="#1e40af")
        style.map("Trans.Treeview",
                  background=[("selected", "#bfdbfe")])

        self._tree = ttk.Treeview(tv_frame, style="Trans.Treeview",
                                   show="headings", selectmode="none")
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb_y = ttk.Scrollbar(tv_frame, orient="vertical",
                             command=self._tree.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(tv_frame, orient="horizontal",
                             command=self._tree.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self._tree.configure(yscrollcommand=sb_y.set,
                              xscrollcommand=sb_x.set)

        # Tag màu ô cơ sở
        self._tree.tag_configure("basis", background="#DBEAFE", foreground="#1e40af")
        self._tree.tag_configure("free",  background="#f8fafc", foreground="#374151")

        # Placeholder
        self._tree["columns"] = ("info",)
        self._tree.heading("info", text="(Chưa có kết quả)")
        self._tree.column("info", anchor="center", width=300)
        self._tree.insert("", "end", values=("Hãy tải dữ liệu và bấm Giải bài toán",),
                          tags=("free",))

    def _build_xstar_panel(self, parent):
        """Panel hiển thị nghiệm X* dạng văn bản – đặt ngay dưới stats cards."""
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        frame.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        hdr.columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr,
                     text="Nghiệm tối ưu X*  (các biến cơ sở)",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#1e293b").grid(row=0, column=0, sticky="w")

        # Text widget 3 dòng – cuộn ngang nếu nhiều biến
        txt_frame = tk.Frame(frame, bg="#f0f7ff")
        txt_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        txt_frame.columnconfigure(0, weight=1)

        self._xstar_text = tk.Text(
            txt_frame,
            height=3,
            wrap="none",
            font=("Consolas", 11),
            bg="#f0f7ff",
            fg="#1e40af",
            relief="flat",
            borderwidth=0,
            state="disabled",
        )
        self._xstar_text.grid(row=0, column=0, sticky="ew")

        sb_x2 = ttk.Scrollbar(txt_frame, orient="horizontal",
                               command=self._xstar_text.xview)
        sb_x2.grid(row=1, column=0, sticky="ew")
        self._xstar_text.configure(xscrollcommand=sb_x2.set)

        # Tag màu
        self._xstar_text.tag_configure("var",  foreground="#1e40af", font=("Consolas", 11, "bold"))
        self._xstar_text.tag_configure("eq",   foreground="#374151", font=("Consolas", 11))
        self._xstar_text.tag_configure("zero", foreground="#6366f1", font=("Consolas", 11, "italic"))

        # Placeholder
        self._xstar_text.configure(state="normal")
        self._xstar_text.insert("1.0", "(Chưa có nghiệm – hãy giải bài toán)")
        self._xstar_text.configure(state="disabled")

    def _build_diagram_panel(self, parent):
        """Khung chứa các nút thao tác với sơ đồ solution_table.png."""
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        frame.columnconfigure(0, weight=1)

        # ── Tiêu đề + Các nút thao tác ───────────────────────────────
        hdr_diag = ctk.CTkFrame(frame, fg_color="transparent")
        hdr_diag.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 10))
        hdr_diag.columnconfigure(0, weight=1)

        # Tiêu đề
        ctk.CTkLabel(hdr_diag,
                     text="Sơ đồ Bảng Vận Tải  (solution_table.png)",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color="#1e293b").grid(row=0, column=0, sticky="w", padx=4)

        # Cụm nút bấm
        btn_frame = ctk.CTkFrame(hdr_diag, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(btn_frame,
                      text="🔲  Mở cửa sổ riêng",
                      width=140, height=28,
                      fg_color="#e2e8f0", hover_color="#cbd5e1",
                      text_color="#1e293b",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._open_diagram_window,
                      ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_frame, text="💾  Lưu ảnh", width=110, height=28,
                      fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_HV,
                      text_color="white",
                      font=ctk.CTkFont("Segoe UI", 11),
                      command=self._save_image).pack(side="left")

    # =========================================================================
    # CÁC HÀNH ĐỘNG NGƯỜI DÙNG
    # =========================================================================


    # ── UPLOAD FILE ───────────────────────────────────────────────────────────
    def _do_upload(self):
        path = filedialog.askopenfilename(
            title="Chọn file Excel đầu vào",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        self._load_data(path)

    def _load_data(self, filepath: str):
        try:
            C, A, B = load_transportation_data(filepath)
        except FileNotFoundError as exc:
            self._set_status_error(f"File không tồn tại:\n{exc}")
            return
        except ValueError as exc:
            self._set_status_error(f"Dữ liệu không hợp lệ:\n{exc}")
            return
        except Exception as exc:
            self._set_status_error(f"Lỗi không xác định:\n{exc}")
            return

        self._C, self._A, self._B = C, A, B
        m, n = C.shape
        self._set_status_ok()
        short = Path(filepath).name
        self._lbl_file.configure(
            text=f"{short}\n{m} trạm phát × {n} trạm thu | Tổng: {np.sum(A):.4g}"
        )
        self._btn_solve.configure(state="normal")

    # ── GENERATE DỮ LIỆU MẪU ─────────────────────────────────────────────────
    def _parse_mn(self):
        """Đọc và xác thực m, n từ Entry. Trả về (m, n) hoặc None nếu lỗi."""
        try:
            m = int(self._m_entry.get().strip())
            n = int(self._n_entry.get().strip())
        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "m và n phải là số nguyên.")
            return None
        if not (2 <= m <= 10 and 2 <= n <= 10):
            messagebox.showerror("Lỗi nhập liệu",
                                 f"m và n phải nằm trong khoảng [2, 10].\n"
                                 f"Giá trị nhập: m={m}, n={n}")
            return None
        return m, n

    def _do_generate(self):
        parsed = self._parse_mn()
        if parsed is None:
            return
        m, n = parsed
        want_degen = (self._degen_var.get() == 1)
        rng = np.random.default_rng()

        # Ma trận cước phí ngẫu nhiên 1–19
        C = rng.integers(1, 20, (m, n)).astype(float)

        if not want_degen:
            # ── Không suy biến ────────────────────────────────────────────
            # Đảm bảo không có aᵢ = bⱼ nào trùng nhau để tránh suy biến
            # Cách: tạo A ngẫu nhiên, rồi chia đều B ≈ sum(A)/n với nhiễu nhỏ
            A = rng.integers(8, 25, m).astype(float)
            total = float(A.sum())
            # B chia đều + nhiễu lẻ, đảm bảo không có bⱼ = aᵢ nào
            base = total / n
            B = np.array([base + rng.uniform(-base * 0.3, base * 0.3)
                          for _ in range(n)])
            B = np.round(B).clip(1)
            # Hiệu chỉnh để cân bằng tổng chính xác
            diff = total - B.sum()
            B[-1] += diff
            # Nếu vô tình bⱼ[-1] ≤ 0 thì điều chỉnh lại
            if B[-1] <= 0:
                B[-1] = 1
                B[0] += diff - (B[-1] - 1)
            name = f"{m}x{n}_nodegen"
        else:
            # ── Có suy biến ───────────────────────────────────────────────
            # Tạo suy biến: đặt aᵢ[0] = bⱼ[0] (supply dòng 1 = demand cột 1)
            # → khi chạy phương pháp xuất phát, ô (0,0) bị triệt tiêu đồng thời
            #   cả hàng 0 lẫn cột 0 → tập cơ sở bị suy biến
            A = rng.integers(6, 20, m).astype(float)
            B = rng.integers(6, 20, n).astype(float)
            shared_val = float(rng.integers(5, min(int(A.min()), int(B.min())) + 1))
            A[0] = shared_val          # a₁ = borrow value
            B[0] = shared_val          # b₁ = cùng giá trị → suy biến khi giao nhau
            # Cân bằng thu phát: điều chỉnh B[-1]
            diff = A.sum() - B.sum()
            B[-1] = max(1, B[-1] + diff)
            # Nếu vẫn chưa bằng (B[-1] đổi làm mất cân bằng) → lặp lại
            B[-1] += A.sum() - B.sum()
            name = f"{m}x{n}_degen"

        out = str(_ROOT / "data_and_results" / "input_data.xlsx")
        try:
            create_excel(C, A, B, output_path=out)
        except Exception as exc:
            messagebox.showerror("Lỗi sinh dữ liệu", str(exc))
            return

        self._C, self._A, self._B = C, A, B
        self._set_status_ok()
        degen_txt = "(có suy biến)" if want_degen else "(không suy biến)"
        self._lbl_file.configure(
            text=f"(Tự sinh) {name} {degen_txt}\n"
                 f"{m} trạm phát × {n} trạm thu | Tổng: {np.sum(A):.4g}"
        )
        self._btn_solve.configure(state="normal")
        messagebox.showinfo("Tự sinh thành công",
                            f"Đã tạo file: input_data.xlsx\n"
                            f"Kích thước: {m} × {n}  {degen_txt}\n"
                            f"Tổng: {np.sum(A):.4g}")

    # ── GIẢI BÀI TOÁN ─────────────────────────────────────────────────────────
    def _do_solve(self):
        if self._C is None:
            messagebox.showwarning("Chưa có dữ liệu",
                                   "Hãy tải file Excel hoặc tự sinh dữ liệu trước.")
            return

        # Vô hiệu hóa nút tránh nhấn nhiều lần
        self._btn_solve.configure(state="disabled", text="⏳  Đang giải...")
        self._btn_log.configure(state="disabled")
        self.update_idletasks()

        # Chạy trong thread nền để không đóng băng UI
        threading.Thread(target=self._solve_thread, daemon=True).start()

    def _solve_thread(self):
        """Thực hiện toàn bộ pipeline giải toán (chạy nền)."""
        self._log_handler.clear()
        log = logging.getLogger("ui_solver")

        C, A, B = self._C, self._A, self._B
        m, n = C.shape
        method_id = self._method_var.get()

        try:
            # Giai đoạn 1 – Phương án cực biên ban đầu
            if method_id == 2:
                method_name = "Góc Tây Bắc"
                log.info(f"[BƯỚC 2] Phương pháp Góc Tây Bắc ({m}×{n})...")
                X_init, basis_init = northwest_corner_method(C, A, B)
            else:
                method_name = "Cực tiểu Chi phí"
                log.info(f"[BƯỚC 2] Phương pháp Cực tiểu Chi phí ({m}×{n})...")
                X_init, basis_init = least_cost_method(C, A, B)

            cost_init = float(np.sum(C * X_init))
            log.info(f"         Chi phí ban đầu = {cost_init:.6g}")

            # Giai đoạn 2 – Tối ưu hóa
            log.info("[BƯỚC 3] Tối ưu hóa Thuật toán Thế vị...")
            X_opt, basis_opt, cost_opt, iterations = optimize(
                C=C, X_init=X_init, basis_init=basis_init,
                A=A, B=B, max_iterations=1000,
            )
            log.info(f"         Chi phí tối ưu = {cost_opt:.6g}  |  Vòng lặp = {iterations}")

            # Giai đoạn 3 – Trực quan hóa
            log.info("[BƯỚC 5] Xuất sơ đồ solution_table.png...")
            png_path = str(_ROOT / "data_and_results" / "solution_table.png")
            plot_solution_table(
                C=C, X=X_opt, A=A, B=B,
                basis=basis_opt,
                total_cost=cost_opt,
                output_path=png_path,
                title="Phương án vận tải tối ưu",
                init_method_name=method_name,
            )

            # Lưu kết quả
            self._X_opt     = X_opt
            self._basis_opt = basis_opt
            self._cost_init = cost_init
            self._cost_opt  = cost_opt
            self._iterations = iterations
            self._log_text  = self._log_handler.get_text()

            # Cập nhật UI trên main thread
            self.after(0, lambda: self._update_results(
                C, A, B, X_opt, basis_opt, cost_init, cost_opt, iterations, png_path
            ))

        except Exception as exc:
            self._log_text = self._log_handler.get_text()
            err = str(exc)
            self.after(0, lambda: self._on_solve_error(err))

    def _on_solve_error(self, err: str):
        self._btn_solve.configure(state="normal", text="▶  GIẢI BÀI TOÁN")
        messagebox.showerror("Lỗi giải toán", err)

    # ── CẬP NHẬT GIAO DIỆN SAU KHI GIẢI XONG ─────────────────────────────────
    def _update_results(self, C, A, B, X_opt, basis_opt,
                        cost_init, cost_opt, iterations, png_path):
        m, n = C.shape

        # Cards thống kê
        self._stat_vals[0].configure(text=f"{cost_opt:.6g}")
        if cost_init > 1e-9:
            pct = (cost_init - cost_opt) / cost_init * 100
            self._stat_vals[1].configure(text=f"{pct:.2f}%")
        else:
            self._stat_vals[1].configure(text="–")
        self._stat_vals[2].configure(text=str(iterations))

        # Bảng X*
        self._fill_table(C, A, B, X_opt, basis_opt, m, n)

        # Nghiệm X* dạng văn bản
        self._fill_xstar_text(X_opt, basis_opt, cost_opt, m, n)

        # Ảnh sơ đồ
        self._load_diagram(png_path)

        # Mở khóa nút
        self._btn_solve.configure(state="normal", text="▶  GIẢI BÀI TOÁN")
        self._btn_log.configure(state="normal")

    # ── ĐIỀN NGHIỆM X* DẠNG VĂN BẢN ─────────────────────────────────────────
    def _fill_xstar_text(self, X_opt, basis_opt, cost_opt, m, n):
        """Hiển thị danh sách biến cơ sở: x_{i,j} = val, ..."""
        txt = self._xstar_text
        txt.configure(state="normal")
        txt.delete("1.0", "end")

        # Dòng 1: liệt kê từng xᵢⱼ cơ sở
        basis_sorted = sorted(basis_opt, key=lambda ij: (ij[0], ij[1]))
        parts = []
        for (i, j) in basis_sorted:
            val = X_opt[i, j]
            subscript = f"x({i+1},{j+1})"
            if val < 1e-9:
                parts.append((subscript, "= 0", True))   # suy biến
            else:
                parts.append((subscript, f"= {val:.4g}", False))

        # Dòng 1: các biến
        txt.insert("end", "Cơ sở tối ưu:  ", "eq")
        for k, (sub, eq_str, is_zero) in enumerate(parts):
            txt.insert("end", sub, "var" if not is_zero else "zero")
            txt.insert("end", f" {eq_str}", "eq" if not is_zero else "zero")
            if k < len(parts) - 1:
                txt.insert("end", "  │  ", "eq")
        txt.insert("end", "\n")

        # Dòng 2: hàm mục tiêu
        txt.insert("end", f"f(X*) = {cost_opt:.6g}  ", "var")
        txt.insert("end", f"   (|cơ sở| = {len(basis_sorted)} = m+n−1 = {m+n-1})", "eq")
        txt.insert("end", "\n")

        # Dòng 3: kiểm tra suy biến
        degen_count = sum(1 for (i, j) in basis_sorted if X_opt[i, j] < 1e-9)
        if degen_count > 0:
            txt.insert("end",
                       f"⚠ Suy biến: {degen_count} ô cơ sở có xᵢⱼ = 0  "
                       "(epsilon-perturbation được áp dụng)",
                       "zero")
        else:
            txt.insert("end", "✓ Không suy biến – tất cả ô cơ sở có xᵢⱼ > 0", "eq")

        txt.configure(state="disabled")

    # ── ĐỔ DỮ LIỆU VÀO BẢNG X* ──────────────────────────────────────────────
    def _fill_table(self, C, A, B, X_opt, basis_opt, m, n):
        tree = self._tree
        tree.delete(*tree.get_children())

        # Cột: Trạm phát | T1 | T2 | ... | Tn | aᵢ
        cols = ["Trạm phát"] + [f"T{j+1}" for j in range(n)] + ["aᵢ"]
        tree["columns"] = cols
        tree.column("Trạm phát", width=90, anchor="center")
        for j in range(n):
            tree.column(f"T{j+1}", width=75, anchor="center")
        tree.column("aᵢ", width=60, anchor="center")

        tree.heading("Trạm phát", text="Trạm phát")
        for j in range(n):
            tree.heading(f"T{j+1}", text=f"T{j+1}")
        tree.heading("aᵢ", text="aᵢ")

        # Dữ liệu hàng (mỗi hàng = một trạm phát Pᵢ)
        # Hiển thị: [Pᵢ | x*ᵢⱼ (với * nếu cơ sở) | aᵢ]
        for i in range(m):
            row_vals = [f"P{i+1}"]
            is_basis_row = []
            for j in range(n):
                val = X_opt[i, j]
                in_basis = (i, j) in basis_opt
                is_basis_row.append(in_basis)
                if in_basis:
                    s = f"{val:.4g}*" if val > 1e-9 else "0*"
                else:
                    s = "" if val < 1e-9 else f"{val:.4g}"
                row_vals.append(s)
            row_vals.append(f"{A[i]:.4g}")

            # Nếu hàng có ít nhất một ô cơ sở → dùng tag "basis" cho toàn hàng
            tag = "basis" if any(is_basis_row) else "free"
            tree.insert("", "end", values=row_vals, tags=(tag,))

        # Hàng bⱼ cuối
        bj_row = ["bⱼ"] + [f"{B[j]:.4g}" for j in range(n)] + [f"{np.sum(A):.4g}"]
        tree.insert("", "end", values=bj_row, tags=("free",))

    # ── TẢI ẢNH SƠ ĐỒ ───────────────────────────────────────────────────────
    def _load_diagram(self, png_path: str):
        """Chỉ nạp ảnh vào bộ nhớ để phục vụ nút Save và Mở cửa sổ riêng."""
        try:
            self._img_pil = Image.open(png_path)
        except Exception as exc:
            messagebox.showwarning("Không thể nạp ảnh", str(exc))

    # ── LƯU ẢNH ──────────────────────────────────────────────────────────────
    def _save_image(self):
        if self._img_pil is None:
            messagebox.showwarning("Chưa có ảnh", "Hãy giải bài toán trước để tạo sơ đồ.")
            return
        path = filedialog.asksaveasfilename(
            title="Lưu sơ đồ bảng vận tải",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("All files", "*.*")],
            initialfile="solution_table.png",
        )
        if path:
            self._img_pil.save(path, dpi=(150, 150))
            messagebox.showinfo("Đã lưu", f"Ảnh đã được lưu:\n{path}")

    # ── MỞ SƠ ĐỒ TRONG CỬA SỔ RIÊNG ─────────────────────────────────────────
    def _open_diagram_window(self):
        if self._img_pil is None:
            messagebox.showwarning("Chưa có sơ đồ",
                                   "Hãy giải bài toán trước để tạo sơ đồ.")
            return
        DiagramWindow(self, self._img_pil)

    # ── HIỆN CỬA SỔ LOG ───────────────────────────────────────────────────────
    def _show_log(self):
        log_path = _ROOT / "data_and_results" / "optimization_log.txt"
        log_text = self._log_text

        # Cố gắng đọc thêm từ file log chi tiết nếu có
        if log_path.exists():
            try:
                extra = log_path.read_text(encoding="utf-8")
                if extra:
                    log_text = extra
            except Exception:
                pass

        OptLogWindow(self, log_text)

    # ── ĐÈN TRẠNG THÁI ───────────────────────────────────────────────────────
    def _set_status_ok(self):
        self._status_dot.itemconfig(self._dot_id, fill=CLR_OK)

    def _set_status_error(self, msg: str):
        self._status_dot.itemconfig(self._dot_id, fill=CLR_ERR)
        messagebox.showerror("Lỗi đọc dữ liệu", msg)


# ===========================================================================
# Entry point
# ===========================================================================

def main():
    app = TransportApp()
    app.mainloop()


if __name__ == "__main__":
    main()
