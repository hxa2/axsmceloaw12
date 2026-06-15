"""
backend/app/main.py
=====================
FastAPI application entry point.

Cấu hình:
  - CORS cho frontend React (localhost:5173).
  - Router /api/transportation.
  - Exception handlers cho lỗi rõ ràng.
  - Logging cơ bản.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.transportation import router as transportation_router
from backend.app.api.assignment import router as assignment_router
from backend.app.config import settings

# ── Cấu hình logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)-22s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Tạo FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API cho Bài Toán Vận Tải – hỗ trợ nhiều phương pháp khởi tạo "
        "và tối ưu hóa, trả nghiệm chi tiết từng bước."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ───────────────────────────────────────────────────────────
app.include_router(transportation_router)
app.include_router(assignment_router)


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Bắt ValueError chưa được xử lý → 400."""
    logger.warning(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    """Bắt RuntimeError chưa được xử lý → 500."""
    logger.error(f"RuntimeError: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Lỗi nội bộ: {exc}"},
    )


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    """Bắt NotImplementedError → 422."""
    logger.warning(f"NotImplementedError: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ── Phục vụ Frontend Static Files (Dành cho Docker Deployment) ───────────────
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.isdir(frontend_dist):
    # Mount assets folder
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    # Catch-all route to serve index.html for SPA (React Router)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Bỏ qua các request bắt đầu bằng /api hoặc /docs đã được FastAPI xử lý
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
            
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})
else:
    # ── Root endpoint (Mặc định khi chạy local backend độc lập) ───────────────
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/transportation/health",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
