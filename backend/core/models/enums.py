"""
backend/core/models/enums.py
==============================
Enum cho các phương pháp thuật toán.
"""

from enum import Enum


class InitialMethod(str, Enum):
    """Phương pháp tìm phương án cực biên ban đầu."""
    LEAST_COST = "least_cost"
    NORTHWEST_CORNER = "northwest_corner"
    VOGEL = "vogel"


class OptimizationMethod(str, Enum):
    """Phương pháp tối ưu hóa."""
    POTENTIAL = "potential"
    NONE = "none"
