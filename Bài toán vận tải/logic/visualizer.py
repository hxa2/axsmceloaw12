"""
Module: visualizer.py
======================
Trực quan hóa kết quả bài toán vận tải bằng Matplotlib.

Cung cấp hai loại biểu đồ xuất ra file PNG riêng biệt:

  1. plot_solution_table()
     ─ Bảng ma trận kết quả (m+2 hàng × n+2 cột).
     ─ Mỗi ô hiển thị: c_ij (cước phí) ở góc trên, x_ij* (luồng) ở trung tâm.
     ─ Ô cơ sở được tô màu khác; hàng/cột marginal được tô màu riêng.

"""

import logging
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np

# Dùng backend không cần GUI – bắt buộc khi chạy không có màn hình
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D

from logic.initial_solution import BasisSet

logger = logging.getLogger(__name__)

# ===========================================================================
# Bảng màu thống nhất toàn module
# ===========================================================================
_C = {
    # Màu ô trong bảng
    "cell_basis"      : "#D6EAF8",   # Xanh nhạt   – ô cơ sở
    "cell_free"       : "#FDFEFE",   # Trắng        – ô loại
    "cell_supply_hdr" : "#D5F5E3",   # Xanh lá nhạt – cột lượng phát
    "cell_demand_hdr" : "#FAD7A0",   # Cam nhạt      – hàng lượng thu
    "cell_corner"     : "#F9E79F",   # Vàng nhạt     – ô tổng góc
    "cell_row_hdr"    : "#2C3E50",   # Xanh đen      – header hàng/cột
    "text_header"     : "white",

    # Màu cạnh đồ thị
    "edge_active"     : "#1A5276",   # Xanh đậm  – cạnh luồng > 0
    "edge_degen"      : "#5DADE2",   # Xanh giữa – ô cơ sở suy biến (x=0)
    "edge_inactive"   : "#D5D8DC",   # Xám nhạt  – cạnh không có luồng

    # Màu node đồ thị
    "node_source"     : "#1ABC9C",   # Xanh ngọc – trạm phát
    "node_sink"       : "#E74C3C",   # Đỏ        – trạm thu
    "node_text"       : "white",
}

_NODE_RADIUS = 0.28   # Bán kính node (đơn vị data)
_EPS         = 1e-9


# ===========================================================================
# 1. Bảng ma trận kết quả
# ===========================================================================

def _compute_potentials_viz(C, basis, m, n):
    """Tính thế vị u_i, v_j với u[0]=0 từ tập cơ sở."""
    u = [None] * m
    v = [None] * n
    u[0] = 0.0
    changed = True
    while changed:
        changed = False
        for (i, j) in basis:
            if u[i] is not None and v[j] is None:
                v[j] = float(C[i, j]) - u[i]; changed = True
            elif v[j] is not None and u[i] is None:
                u[i] = float(C[i, j]) - v[j]; changed = True
    for i in range(m):
        if u[i] is None: u[i] = 0.0
    for j in range(n):
        if v[j] is None: v[j] = 0.0
    return u, v


def plot_solution_table(
    C: np.ndarray,
    X: np.ndarray,
    A: np.ndarray,
    B: np.ndarray,
    basis: BasisSet,
    total_cost: float,
    output_path: str,
    title: str = "Phương án vận tải tối ưu",
    init_method_name: str = "",
) -> None:
    """
    Vẽ bảng vận tải theo dạng chuẩn giáo khoa:
      - Hàng đầu: thế vị v_j và lượng thu b_j
      - Cột đầu:  thế vị u_i và lượng phát a_i
      - Mỗi ô (i,j): c_ij (nhỏ, góc trên-trái) + x_ij/Δ_ij (lớn, góc dưới-phải)

    Parameters
    ----------
    C, X        : np.ndarray        Ma trận cước phí và phương án tối ưu.
    A, B        : np.ndarray        Vectơ lượng phát / lượng thu.
    basis       : BasisSet          Tập ô cơ sở tối ưu.
    total_cost  : float             Tổng chi phí tối ưu f(X*).
    output_path : str               Đường dẫn file PNG đầu ra.
    title       : str               Tiêu đề biểu đồ.
    """
    m, n = C.shape

    # ── Tính thế vị và delta ─────────────────────────────────────────────
    u, v = _compute_potentials_viz(C, basis, m, n)
    delta = [[u[i] + v[j] - C[i, j] for j in range(n)] for i in range(m)]

    # ── Kích thước ô (đơn vị: inch-like data coords) ─────────────────────
    CW = 2.0      # chiều rộng ô dữ liệu
    CH = 1.6      # chiều cao ô dữ liệu
    LW = 1.4      # chiều rộng cột lề trái (u_i / a_i)
    TH = 0.8      # chiều cao hàng lề trên (v_j / b_j)

    # Tổng số hàng / cột kể cả header + footer:
    #   cột: [u_i | a_i | data cols x n | a_i-repeat]
    #   hàng: [v_j | b_j | data rows x m | b_j-footer]
    total_w = LW + LW + n * CW + LW
    total_h = TH + TH + m * CH + TH   # +TH cho footer b_j

    fig_w = max(10, total_w * 0.85 + 1.5)
    fig_h = max(6,  total_h * 0.85 + 2.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.invert_yaxis()   # hàng 0 ở trên cùng

    # ── Màu sắc ───────────────────────────────────────────────────────────
    CLR_BASIS   = "#D6EAF8"   # xanh nhạt – ô cơ sở
    CLR_FREE    = "#FDFEFE"   # trắng     – ô không cơ sở
    CLR_HDR_BG  = "#ECF0F1"   # xám rất nhạt – header v_j / u_i
    CLR_BJ_BG   = "#FAD7A0"   # cam nhạt – b_j
    CLR_AI_BG   = "#D5F5E3"   # xanh lá nhạt – a_i
    CLR_CORNER  = "#F9E79F"   # vàng – ô góc

    def cell_x(col: int) -> float:
        """Tọa độ x bên trái ô cột col (0=u_i, 1=a_i, 2..n+1=data, n+2=a_i)."""
        if col == 0: return 0.0
        if col == 1: return LW
        if col <= n + 1: return LW + LW + (col - 2) * CW
        return LW + LW + n * CW

    def cell_y(row: int) -> float:
        """Tọa độ y trên cùng ô hàng row (0=v_j, 1=b_j, 2..m+1=data, m+2=b_j footer)."""
        if row == 0: return 0.0
        if row == 1: return TH
        if row <= m + 1: return TH + TH + (row - 2) * CH
        return TH + TH + m * CH   # footer b_j

    def cw(col: int) -> float:
        if col in (0, 1, n + 2): return LW
        return CW

    def ch(row: int) -> float:
        if row in (0, 1, m + 2): return TH   # footer cũng cao = TH
        return CH

    def draw_rect(col, row, facecolor, edgecolor="#999999", lw=0.8):
        x0, y0 = cell_x(col), cell_y(row)
        w, h   = cw(col), ch(row)
        rect = plt.Rectangle(
            (x0, y0), w, h,
            facecolor=facecolor, edgecolor=edgecolor,
            linewidth=lw, clip_on=False,
        )
        ax.add_patch(rect)
        return x0, y0, w, h

    def draw_text(x, y, text, **kwargs):
        ax.text(x, y, text, clip_on=False, **kwargs)

    # ── Vẽ từng ô ─────────────────────────────────────────────────────────

    # Hàng 0: v_j (thế vị)
    # Ô góc trên-trái — chiếm 2 cột × 2 hàng
    # Bố cục theo phác thảo người dùng:
    #   - Đường chéo từ góc TRÊN-TRÁI → DƯỚI-PHẢI
    #   - vⱼ* : góc trên-phải (trên đường chéo)
    #   - bⱼ  : giữa-phải (dưới đường chéo, sát cạnh phải)
    #   - uᵢ  : góc dưới-trái (dưới đường chéo)
    #   - aᵢ  : góc dưới-phải (dưới đường chéo, khớp cột aᵢ)
    x0, y0 = 0.0, 0.0
    corner_w = LW + LW          # = 2 × LW
    corner_h = TH + TH          # = 2 × TH
    ax.add_patch(plt.Rectangle((x0, y0), corner_w, corner_h,
        facecolor=CLR_CORNER, edgecolor="#999999", linewidth=0.8, clip_on=False))
    # Đường chéo từ góc trên-trái → dưới-phải (y0 nhỏ = trên, y0+corner_h = dưới)
    ax.plot([x0, x0 + corner_w], [y0, y0 + corner_h],
            color="#999999", linewidth=0.8, clip_on=False)
    # vⱼ* — góc trên-phải (trên đường chéo)
    draw_text(x0 + corner_w - 0.10, y0 + 0.10, "vⱼ",
              fontsize=10, ha="right", va="top",
              color="#1A5276", style="italic", fontweight="bold")
    # bⱼ — giữa-phải, phía dưới đường chéo
    draw_text(x0 + corner_w - 0.12, y0 + corner_h * 0.75, "bⱼ",
              fontsize=10, ha="right", va="center",
              color="#555555", style="italic", fontweight="bold")
    # uᵢ — góc dưới-trái (dưới đường chéo, khớp cột uᵢ)
    draw_text(x0 + 0.12, y0 + corner_h - 0.12, "uᵢ",
              fontsize=11, ha="left", va="bottom",
              color="#555555", style="italic", fontweight="bold")
    # aᵢ — góc dưới-phải (dưới đường chéo, khớp cột aᵢ)
    draw_text(x0 + corner_w - 0.60, y0 + corner_h - 0.12, "aᵢ",
              fontsize=11, ha="right", va="bottom",
              color="#555555", style="italic", fontweight="bold")
    # Hàng v_j
    for j in range(n):
        col = j + 2
        x0r, y0r, wr, hr = draw_rect(col, 0, CLR_HDR_BG, lw=1.0)
        vj_s = _fmt(v[j])
        draw_text(x0r + wr/2, y0r + hr/2, vj_s,
                  fontsize=12, ha="center", va="center",
                  fontweight="bold", color="#1A5276")
    # Cột a_i header
    draw_rect(n + 2, 0, CLR_AI_BG, lw=1.0)

    # Hàng 1: b_j (lượng thu)
    for j in range(n):
        col = j + 2
        x0r, y0r, wr, hr = draw_rect(col, 1, CLR_BJ_BG, lw=1.0)
        bj_s = _fmt(B[j])
        draw_text(x0r + wr/2, y0r + hr/2, bj_s,
                  fontsize=13, ha="center", va="center", fontweight="bold")
    # "a_i" label header
    x0r, y0r, wr, hr = draw_rect(n + 2, 1, CLR_AI_BG, lw=1.0)
    draw_text(x0r + wr/2, y0r + hr/2, "aᵢ",
              fontsize=10, ha="center", va="center", color="#555555", style="italic")

    # Hàng dữ liệu 2..m+1
    for i in range(m):
        row = i + 2

        # Cột 0: u_i
        x0r, y0r, wr, hr = draw_rect(0, row, CLR_HDR_BG, lw=1.0)
        ui_s = _fmt(u[i])
        draw_text(x0r + wr/2, y0r + hr/2, ui_s,
                  fontsize=12, ha="center", va="center",
                  fontweight="bold", color="#1A5276")

        # Cột 1: a_i
        x0r, y0r, wr, hr = draw_rect(1, row, CLR_AI_BG, lw=1.0)
        ai_s = _fmt(A[i])
        draw_text(x0r + wr/2, y0r + hr/2, ai_s,
                  fontsize=13, ha="center", va="center", fontweight="bold")

        # Ô dữ liệu (i, j)
        for j in range(n):
            col = j + 2
            is_basis = (i, j) in basis
            bg = CLR_BASIS if is_basis else CLR_FREE
            x0r, y0r, wr, hr = draw_rect(col, row, bg, lw=0.8)

            pad = 0.13

            # c_ij – góc trên-trái, nhỏ
            draw_text(x0r + pad, y0r + pad,
                      _fmt(C[i, j]),
                      fontsize=10, ha="left", va="top",
                      color="#555555")

            # x_ij hoặc Δ_ij – góc dưới-phải
            if is_basis:
                flow = X[i, j]
                if flow > _EPS:
                    draw_text(x0r + wr - pad, y0r + hr - pad,
                              _fmt(flow),
                              fontsize=14, ha="right", va="bottom",
                              fontweight="bold", color="#154360")
                else:
                    # Ô cơ sở suy biến (x=0)
                    draw_text(x0r + wr - pad, y0r + hr - pad,
                              "0*",
                              fontsize=12, ha="right", va="bottom",
                              fontweight="bold", color="#5DADE2")
            else:
                dij = delta[i][j]
                dij_s = _fmt(dij)
                clr = "#CB4335" if dij > _EPS else "#7F8C8D"
                draw_text(x0r + wr - pad, y0r + hr - pad,
                          dij_s,
                          fontsize=11, ha="right", va="bottom",
                          style="italic", color=clr)

        # Cột n+2: a_i (lặp lại bên phải)
        x0r, y0r, wr, hr = draw_rect(n + 2, row, CLR_AI_BG, lw=1.0)
        draw_text(x0r + wr/2, y0r + hr/2, ai_s,
                  fontsize=13, ha="center", va="center", fontweight="bold")

    # ── Hàng footer b_j (cuối bảng) ────────────────────────────────────────
    footer_row = m + 2
    # Ô góc cuối (2 cột đầu gộp lại)
    foot_x = 0.0
    foot_y = cell_y(footer_row)
    ax.add_patch(plt.Rectangle((foot_x, foot_y), LW + LW, TH,
        facecolor=CLR_BJ_BG, edgecolor="#999999", linewidth=1.0, clip_on=False))
    draw_text(foot_x + (LW + LW) / 2, foot_y + TH / 2, "bⱼ",
              fontsize=11, ha="center", va="center",
              color="#7D3C98", fontweight="bold", style="italic")
    # Các ô b_j
    for j in range(n):
        col = j + 2
        x0r, y0r, wr, hr = draw_rect(col, footer_row, CLR_BJ_BG, lw=1.0)
        draw_text(x0r + wr/2, y0r + hr/2, _fmt(B[j]),
                  fontsize=13, ha="center", va="center", fontweight="bold")
    # Ô tổng góc cuối
    x0r, y0r, wr, hr = draw_rect(n + 2, footer_row, "#F9E79F", lw=1.0)
    draw_text(x0r + wr/2, y0r + hr/2,
              f"Tổng\n{_fmt(float(np.sum(A)))}",
              fontsize=10, ha="center", va="center", fontweight="bold")

    # ── Đường kẻ ngoài viền ──────────────────────────────────────────────
    outer_h_full = TH + TH + m * CH + TH
    ax.add_patch(plt.Rectangle((0, 0), total_w, outer_h_full,
        fill=False, edgecolor="#333333", linewidth=1.8, clip_on=False))
    ax.set_ylim(outer_h_full, -0.05)

    # ── Chú thích ─────────────────────────────────────────────────────────
    legend_patches = [
        mpatches.Patch(facecolor=CLR_BASIS,  edgecolor="#999999",
                       label="Ô cơ sở (xᵢⱼ)"),
        mpatches.Patch(facecolor=CLR_FREE,   edgecolor="#999999",
                       label="Ô không cơ sở (Δᵢⱼ)"),
        mpatches.Patch(facecolor=CLR_AI_BG,  edgecolor="#999999",
                       label="Lượng phát aᵢ"),
        mpatches.Patch(facecolor=CLR_BJ_BG,  edgecolor="#999999",
                       label="Lượng thu bⱼ"),
        mpatches.Patch(facecolor=CLR_HDR_BG, edgecolor="#999999",
                       label="Thế vị uᵢ / vⱼ"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=3,
        fontsize=8,
        framealpha=0.9,
    )

    # ── Tiêu đề ───────────────────────────────────────────────────────────
    subtitle_parts = [f"Tổng chi phí tối ưu: f(X*) = {total_cost:.6g}"]
    if init_method_name:
        subtitle_parts.append(
            f"Phương pháp xuất phát: {init_method_name}"
        )
    fig.suptitle(
        f"{title}\n" + "  |  ".join(subtitle_parts),
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    _save_fig(fig, output_path, "bang ket qua")

# ===========================================================================
# Các hàm hỗ trợ nội bộ
# ===========================================================================

def _node_positions(
    count: int,
    x: float,
    total: int,
) -> List[Tuple[float, float]]:
    """
    Tính vị trí (x, y) cho `count` node phân bố đều theo trục dọc.

    Các node được căn giữa trong khoảng [0, total−1] để cả hai bên
    (phát và thu) đều được căn chỉnh nhất quán.

    Parameters
    ----------
    count : int     Số node cần xếp.
    x     : float   Tọa độ x cố định.
    total : int     Tổng chiều cao chia sẻ (= max(m, n)).

    Returns
    -------
    list of (x, y)
    """
    if count == 1:
        # Node duy nhất → đặt ở giữa
        return [(x, (total - 1) / 2.0)]

    # Khoảng cách giữa các node
    span  = total - 1
    step  = span / (count - 1)
    start = 0.0
    return [(x, start + k * step) for k in range(count)]


def _draw_node(
    ax: plt.Axes,
    cx: float,
    cy: float,
    radius: float,
    face_color: str,
    label: str,
    fontsize: float = 8.0,
) -> None:
    """
    Vẽ node hình tròn tại (cx, cy) với nhãn văn bản ở trung tâm.

    Node gồm:
        - Hình tròn nền màu face_color với viền trắng mỏng.
        - Văn bản trắng đậm ở giữa.
    """
    # Viền trắng phía dưới (để tạo hiệu ứng outline nhẹ)
    border = plt.Circle(
        (cx, cy), radius + 0.015,
        color="white", zorder=4,
    )
    ax.add_patch(border)

    # Hình tròn chính
    circle = plt.Circle(
        (cx, cy), radius,
        color=face_color, zorder=5,
    )
    ax.add_patch(circle)

    # Nhãn văn bản
    ax.text(
        cx, cy, label,
        fontsize=fontsize,
        ha="center", va="center",
        color=_C["node_text"],
        fontweight="bold",
        zorder=6,
        multialignment="center",
    )


def _fmt(value: float) -> str:
    """
    Định dạng số thực cho hiển thị gọn.
    - Nếu gần số nguyên → hiển thị không có phần thập phân.
    - Ngược lại → tối đa 4 chữ số có nghĩa.
    """
    if abs(value - round(value)) < _EPS:
        return str(int(round(value)))
    return f"{value:.4g}"


def _save_fig(fig: plt.Figure, output_path: str, desc: str) -> None:
    """
    Lưu figure ra file PNG và giải phóng bộ nhớ.

    Parameters
    ----------
    fig         : Figure    Figure cần lưu.
    output_path : str       Đường dẫn file đích.
    desc        : str       Mô tả ngắn để ghi log.
    """
    # Tạo thư mục đích nếu chưa tồn tại
    os.makedirs(Path(output_path).parent, exist_ok=True)

    fig.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    logger.info(f"Đã lưu {desc} → {output_path}")
