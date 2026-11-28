"""Tầng 1 – class Config, clean_env(). TODO: B01"""
import os
from dotenv import load_dotenv

load_dotenv()


def clean_env(key: str, default: str = "") -> str:
    """Đọc biến môi trường, cắt bỏ khoảng trắng thừa và dấu ngoặc bọc ngoài."""
    raw = os.getenv(key)
    if raw is None:
        return default
    cleaned = raw.strip().strip('"').strip("'").strip()
    return cleaned if cleaned else default


def env_bool(key: str, default: bool = False) -> bool:
    """Chuyển biến môi trường dạng chuỗi ('true', '1', 'yes') sang kiểu bool."""
    val = clean_env(key, "").lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


class Config:
    """Cấu hình trung tâm cho Flask app (được nạp vào app.config ở B06)."""

    SECRET_KEY = clean_env("SECRET_KEY", "dev-secret-key-khong-dung-production")
    DATABASE_URL = clean_env("DATABASE_URL")

    # Cấu hình Cookie Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)

    # Danh sách domain Frontend được phép gọi API (phân tách bằng dấu phẩy)
    CORS_ORIGINS = [
        origin.strip()
        for origin in clean_env(
            "CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5000",
        ).split(",")
        if origin.strip()
    ]

    # Cấu hình bảo vệ các route Debug
    ENABLE_DEBUG_ROUTES = env_bool("ENABLE_DEBUG_ROUTES", False)
    DEBUG_ACCESS_TOKEN = clean_env("DEBUG_ACCESS_TOKEN", "")