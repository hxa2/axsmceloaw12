"""
backend/app/services/export_service.py
========================================
Service tạo visualization (PNG) từ kết quả giải bài toán vận tải.

Dùng matplotlib để vẽ bảng kết quả.
Trả bytes PNG để API trả về, không ghi file trực tiếp.
"""

import io
import logging
from typing import Optional

import numpy as np

from backend.core.algorithms.initial_solution._basis import BasisSet
from backend.core.models.solution import TransportationSolution

logger = logging.getLogger(__name__)

_EPS = 1e-9


class ExportService:
    """
    Service xuất kết quả bài toán vận tải ra PNG.

    Tách từ visualizer.py cũ: không ghi file trực tiếp,
    trả bytes thay vì path.
    """

    def render_solution_table(
        self,
        cost_matrix: list[list[float]],
        solution: TransportationSolution,
        supply: list[float],
        demand: list[float],
        title: str = "Phương án vận tải tối ưu",
    ) -> bytes:
        """
        Render bảng kết quả vận tải sang PNG bytes.

        Returns
        -------
        bytes  Nội dung file PNG.
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            raise RuntimeError("matplotlib không được cài đặt. Chạy: pip install matplotlib")

        C = np.array(cost_matrix, dtype=float)
        X = np.array(solution.allocation_matrix, dtype=float)
        A = np.array(supply, dtype=float)
        B = np.array(demand, dtype=float)
        m, n = C.shape

        # Tập ô cơ sở
        basis = BasisSet()
        for cell in solution.basis_cells:
            basis.add(cell[0], cell[1])

        # Tính thế vị
        u, v = self._compute_potentials(C, basis, m, n)
        delta = [[u[i] + v[j] - C[i, j] for j in range(n)] for i in range(m)]

        # Kích thước ô
        CW, CH, LW, TH = 2.0, 1.6, 1.4, 0.8
        total_w = LW + LW + n * CW + LW
        total_h = TH + TH + m * CH + TH

        fig_w = max(10, total_w * 0.85 + 1.5)
        fig_h = max(6, total_h * 0.85 + 2.0)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_xlim(0, total_w)
        ax.set_ylim(0, total_h)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.invert_yaxis()

        # Colors
        CLR_BASIS = "#D6EAF8"
        CLR_FREE = "#FDFEFE"
        CLR_HDR_BG = "#ECF0F1"
        CLR_BJ_BG = "#FAD7A0"
        CLR_AI_BG = "#D5F5E3"
        CLR_CORNER = "#F9E79F"

        def cx(col: int) -> float:
            if col == 0: return 0.0
            if col == 1: return LW
            if col <= n + 1: return LW + LW + (col - 2) * CW
            return LW + LW + n * CW

        def cy(row: int) -> float:
            if row == 0: return 0.0
            if row == 1: return TH
            if row <= m + 1: return TH + TH + (row - 2) * CH
            return TH + TH + m * CH

        def cw(col: int) -> float:
            return LW if col in (0, 1, n + 2) else CW

        def ch(row: int) -> float:
            return TH if row in (0, 1, m + 2) else CH

        def rect(col, row, fc, ec="#999999", lw=0.8):
            x0, y0 = cx(col), cy(row)
            w, h = cw(col), ch(row)
            ax.add_patch(plt.Rectangle((x0, y0), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, clip_on=False))
            return x0, y0, w, h

        def txt(x, y, s, **kw):
            ax.text(x, y, s, clip_on=False, **kw)

        def fmt(v):
            return str(int(round(v))) if abs(v - round(v)) < _EPS else f"{v:.4g}"

        # Corner
        ax.add_patch(plt.Rectangle((0, 0), LW + LW, TH + TH, facecolor=CLR_CORNER, edgecolor="#999999", linewidth=0.8, clip_on=False))
        ax.plot([0, LW + LW], [0, TH + TH], color="#999999", linewidth=0.8, clip_on=False)
        txt(LW + LW - 0.10, 0.10, "vⱼ", fontsize=10, ha="right", va="top", color="#1A5276", style="italic", fontweight="bold")
        txt(LW + LW - 0.12, (TH + TH) * 0.75, "bⱼ", fontsize=10, ha="right", va="center", color="#555555", style="italic", fontweight="bold")
        txt(0.12, (TH + TH) - 0.12, "uᵢ", fontsize=11, ha="left", va="bottom", color="#555555", style="italic", fontweight="bold")
        txt(LW + LW - 0.60, (TH + TH) - 0.12, "aᵢ", fontsize=11, ha="right", va="bottom", color="#555555", style="italic", fontweight="bold")

        # Header v_j
        for j in range(n):
            x0r, y0r, wr, hr = rect(j + 2, 0, CLR_HDR_BG, lw=1.0)
            txt(x0r + wr/2, y0r + hr/2, fmt(v[j]), fontsize=12, ha="center", va="center", fontweight="bold", color="#1A5276")
        rect(n + 2, 0, CLR_AI_BG, lw=1.0)

        # Header b_j
        for j in range(n):
            x0r, y0r, wr, hr = rect(j + 2, 1, CLR_BJ_BG, lw=1.0)
            txt(x0r + wr/2, y0r + hr/2, fmt(B[j]), fontsize=13, ha="center", va="center", fontweight="bold")
        x0r, y0r, wr, hr = rect(n + 2, 1, CLR_AI_BG, lw=1.0)
        txt(x0r + wr/2, y0r + hr/2, "aᵢ", fontsize=10, ha="center", va="center", color="#555555", style="italic")

        # Data rows
        for i in range(m):
            row = i + 2
            x0r, y0r, wr, hr = rect(0, row, CLR_HDR_BG, lw=1.0)
            txt(x0r + wr/2, y0r + hr/2, fmt(u[i]), fontsize=12, ha="center", va="center", fontweight="bold", color="#1A5276")

            x0r, y0r, wr, hr = rect(1, row, CLR_AI_BG, lw=1.0)
            ai_s = fmt(A[i])
            txt(x0r + wr/2, y0r + hr/2, ai_s, fontsize=13, ha="center", va="center", fontweight="bold")

            for j in range(n):
                is_basis = (i, j) in basis
                bg = CLR_BASIS if is_basis else CLR_FREE
                x0r, y0r, wr, hr = rect(j + 2, row, bg, lw=0.8)
                pad = 0.13
                txt(x0r + pad, y0r + pad, fmt(C[i, j]), fontsize=10, ha="left", va="top", color="#555555")
                if is_basis:
                    flow = X[i, j]
                    if flow > _EPS:
                        txt(x0r + wr - pad, y0r + hr - pad, fmt(flow), fontsize=14, ha="right", va="bottom", fontweight="bold", color="#154360")
                    else:
                        txt(x0r + wr - pad, y0r + hr - pad, "0*", fontsize=12, ha="right", va="bottom", fontweight="bold", color="#5DADE2")
                else:
                    dij = delta[i][j]
                    clr = "#CB4335" if dij > _EPS else "#7F8C8D"
                    txt(x0r + wr - pad, y0r + hr - pad, fmt(dij), fontsize=11, ha="right", va="bottom", style="italic", color=clr)

            x0r, y0r, wr, hr = rect(n + 2, row, CLR_AI_BG, lw=1.0)
            txt(x0r + wr/2, y0r + hr/2, ai_s, fontsize=13, ha="center", va="center", fontweight="bold")

        # Footer b_j
        footer_row = m + 2
        foot_y = cy(footer_row)
        ax.add_patch(plt.Rectangle((0.0, foot_y), LW + LW, TH, facecolor=CLR_BJ_BG, edgecolor="#999999", linewidth=1.0, clip_on=False))
        txt((LW + LW) / 2, foot_y + TH / 2, "bⱼ", fontsize=11, ha="center", va="center", color="#7D3C98", fontweight="bold", style="italic")
        for j in range(n):
            x0r, y0r, wr, hr = rect(j + 2, footer_row, CLR_BJ_BG, lw=1.0)
            txt(x0r + wr/2, y0r + hr/2, fmt(B[j]), fontsize=13, ha="center", va="center", fontweight="bold")
        x0r, y0r, wr, hr = rect(n + 2, footer_row, "#F9E79F", lw=1.0)
        txt(x0r + wr/2, y0r + hr/2, f"Tổng\n{fmt(float(np.sum(A)))}", fontsize=10, ha="center", va="center", fontweight="bold")

        outer_h_full = TH + TH + m * CH + TH
        ax.add_patch(plt.Rectangle((0, 0), total_w, outer_h_full, fill=False, edgecolor="#333333", linewidth=1.8, clip_on=False))
        ax.set_ylim(outer_h_full, -0.05)

        legend_patches = [
            mpatches.Patch(facecolor=CLR_BASIS, edgecolor="#999999", label="Ô cơ sở (xᵢⱼ)"),
            mpatches.Patch(facecolor=CLR_FREE, edgecolor="#999999", label="Ô không cơ sở (Δᵢⱼ)"),
            mpatches.Patch(facecolor=CLR_AI_BG, edgecolor="#999999", label="Lượng phát aᵢ"),
            mpatches.Patch(facecolor=CLR_BJ_BG, edgecolor="#999999", label="Lượng thu bⱼ"),
        ]
        ax.legend(handles=legend_patches, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=4, fontsize=8, framealpha=0.9)

        fig.suptitle(f"{title}\nTổng chi phí tối ưu: f(X*) = {solution.total_cost:.4g}", fontsize=14, fontweight="bold", y=1.02)

        buf = io.BytesIO()
        fig.tight_layout(rect=[0, 0.04, 1, 0.96])
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _compute_potentials(self, C, basis, m, n):
        """Tính thế vị cho visualization."""
        u = [None] * m
        v = [None] * n
        u[0] = 0.0
        changed = True
        while changed:
            changed = False
            for (i, j) in basis:
                if u[i] is not None and v[j] is None:
                    v[j] = float(C[i, j]) - u[i]
                    changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = float(C[i, j]) - v[j]
                    changed = True
        return [x or 0.0 for x in u], [x or 0.0 for x in v]
