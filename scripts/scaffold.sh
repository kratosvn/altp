#!/usr/bin/env bash
# Dựng khung thư mục 4 tầng cho dự án Ai Là Triệu Phú.
# Chỉ tạo file rỗng có docstring TODO – KHÔNG chứa code giải. Không ghi đè file đã có.
# Chạy ở thư mục gốc repo:  bash scripts/scaffold.sh
set -euo pipefail

mk() {  # mk <path> <docstring>
  local path="$1" doc="$2"
  mkdir -p "$(dirname "$path")"
  if [ -e "$path" ]; then echo "skip  $path"; return; fi
  case "$path" in
    *.py) printf '"""%s"""\n' "$doc" > "$path" ;;
    *)    : > "$path" ;;
  esac
  echo "create $path"
}

# Tầng 1
mk database.py              "Tầng 1 – ThreadedConnectionPool, init_pool, get/release_connection, create_schema (8 bảng, index, trigger trg_win_rate). TODO: B01"
mk backend/__init__.py      "Backend package."
mk backend/config.py        "Tầng 1 – class Config, clean_env(). TODO: B01"

# Tầng 2A – Core
mk backend/core/__init__.py      "Tầng 2A – Core."
mk backend/core/extensions.py    "get_db/close_db trên flask.g, standalone_db_connection(), init_extensions (CORS), init_db_schema. TODO: B02"
mk backend/core/security.py      "hash_password/check_password (bcrypt), @login_required, @debug_access_required. TODO: B03"
mk backend/core/constants.py     "PRIZE_LEVELS, MILESTONES, SHOP_PRICES, AMT_REF_PATTERN, LEGACY_REF_PATTERN, format_prize, get_safe_prize. TODO: B12"

# Tầng 2B – Services
mk backend/services/__init__.py        "Tầng 2B – Services."
mk backend/services/mail_service.py    "send_email_code(receiver_email, code) qua SMTP, fallback log console. TODO: B09"
mk backend/services/wallet_service.py  "get_or_create_wallet, deduct_game_turn, deduct_bonus_lifeline, credit_wallet (SAVEPOINT). TODO: B12"
mk backend/services/game_service.py    "GameSessionStore, record_game_result. TODO: B13"
mk backend/services/gemini_service.py  "Lazy Singleton get_gemini_client, generate_questions_with_ai, generate_mc_reply, translate_question_with_ai. TODO: B22-B27"
mk backend/services/question_bank.py   "45 câu offline (LOCAL_EASY/MEDIUM/HARD_QUESTIONS), get_local_fallback_questions. TODO: B24"

# Tầng 3 – Domains
mk backend/domains/__init__.py   "register_blueprints(app) – đăng ký 6 blueprint. TODO: B06"

mk backend/domains/auth/__init__.py    "auth_bp = Blueprint('auth', __name__). TODO: B04"
mk backend/domains/auth/register.py    "POST /api/auth/register. TODO: B04"
mk backend/domains/auth/login.py       "POST /api/auth/login, GET /api/auth/me, GET /, GET /auth. TODO: B05"
mk backend/domains/auth/logout.py      "POST /api/auth/logout. TODO: B08"
mk backend/domains/auth/forgotpass.py  "POST /api/auth/forgot-password, POST /api/auth/verify-reset-code. TODO: B10-B11"

mk backend/domains/gameplay/__init__.py      "game_bp = Blueprint('gameplay', __name__). TODO: B14"
mk backend/domains/gameplay/game_session.py  "POST /api/game/start. TODO: B14, B25"
mk backend/domains/gameplay/qa.py            "POST /api/game/answer. TODO: B15-B16"
mk backend/domains/gameplay/supports.py      "POST /api/game/lifeline (5050, phone, audience). TODO: B17-B18"
mk backend/domains/gameplay/stopped.py       "POST /api/game/stop. TODO: B19"
mk backend/domains/gameplay/endtime.py       "POST /api/game/timeout. TODO: B20"

mk backend/domains/ai/__init__.py   "ai_bp = Blueprint('ai', __name__). TODO: B26"
mk backend/domains/ai/chatbot.py    "POST /api/chatbot. TODO: B26"
mk backend/domains/ai/translate.py  "POST /api/translate. TODO: B27"

mk backend/domains/ranking/__init__.py  "ranking_bp = Blueprint('ranking', __name__). TODO: B29"
mk backend/domains/ranking/history.py   "GET /api/game/history. TODO: B29"
mk backend/domains/ranking/rank.py      "GET /api/leaderboard. TODO: B30"

mk backend/domains/shop/__init__.py  "shop_bp = Blueprint('shop', __name__). TODO: B31"
mk backend/domains/shop/shop.py      "GET wallet/check-status/history, POST create-order. TODO: B31-B32"
mk backend/domains/shop/bank.py      "POST /api/shop/webhook, /api/webhook/sepay. TODO: B33-B34"

mk backend/domains/debug/__init__.py  "debug_bp = Blueprint('debug', __name__). TODO: B35"
mk backend/domains/debug/debug.py     "GET /api/debug/status|webhooks|transaction/<ref>. TODO: B35"

# Tầng 4
mk backend/app.py  "Tầng 4 – create_app(): Config, extensions, blueprints, schema, PWA routes. TODO: B06"
mk app.py          "Tầng 4 – WSGI root cho Gunicorn/Docker. TODO: B06"

# Khác
mk tests/__init__.py "Tests."
mkdir -p templates static/js && echo "create templates/ static/js/"

[ -e requirements.txt ] || cat > requirements.txt <<'EOF'
flask
flask-cors
psycopg2-binary
bcrypt
python-dotenv
google-genai
gunicorn
pytest
EOF

[ -e .env.example ] || cat > .env.example <<'EOF'
# Copy thành .env và điền giá trị thật. KHÔNG commit .env
FLASK_ENV=development
SECRET_KEY=
DATABASE_URL=postgresql://user:password@localhost:5432/altp
GEMINI_API_KEY=
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SEPAY_BANK_CODE=
SEPAY_ACCOUNT_NUMBER=
SEPAY_WEBHOOK_SECRET=
ADMIN_DEBUG_KEY=
PORT=5002
EOF

[ -e .gitignore ] || cat > .gitignore <<'EOF'
.env
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
EOF

echo "Xong. Kiểm tra: tree -I '__pycache__|.venv'"
