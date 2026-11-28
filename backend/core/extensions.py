"""get_db/close_db trên flask.g, standalone_db_connection(), init_extensions (CORS), init_db_schema. TODO: B02"""
from contextlib import contextmanager
from flask import g
from flask_cors import CORS

from database import (
    get_db_connection,
    init_db,
    init_pool,
    release_db_connection,
)


def get_db():
    """Mượn kết nối DB cho request hiện tại và lưu tạm trong flask.g."""
    if "db_conn" not in g:
        g.db_conn = get_db_connection()
    return g.db_conn


def close_db(exception=None):
    """Hook teardown: luôn chạy khi request kết thúc để trả kết nối về Pool."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        if exception is not None and not conn.closed:
            conn.rollback()
        release_db_connection(conn)


@contextmanager
def standalone_db_connection():
    """Context manager dùng cho tác vụ nằm NGOÀI vòng đời request của Flask."""
    conn = get_db_connection()
    try:
        yield conn
    except Exception:
        if not conn.closed:
            conn.rollback()
        raise
    finally:
        release_db_connection(conn)


def init_db_schema():
    """Khởi tạo Connection Pool, bảng và Trigger từ Tầng 1."""
    init_pool()
    init_db()


def init_extensions(app):
    """Gắn CORS và DB teardown vào Flask app (gọi từ create_app ở B06)."""
    CORS(
        app,
        origins=app.config.get("CORS_ORIGINS", []),
        supports_credentials=True,
    )
    app.teardown_appcontext(close_db)