"""
backend/app/api/assignment.py
================================
FastAPI router cho bài toán phân việc (Hungarian Algorithm).

Endpoints:
  POST /api/assignment/solve
"""

import logging
from fastapi import APIRouter
from backend.app.schemas.request import AssignmentRequest
from backend.app.schemas.response import ExtendedSolveResponse
from backend.app.services.assignment_service import solve_assignment_problem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assignment", tags=["assignment"])


@router.post(
    "/solve",
    response_model=ExtendedSolveResponse,
    summary="Giải bài toán phân việc (Hungarian Algorithm)",
)
async def solve_assignment_endpoint(request: AssignmentRequest) -> ExtendedSolveResponse:
    """
    Giải bài toán phân việc bằng Hungarian Algorithm.

    Body:
    - `matrix`: Ma trận chi phí / lợi nhuận (m×n, có thể không vuông).
    - `objective`: "minimize" hoặc "maximize".
    - `workerNames`: Tên người (tuỳ chọn).
    - `jobNames`: Tên công việc (tuỳ chọn).

    Response:
    - `solution.assignments`: Danh sách phân công.
    - `solution.totalCost` / `solution.totalProfit`: Tổng chi phí / lợi nhuận.
    - `steps`: Chi tiết từng bước Hungarian.
    """
    return solve_assignment_problem(request)
