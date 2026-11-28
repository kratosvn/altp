"""hash_password/check_password (bcrypt), @login_required, @debug_access_required. TODO: B03"""
from functools import wraps
import bcrypt
from flask import current_app, jsonify, request, session


def hash_password(plain_text: str) -> str:
    """Băm mật khẩu hoặc mã OTP một chiều bằng bcrypt kèm salt ngẫu nhiên."""
    # [FIX Lỗi 3] Chặn đầu vào None hoặc chuỗi rỗng trước khi .encode("utf-8")
    # để tránh crash AttributeError (với None) và tránh băm mật khẩu rỗng ""
    if not isinstance(plain_text, str) or not plain_text:
        raise ValueError("Mật khẩu hoặc mã OTP không được để trống.")
    hashed = bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def check_password(plain_text: str, hashed_text: str) -> bool:
    """So khớp mật khẩu/OTP người dùng nhập với chuỗi hash trong DB."""
    if not plain_text or not hashed_text:
        return False
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed_text.encode("utf-8"))


def login_required(f):
    """Chặn request chưa có phiên đăng nhập hợp lệ."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Bạn cần đăng nhập để tiếp tục."}), 401
        return f(*args, **kwargs)
    return decorated


def debug_access_required(f):
    """Khóa các route debug: chỉ mở khi bật cờ trong .env và khớp token (nếu có đặt)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config.get("ENABLE_DEBUG_ROUTES", False):
            return jsonify({"error": "Chức năng debug đang bị tắt."}), 403

        expected_token = current_app.config.get("DEBUG_ACCESS_TOKEN", "")
        if expected_token:
            client_token = request.headers.get("X-Debug-Token", "")
            if client_token != expected_token:
                return jsonify({"error": "Thiếu hoặc sai X-Debug-Token."}), 403

        return f(*args, **kwargs)
    return decorated