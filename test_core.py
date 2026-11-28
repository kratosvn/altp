"""Kịch bản kiểm thử cho 3 module nền tảng:
- B01: backend/config.py (clean_env, Config)
- B02: backend/core/extensions.py (standalone_db_connection, init_extensions, get_db/close_db, CORS)
- B03: backend/core/security.py (hash_password, check_password, @login_required, @debug_access_required)

Chạy bằng:
    .venv/bin/python test_core.py
hoặc:
    .venv/bin/pytest test_core.py -v
"""
import sys
import pytest
from flask import Flask, jsonify


# ==============================================================================
# B01: Kiểm thử backend/config.py
# ==============================================================================


def test_b01_clean_env_strips_whitespace_and_quotes(monkeypatch):
    """Kiểm tra clean_env() cắt bỏ khoảng trắng thừa, dấu nháy đơn/kép và trả default khi rỗng."""
    from backend.config import clean_env

    monkeypatch.setenv("TEST_ENV_SPACES", "   hello_world   ")
    assert clean_env("TEST_ENV_SPACES") == "hello_world"

    monkeypatch.setenv("TEST_ENV_DOUBLE_QUOTES", '  "  secret_value  "  ')
    assert clean_env("TEST_ENV_DOUBLE_QUOTES") == "secret_value"

    monkeypatch.setenv("TEST_ENV_SINGLE_QUOTES", "  'single_quoted'  ")
    assert clean_env("TEST_ENV_SINGLE_QUOTES") == "single_quoted"

    monkeypatch.setenv("TEST_ENV_EMPTY_QUOTES", '   ""   ')
    assert clean_env("TEST_ENV_EMPTY_QUOTES", "fallback_val") == "fallback_val"

    monkeypatch.delenv("TEST_ENV_MISSING", raising=False)
    assert clean_env("TEST_ENV_MISSING", "default_val") == "default_val"


def test_b01_config_basic_attributes():
    """Kiểm tra các thuộc tính cơ bản trên Config (SECRET_KEY, CORS_ORIGINS, SESSION_COOKIE_HTTPONLY)."""
    from backend.config import Config

    assert isinstance(Config.SECRET_KEY, str) and len(Config.SECRET_KEY) > 0
    assert Config.SESSION_COOKIE_HTTPONLY is True
    assert isinstance(Config.CORS_ORIGINS, list) and len(Config.CORS_ORIGINS) > 0
    for origin in Config.CORS_ORIGINS:
        assert origin == origin.strip() and len(origin) > 0


def test_b01_config_database_url():
    """Kiểm tra Config.DATABASE_URL đã được cấu hình hợp lệ (không rỗng)."""
    from backend.config import Config

    assert isinstance(Config.DATABASE_URL, str)
    assert len(Config.DATABASE_URL) > 0, (
        "Config.DATABASE_URL đang rỗng ('') — thiếu biến DATABASE_URL trong .env"
    )


# ==============================================================================
# B02: Kiểm thử backend/core/extensions.py
# ==============================================================================


def test_b02_standalone_db_connection_select_1_and_error_recovery():
    """Test standalone_db_connection() chạy SELECT 1 và tự trả kết nối về pool (cả khi có lỗi)."""
    import database
    from backend.core.extensions import standalone_db_connection

    pool_instance = database.init_pool()
    used_before = len(pool_instance._used)

    # 1. Chạy SELECT 1 thành công và kiểm tra kết nối được trả về pool
    with standalone_db_connection() as conn:
        assert len(pool_instance._used) == used_before + 1
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
            assert row is not None and row[0] == 1

    assert len(pool_instance._used) == used_before, (
        "Kết nối chưa được trả về pool sau khi thoát khối with bình thường."
    )

    # 2. Giả lập lỗi bên trong khối with -> phải rollback và vẫn trả kết nối về pool
    with pytest.raises(RuntimeError, match="Simulated failure"):
        with standalone_db_connection() as conn_err:
            assert len(pool_instance._used) == used_before + 1
            with conn_err.cursor() as cur:
                cur.execute("SELECT 1")
            raise RuntimeError("Simulated failure")

    assert len(pool_instance._used) == used_before, (
        "Kết nối bị rò rỉ (không trả về pool) khi xảy ra ngoại lệ trong khối with."
    )


def test_b02_ping_db_route_and_teardown():
    """Test init_extensions(app) + get_db() + close_db() teardown qua route /ping-db bằng test_client."""
    import database
    from backend.config import Config
    from backend.core.extensions import get_db, init_extensions

    pool_instance = database.init_pool()
    used_before = len(pool_instance._used)

    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["TESTING"] = True
    init_extensions(app)

    @app.route("/ping-db")
    def ping_db():
        conn = get_db()
        # Gọi get_db() lần 2 trong cùng request phải tái sử dụng cùng 1 connection trên flask.g
        assert get_db() is conn
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            val = cur.fetchone()[0]
        return jsonify({"ok": True, "db": val}), 200

    client = app.test_client()
    resp = client.get("/ping-db")
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True, "db": 1}
    assert len(pool_instance._used) == used_before, (
        "Hook close_db() chưa trả kết nối về pool sau khi request kết thúc."
    )


def test_b02_cors_headers_on_valid_origin():
    """Kiểm tra header CORS phản hồi khi gửi request có header Origin hợp lệ."""
    from backend.config import Config
    from backend.core.extensions import init_extensions

    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["TESTING"] = True
    init_extensions(app)

    @app.route("/api/test-cors")
    def test_cors_route():
        return jsonify({"ok": True}), 200

    valid_origin = Config.CORS_ORIGINS[0]
    client = app.test_client()
    resp = client.get("/api/test-cors", headers={"Origin": valid_origin})

    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == valid_origin
    assert resp.headers.get("Access-Control-Allow-Credentials") == "true"


# ==============================================================================
# B03: Kiểm thử backend/core/security.py
# ==============================================================================


def test_b03_hash_and_check_password_valid_and_invalid():
    """Test hash_password() và check_password() với mật khẩu đúng và mật khẩu sai."""
    from backend.core.security import check_password, hash_password

    raw_pw = "TrieuPhu@2026"
    hashed = hash_password(raw_pw)

    assert isinstance(hashed, str)
    assert hashed != raw_pw
    assert hashed.startswith("$2")

    assert check_password(raw_pw, hashed) is True
    assert check_password("SaiMatKhau@123", hashed) is False


def test_b03_check_password_empty_and_none():
    """Test check_password() trả False an toàn với chuỗi rỗng và None."""
    from backend.core.security import check_password, hash_password

    valid_hash = hash_password("MatKhauHopLe123")

    assert check_password("", valid_hash) is False
    assert check_password(None, valid_hash) is False
    assert check_password("MatKhauHopLe123", "") is False
    assert check_password("MatKhauHopLe123", None) is False


def test_b03_hash_password_empty_and_none():
    """Test hash_password() từ chối chuỗi rỗng và None bằng ValueError (không crash AttributeError)."""
    from backend.core.security import hash_password

    with pytest.raises(ValueError):
        hash_password(None)
    with pytest.raises(ValueError):
        hash_password("")


def test_b03_login_required_decorator():
    """Test @login_required: chặn 401 khi chưa có session, cho qua 200 khi có user_id trong session."""
    from backend.core.security import login_required

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["TESTING"] = True

    @app.route("/api/protected")
    @login_required
    def protected_route():
        return jsonify({"ok": True}), 200

    client = app.test_client()

    # 1. Chưa đăng nhập -> 401
    resp_unauth = client.get("/api/protected")
    assert resp_unauth.status_code == 401
    assert "error" in resp_unauth.get_json()

    # 2. Đã gán user_id trong session_transaction -> 200
    with client.session_transaction() as sess:
        sess["user_id"] = 42

    resp_auth = client.get("/api/protected")
    assert resp_auth.status_code == 200
    assert resp_auth.get_json() == {"ok": True}


def test_b03_debug_access_required_decorator():
    """Test @debug_access_required: 403 khi tắt cờ, 403 khi sai/thiếu token, 200 khi bật cờ + đúng X-Debug-Token."""
    from backend.core.security import debug_access_required

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["TESTING"] = True

    @app.route("/api/debug/ping")
    @debug_access_required
    def debug_ping():
        return jsonify({"debug": "ok"}), 200

    client = app.test_client()

    # 1. ENABLE_DEBUG_ROUTES = False -> 403
    app.config["ENABLE_DEBUG_ROUTES"] = False
    app.config["DEBUG_ACCESS_TOKEN"] = "my-debug-token"
    resp_disabled = client.get(
        "/api/debug/ping", headers={"X-Debug-Token": "my-debug-token"}
    )
    assert resp_disabled.status_code == 403

    # 2. ENABLE_DEBUG_ROUTES = True nhưng sai hoặc thiếu X-Debug-Token -> 403
    app.config["ENABLE_DEBUG_ROUTES"] = True
    resp_missing_token = client.get("/api/debug/ping")
    assert resp_missing_token.status_code == 403

    resp_wrong_token = client.get(
        "/api/debug/ping", headers={"X-Debug-Token": "wrong-token"}
    )
    assert resp_wrong_token.status_code == 403

    # 3. ENABLE_DEBUG_ROUTES = True + đúng X-Debug-Token -> 200
    resp_valid = client.get(
        "/api/debug/ping", headers={"X-Debug-Token": "my-debug-token"}
    )
    assert resp_valid.status_code == 200
    assert resp_valid.get_json() == {"debug": "ok"}

    # 4. ENABLE_DEBUG_ROUTES = True + không cấu hình DEBUG_ACCESS_TOKEN -> 200
    app.config["DEBUG_ACCESS_TOKEN"] = ""
    resp_no_token_cfg = client.get("/api/debug/ping")
    assert resp_no_token_cfg.status_code == 200


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
