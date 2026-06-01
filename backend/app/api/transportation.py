"""
backend/app/api/transportation.py
===================================
FastAPI router cho bài toán vận tải.

Endpoints:
  GET  /api/transportation/health
  GET  /api/transportation/methods
  GET  /api/transportation/sample
  GET  /api/transportation/samples
  POST /api/transportation/solve
  POST /api/transportation/solve-from-file
  GET  /api/transportation/export/{format}  (POST body = solve result)

Router chỉ xử lý HTTP I/O. Logic nằm ở services.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from backend.app.repositories.csv_repository import CsvRepository
from backend.app.repositories.excel_repository import ExcelRepository
from backend.app.repositories.json_repository import JsonRepository
from backend.app.schemas.request import SolveRequest
from backend.app.schemas.response import (
    HealthResponse,
    MethodInfo,
    MethodsResponse,
    SampleProblemResponse,
    SolveResponse,
)
from backend.app.services.sample_data_service import SampleDataService
from backend.app.services.solver_service import SolverService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transportation", tags=["transportation"])

# Dependency injection đơn giản (singleton per-request)
_solver_service = SolverService()
_sample_service = SampleDataService()
_excel_repo = ExcelRepository()
_csv_repo = CsvRepository()
_json_repo = JsonRepository()


# ── Health check ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Kiểm tra trạng thái hoạt động của API."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        message="Transportation API đang hoạt động.",
    )


# ── Methods ───────────────────────────────────────────────────────────────────

@router.get("/methods", response_model=MethodsResponse, summary="Danh sách thuật toán")
async def get_methods() -> MethodsResponse:
    """Trả danh sách các thuật toán initial solution và optimization có thể dùng."""
    return MethodsResponse(
        initialMethods=[
            MethodInfo(
                id="least_cost",
                name="Least Cost",
                description="Chọn ô có chi phí nhỏ nhất trước. Thường cho nghiệm ban đầu tốt hơn Northwest Corner.",
                isAvailable=True,
            ),
            MethodInfo(
                id="northwest_corner",
                name="Northwest Corner",
                description="Bắt đầu từ góc tây bắc của bảng. Nhanh, đơn giản nhưng chi phí ban đầu thường cao hơn.",
                isAvailable=True,
            ),
            MethodInfo(
                id="vogel",
                name="Vogel Approximation",
                description="Phương pháp xấp xỉ Vogel (VAM). Cho nghiệm ban đầu tốt nhất. (Chưa triển khai)",
                isAvailable=False,
            ),
        ],
        optimizationMethods=[
            MethodInfo(
                id="potential",
                name="Potential Method",
                description="Tối ưu nghiệm bằng phương pháp thế vị (MODI). Đảm bảo hội tụ về nghiệm tối ưu toàn cục.",
                isAvailable=True,
            ),
            MethodInfo(
                id="none",
                name="No Optimization",
                description="Chỉ trả nghiệm khởi tạo, không tối ưu hóa.",
                isAvailable=True,
            ),
        ],
    )


# ── Sample problems ───────────────────────────────────────────────────────────

@router.get("/sample", response_model=SampleProblemResponse, summary="Bài toán mẫu")
async def get_sample(
    id: str = Query(default="classic_3x4", description="ID của bài toán mẫu"),
) -> SampleProblemResponse:
    """Trả một bài toán vận tải mẫu theo ID."""
    return _sample_service.get_sample_problem(id)


@router.get("/samples", response_model=list[SampleProblemResponse], summary="Tất cả bài toán mẫu")
async def list_samples() -> list[SampleProblemResponse]:
    """Trả danh sách tất cả bài toán mẫu có sẵn."""
    return _sample_service.list_samples()


@router.get(
    "/sample/random",
    response_model=SampleProblemResponse,
    summary="Bài toán ngẫu nhiên",
)
async def get_random_sample(
    m: int = Query(default=3, ge=2, le=10, description="Số trạm phát"),
    n: int = Query(default=4, ge=2, le=10, description="Số trạm thu"),
    degenerate: bool = Query(default=False, description="Có muốn bài toán suy biến không"),
) -> SampleProblemResponse:
    """Sinh bài toán vận tải ngẫu nhiên."""
    return _sample_service.get_random_problem(m=m, n=n, degenerate=degenerate)


# ── Solve ─────────────────────────────────────────────────────────────────────

@router.post("/solve", response_model=SolveResponse, summary="Giải bài toán vận tải")
async def solve(request: SolveRequest) -> SolveResponse:
    """
    Giải bài toán vận tải từ JSON request.

    Body:
    - `costMatrix`: Ma trận cước phí (m × n).
    - `supply`: Vectơ lượng phát (m,).
    - `demand`: Vectơ lượng thu (n,).
    - `initialMethod`: Phương pháp khởi tạo ("least_cost" hoặc "northwest_corner").
    - `optimizationMethod`: Phương pháp tối ưu ("potential" hoặc "none").
    - `includeIterations`: Có trả chi tiết từng bước không (mặc định: true).
    """
    return _solver_service.solve(request)


@router.post(
    "/solve-from-file",
    response_model=SolveResponse,
    summary="Giải từ file Excel/CSV/JSON",
)
async def solve_from_file(
    file: UploadFile = File(..., description="File Excel (.xlsx), CSV (.csv), hoặc JSON (.json)"),
    initialMethod: str = Form(default="least_cost"),
    optimizationMethod: str = Form(default="potential"),
    includeIterations: bool = Form(default=True),
) -> SolveResponse:
    """
    Giải bài toán vận tải từ file upload.

    Hỗ trợ định dạng:
    - `.xlsx` / `.xls`: Excel (3 sheet: cost, supply, demand).
    - `.csv`: CSV với header tên section.
    - `.json`: JSON với keys costMatrix, supply, demand.
    """
    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".xlsx"):
            problem = _excel_repo.load_xlsx_from_bytes(content)
        elif filename.endswith(".xls"):
            problem = _excel_repo.load_xls_from_bytes(content)
        elif filename.endswith(".csv"):
            problem = _csv_repo.load_from_bytes(content)
        elif filename.endswith(".json"):
            problem = _json_repo.load_from_bytes(content)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Định dạng file '{filename}' không hỗ trợ. Chấp nhận: .xlsx, .xls, .csv, .json",
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Tạo request từ problem
    solve_request = SolveRequest(
        costMatrix=problem.cost_matrix,
        supply=problem.supply,
        demand=problem.demand,
        initialMethod=initialMethod,
        optimizationMethod=optimizationMethod,
        sourceNames=problem.source_names,
        destinationNames=problem.destination_names,
        includeIterations=includeIterations,
    )

    return _solver_service.solve(solve_request)
