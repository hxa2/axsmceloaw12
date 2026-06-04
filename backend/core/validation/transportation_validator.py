"""
backend/core/validation/transportation_validator.py
=====================================================
Validator cho bài toán vận tải.

Không phụ thuộc framework nào. Trả ValidationResult với danh sách lỗi
và cảnh báo rõ ràng, thay vì để lỗi Python thô văng ra.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ValidationResult:
    """Kết quả kiểm tra tính hợp lệ."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def first_error(self) -> Optional[str]:
        return self.errors[0] if self.errors else None


@dataclass
class BalanceResult:
    """Kết quả sau khi cân bằng bài toán vận tải."""
    cost_matrix: list
    supply: list
    demand: list
    warnings: List[str]
    is_balanced_original: bool
    balance_type: str  # "none" | "dummy_source" | "dummy_destination"
    dummy_source_index: Optional[int]
    dummy_destination_index: Optional[int]
    original_supply_total: float
    original_demand_total: float



class TransportationValidator:
    """
    Validator chuyên biệt cho bài toán vận tải.

    Kiểm tra:
      - cost_matrix không rỗng, không NaN, không âm.
      - supply không rỗng, không âm.
      - demand không rỗng, không âm.
      - shape: số hàng cost_matrix = len(supply).
      - shape: số cột cost_matrix = len(demand).
      - m ≥ 2, n ≥ 2.
      - Cân bằng: sum(supply) ≈ sum(demand).
      - Nếu không cân bằng: trả warning và đề nghị thêm dummy.
    """

    _EPS = 1e-9
    _BALANCE_TOL = 1e-6  # Dung sai cân bằng (tương đối)

    def validate(
        self,
        cost_matrix: Any,
        supply: Any,
        demand: Any,
    ) -> ValidationResult:
        """
        Kiểm tra tính hợp lệ của dữ liệu đầu vào.

        Parameters
        ----------
        cost_matrix : list[list[float]] hoặc tương tự
        supply      : list[float]
        demand      : list[float]

        Returns
        -------
        ValidationResult với danh sách lỗi và cảnh báo.
        """
        result = ValidationResult(is_valid=True)

        # ── 1. Kiểm tra không rỗng ────────────────────────────────────────
        if not cost_matrix:
            result.add_error("Ma trận cước phí không được rỗng.")
            return result  # Dừng sớm vì không thể kiểm tra tiếp

        if not supply:
            result.add_error("Vectơ lượng phát (supply) không được rỗng.")

        if not demand:
            result.add_error("Vectơ lượng thu (demand) không được rỗng.")

        if not result.is_valid:
            return result

        # ── 2. Kiểm tra kiểu và hàng đồng nhất ───────────────────────────
        if not isinstance(cost_matrix[0], (list, tuple)):
            result.add_error("cost_matrix phải là ma trận 2D (list of lists).")
            return result

        m = len(cost_matrix)
        n = len(cost_matrix[0])

        for row_idx, row in enumerate(cost_matrix):
            if len(row) != n:
                result.add_error(
                    f"Hàng {row_idx + 1} của cost_matrix có {len(row)} phần tử, "
                    f"nhưng cần {n} phần tử."
                )
                return result

        # ── 3. Kiểm tra kích thước tối thiểu ─────────────────────────────
        if m < 2:
            result.add_error(f"Cần ít nhất 2 trạm phát (hiện tại m={m}).")
        if n < 2:
            result.add_error(f"Cần ít nhất 2 trạm thu (hiện tại n={n}).")

        # ── 4. Kiểm tra shape tương thích ────────────────────────────────
        if len(supply) != m:
            result.add_error(
                f"Số hàng cost_matrix ({m}) ≠ số phần tử supply ({len(supply)})."
            )
        if len(demand) != n:
            result.add_error(
                f"Số cột cost_matrix ({n}) ≠ số phần tử demand ({len(demand)})."
            )

        if not result.is_valid:
            return result

        # ── 5. Kiểm tra giá trị số hợp lệ ───────────────────────────────
        for i, row in enumerate(cost_matrix):
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    result.add_error(
                        f"cost_matrix[{i}][{j}] không phải số: {val!r}."
                    )
                elif val != val:  # NaN check
                    result.add_error(f"cost_matrix[{i}][{j}] là NaN.")
                elif val < 0:
                    result.add_error(
                        f"cost_matrix[{i}][{j}] = {val} là âm. "
                        f"Ma trận cước phí phải không âm."
                    )

        for i, val in enumerate(supply):
            if not isinstance(val, (int, float)):
                result.add_error(f"supply[{i}] không phải số: {val!r}.")
            elif val != val:
                result.add_error(f"supply[{i}] là NaN.")
            elif val < 0:
                result.add_error(f"supply[{i}] = {val} là âm. Lượng phát phải không âm.")
            elif val == 0:
                result.add_warning(f"supply[{i}] = 0. Trạm phát S{i+1} không có hàng.")

        for j, val in enumerate(demand):
            if not isinstance(val, (int, float)):
                result.add_error(f"demand[{j}] không phải số: {val!r}.")
            elif val != val:
                result.add_error(f"demand[{j}] là NaN.")
            elif val < 0:
                result.add_error(f"demand[{j}] = {val} là âm. Lượng thu phải không âm.")
            elif val == 0:
                result.add_warning(f"demand[{j}] = 0. Trạm thu D{j+1} không có nhu cầu.")

        if not result.is_valid:
            return result

        # ── 6. Kiểm tra cân bằng ─────────────────────────────────────────
        total_supply = sum(supply)
        total_demand = sum(demand)

        if total_supply <= self._EPS:
            result.add_error("Tổng lượng phát = 0. Không có gì để vận chuyển.")
            return result

        relative_diff = abs(total_supply - total_demand) / total_supply

        if relative_diff > self._BALANCE_TOL:
            if total_supply > total_demand:
                result.add_warning(
                    f"Bài toán KHÔNG cân bằng: "
                    f"Tổng cung ({total_supply:.4g}) > Tổng cầu ({total_demand:.4g}). "
                    f"Chênh lệch = {total_supply - total_demand:.4g}. "
                    f"Backend sẽ tự động thêm trạm thu giả (dummy destination)."
                )
            else:
                result.add_warning(
                    f"Bài toán KHÔNG cân bằng: "
                    f"Tổng cầu ({total_demand:.4g}) > Tổng cung ({total_supply:.4g}). "
                    f"Chênh lệch = {total_demand - total_supply:.4g}. "
                    f"Backend sẽ tự động thêm trạm phát giả (dummy source)."
                )

        return result

    def balance_problem(
        self,
        cost_matrix: list,
        supply: list,
        demand: list,
    ) -> BalanceResult:
        """
        Cân bằng bài toán vận tải bằng cách thêm dummy row/column.

        Returns
        -------
        BalanceResult với dữ liệu đã cân bằng và metadata.
        """
        warnings_list: list[str] = []
        cost_matrix = [list(row) for row in cost_matrix]
        supply = list(supply)
        demand = list(demand)

        original_supply_total = sum(supply)
        original_demand_total = sum(demand)
        diff = original_supply_total - original_demand_total

        if abs(diff) <= self._EPS:
            return BalanceResult(
                cost_matrix=cost_matrix,
                supply=supply,
                demand=demand,
                warnings=warnings_list,
                is_balanced_original=True,
                balance_type="none",
                dummy_source_index=None,
                dummy_destination_index=None,
                original_supply_total=original_supply_total,
                original_demand_total=original_demand_total,
            )

        if diff > 0:
            # Cung > Cầu → thêm dummy destination (cột chi phí 0)
            for row in cost_matrix:
                row.append(0.0)
            demand.append(diff)
            dummy_dest_index = len(demand) - 1
            warnings_list.append(
                f"Đã thêm trạm thu giả (dummy) với nhu cầu {diff:.4g} "
                f"(chi phí vận chuyển = 0)."
            )
            return BalanceResult(
                cost_matrix=cost_matrix,
                supply=supply,
                demand=demand,
                warnings=warnings_list,
                is_balanced_original=False,
                balance_type="dummy_destination",
                dummy_source_index=None,
                dummy_destination_index=dummy_dest_index,
                original_supply_total=original_supply_total,
                original_demand_total=original_demand_total,
            )
        else:
            # Cầu > Cung → thêm dummy source (hàng chi phí 0)
            n = len(demand)
            cost_matrix.append([0.0] * n)
            supply.append(-diff)
            dummy_src_index = len(supply) - 1
            warnings_list.append(
                f"Đã thêm trạm phát giả (dummy) với lượng {-diff:.4g} "
                f"(chi phí vận chuyển = 0)."
            )
            return BalanceResult(
                cost_matrix=cost_matrix,
                supply=supply,
                demand=demand,
                warnings=warnings_list,
                is_balanced_original=False,
                balance_type="dummy_source",
                dummy_source_index=dummy_src_index,
                dummy_destination_index=None,
                original_supply_total=original_supply_total,
                original_demand_total=original_demand_total,
            )

