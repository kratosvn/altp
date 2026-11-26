"""Tầng 1: Database layer — PostgreSQL Connection Pool, Schema và Trigger.

Placeholder — triển khai các thành phần:
- Đọc cấu hình kết nối từ `.env` (python-dotenv)
- Khởi tạo & quản lý Connection Pool (`psycopg2.pool`)
- Khởi tạo Schema (tables, constraints, indexes)
- Khởi tạo Trigger / Function trong PostgreSQL
"""

# TODO (Buổi 1): Triển khai Connection Pool (psycopg2.pool)

# TODO (Buổi 1): Triển khai Schema (CREATE TABLE ...)

# TODO (Buổi 1): Triển khai Trigger & Function (CREATE OR REPLACE FUNCTION / CREATE TRIGGER ...)
import os
from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()

db_pool = None
DATABASE_URL = os.getenv("DATABASE_URL")
DB_MIN_CONN = int(os.getenv("DB_POOL_MIN_CONN", 1))
DB_MAX_CONN = int(os.getenv("DB_POOL_MAX_CONN", 10))


# 1. Quan ly connection pool
def init_pool():
    # Khoi tao ThreadedConnectionPool duy nhat
    global db_pool
    if db_pool is None:
        if not DATABASE_URL:
            raise ValueError("Thieu bien moi truong DATABASE_URL trong .env")
        db_pool = pool.ThreadedConnectionPool(
            minconn=DB_MIN_CONN,
            maxconn=DB_MAX_CONN,
            dsn=DATABASE_URL,
        )
            
            
    return db_pool


def get_db_connection():
    #Muon ket noi tu pool
    if db_pool is None:
        init_pool()
    return db_pool.getconn()

def release_db_connection(conn):
    # Tra ket noi ve pool. Neu ket noi da hong thi dong bo di
    if db_pool is not None and conn is not None:
        if conn.closed:
            db_pool.putconn(conn, close=True)
        else:
            db_pool.putconn(conn)


def close_pool():
    # Dong toan bo ket noi khi tat server
    global db_pool
    if db_pool is not None:
        db_pool.closeall()
        db_pool = None


# 2. SCHEMA 8 BANG + RANG BUOC + INDEX

SCHEMA_SQL = """
-- 1. Nhom Users va Auth
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    VARCHAR(50),
    avatar_url      TEXT,
    role            VARCHAR(20)     NOT NULL DEFAULT 'player'
        CHECK (role IN ('player', 'admin')),

    balance         BIGINT NOT NULL DEFAULT 0 CHECK (balance >= 0),
    high_score      BIGINT NOT NULL DEFAULT 0 CHECK (high_score >= 0),
    total_games     INTEGER NOT NULL DEFAULT 0 CHECK (total_games >= 0),
    total_wins      INTEGER NOT NULL DEFAULT 0 CHECK (total_wins >= 0),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS password_resets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);





-- 2. Nhom Gameplay, Lich su & BXH
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    current_level INTEGER NOT NULL DEFAULT 1 CHECK (current_level BETWEEN 1 AND 15),
    current_question_id INTEGER,
    asked_question_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'playing'
        CHECK (status IN ('playing', 'won', 'lost', 'stopped', 'timeout')),
    prize_won BIGINT NOT NULL DEFAULT 0 CHECK (prize_won >= 0),
    safe_milestone_prize BIGINT NOT NULL DEFAULT 0 CHECK (safe_milestone_prize >= 0),
    supports_used JSONB NOT NULL DEFAULT '{}'::jsonb,
    question_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_duration_sec INTEGER NOT NULL DEFAULT 0 CHECK (total_duration_sec >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);



CREATE TABLE IF NOT EXISTS game_answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 15),
    selected_option VARCHAR(5),
    is_correct BOOLEAN NOT NULL,
    time_spent_sec INTEGER NOT NULL DEFAULT 0 CHECK (time_spent_sec >= 0),
    answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);



-- 3. Nhom Shop & Thanh toan SePay
CREATE TABLE IF NOT EXISTS shop_items (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price BIGINT NOT NULL CHECK (price >= 0),
    item_type VARCHAR(30) NOT NULL DEFAULT 'support',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES shop_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES shop_items(id) ON DELETE SET NULL, -- NULL khi nap tien (deposit)
    external_tx_id VARCHAR(100) UNIQUE,                           -- Chong webhook SePay cong 2 lan
    payment_code VARCHAR(50),
    tx_type VARCHAR(20) NOT NULL CHECK (tx_type IN ('deposit', 'purchase')),
    status VARCHAR(20) NOT NULL DEFAULT 'completed'
        CHECK (status IN ('pending', 'completed', 'failed')),
    amount BIGINT NOT NULL CHECK (amount > 0),
    balance_before BIGINT NOT NULL CHECK (balance_before >= 0),
    balance_after BIGINT NOT NULL CHECK (balance_after >= 0),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);



-- 4. Nhom AI - Gemini
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_type VARCHAR(30) NOT NULL CHECK (feature_type IN ('chatbot', 'translate')),
    prompt_summary TEXT,
    tokens_used INTEGER NOT NULL DEFAULT 0 CHECK (tokens_used >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- 5. Indexes tang toc truy van BXH, Lich su & Giao dich
CREATE INDEX IF NOT EXISTS idx_users_high_score
    ON users (high_score DESC);

CREATE INDEX IF NOT EXISTS idx_game_sessions_user_created
    ON game_sessions (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_user_created
    ON transactions (user_id, created_at DESC);
"""





# 3. SQL TRIGGERS

TRIGGER_SQL = """
-- Trigger 1 (BEFORE UPDATE): Tu dong cap nhat cot updated_at
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION fn_set_updated_at();

DROP TRIGGER IF EXISTS trg_inventory_updated_at ON user_inventory;
CREATE TRIGGER trg_inventory_updated_at
BEFORE UPDATE ON user_inventory
FOR EACH ROW
EXECUTE FUNCTION fn_set_updated_at();

-- Trigger 2 (BEFORE UPDATE): Tu dien finished_at & total_duration_sec khi van choi ket thuc
CREATE OR REPLACE FUNCTION fn_finalize_game_session()
RETURNS TRIGGER AS $$
BEGIN
    NEW.finished_at := COALESCE(NEW.finished_at, NOW());
    NEW.total_duration_sec := GREATEST(
        0,
        EXTRACT(EPOCH FROM (NEW.finished_at - OLD.created_at))::INTEGER
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_game_sessions_finalize ON game_sessions;
CREATE TRIGGER trg_game_sessions_finalize
BEFORE UPDATE ON game_sessions
FOR EACH ROW
WHEN (OLD.status = 'playing' AND NEW.status <> 'playing')
EXECUTE FUNCTION fn_finalize_game_session();

-- Trigger 3 (AFTER UPDATE): Tu dong bo high_score, total_games, total_wins sang bang users
CREATE OR REPLACE FUNCTION fn_sync_user_game_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users
    SET
        total_games = total_games + 1,
        total_wins  = total_wins + CASE WHEN NEW.status = 'won' THEN 1 ELSE 0 END,
        high_score  = GREATEST(high_score, NEW.prize_won)
    WHERE id = NEW.user_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_game_sessions_sync_stats ON game_sessions;
CREATE TRIGGER trg_game_sessions_sync_stats
AFTER UPDATE ON game_sessions
FOR EACH ROW
WHEN (OLD.status = 'playing' AND NEW.status <> 'playing')
EXECUTE FUNCTION fn_sync_user_game_stats();
"""


#4. Ham khoi tao database

def init_db():
    # Chay tao bang, index va trigger trong cung 1 transaction
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            cur.execute(TRIGGER_SQL)
        conn.commit()
        print("OK da khoi tao 8 bang, indexes va trigger thanh cong")
    except Exception as e:
        conn.rollback()
        print(f"Loi khoi tao DB: {e}")
        raise
    finally:
        release_db_connection(conn)

if __name__ == "__main__":
    init_pool()
    init_db()
    close_pool()