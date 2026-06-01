"""
backend/app/config.py
======================
Cấu hình ứng dụng FastAPI.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Cấu hình ứng dụng từ biến môi trường."""

    # Tên ứng dụng
    app_name: str = "Bài Toán Vận Tải API"
    app_version: str = "1.0.0"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ]

    # API
    api_prefix: str = "/api"

    # Algorithm defaults
    max_iterations: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
