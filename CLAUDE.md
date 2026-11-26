# CLAUDE.md – Bàn giao dự án "Ai Là Triệu Phú" (OJT Backend)

> File này bàn giao bối cảnh từ phiên làm việc trên claude.ai sang Claude Code (VS Code).
> Đọc hết file này trước khi làm bất cứ việc gì trong repo.

---

## 1. Bối cảnh

- **Người dùng (owner repo):** senior developer, đang kèm em là **Nguyễn Bảo Ngọc** (sinh viên IT năm 3, tài khoản GitHub `baongocdev304`, Trello "Ngọc Nguyễn Bảo").
- **Mục tiêu:** em tự code lại backend game "Ai Là Triệu Phú" từ đầu theo kiến trúc 4 tầng + 6 Domain Blueprints, theo lộ trình 38 buổi.
- **Repo này (`kratosvn/altp`):** nơi em code lại dự án. Hiện mới có khung thư mục rỗng (xem mục 4).
- **Plan gốc:** https://github.com/baongocdev304/Game-who-want-to-be-a-millionaire/blob/main/PLAN.md
- **Code tham khảo (bản hoàn chỉnh):** https://github.com/baongocdev304/Game-who-want-to-be-a-millionaire

### Vai trò của Claude trong repo này
Claude đóng vai **mentor/reviewer**, KHÔNG phải người code hộ:
- Không viết sẵn code giải bài cho em. Chỉ gợi ý hướng, từ khóa, link docs, chỉ ra lỗi.
- Được phép: dựng khung thư mục/file rỗng, viết test, review code, giải thích khái niệm, viết tài liệu.
- Khi review: dựa trên tiêu chí ở mục 6.

---

## 2. Những gì đã làm (trên claude.ai)

1. **Board Trello "OJT – Ai Là Triệu Phú (Backend)"**: https://trello.com/b/nVKv8VrL
   - List: `📌 Kiến trúc & Luật chơi` → `To Do` → `Doing` → `Review` → `Done`
   - Card ghim: Luật chơi, Kiến trúc 4 tầng + 6 Domain Blueprints, 28 API endpoints
   - 38 ticket `[B01]`…`[B38]`, mỗi ngày 1 buổi, từ **27/11/2026 → 03/01/2027**, due 21:00 (giờ VN). Mỗi ticket có: file, nội dung, tiêu chí "Done khi".
   - Em đã là thành viên board.
2. **Board cũ "Lộ trình Backend Python 3 tháng"** (https://trello.com/b/CPrJApgU): plan FastAPI 12 tuần, đang tạm dừng, sẽ quay lại sau khi xong OJT.
3. **Scheduled task "Check tiến độ em lúc 22h"** (chạy ~21:59 hằng ngày trên MacBook của owner, qua Claude in Chrome):
   - Đọc hoạt động Trello hôm nay (chỉ tính hoạt động của em) + commit GitHub hôm nay.
   - Gửi Messenger cho em đúng 1 trong 2 câu cố định:
     - Có tiến triển: `tình hình sao rồi e`
     - Không có gì: `a chưa thấy e làm thêm gì hôm nay nhỉ, trello, github im ắng quá. Có vấn đề gì ko em`
   - Gửi không được → push notification cho owner.
   - ⚠️ Task hiện đang check repo `baongocdev304/Game-who-want-to-be-a-millionaire`. **Cần đổi sang `kratosvn/altp`** nếu em code ở repo này (sửa trên claude.ai).
4. File `lo-trinh-backend-3-thang.md` (plan cũ, giọng anh trai) đã gửi cho owner.

---

## 3. Luật chơi với em

1. Mỗi buổi = 1 ticket. Bắt đầu → kéo sang **Doing**; xong → kéo sang **Review** + comment link commit.
2. Code tự tay, không copy code AI. Chỉ hỏi AI để hiểu lỗi/khái niệm.
3. Commit nhỏ, message rõ ràng: `feat(auth): add register endpoint`, `fix(qa): ...`
4. Kẹt > 1 tiếng mới hỏi anh, kèm: đang làm gì, lỗi gì, đã thử gì.
5. Mỗi tối trước 22h nhắn daily report: Hôm nay làm / Commit / Đang kẹt / Mai làm / Số giờ code.
6. Chỉ anh được kéo ticket sang **Done**.

---

## 4. Cấu trúc thư mục (kiến trúc 4 tầng)

Phụ thuộc **một chiều**: Tầng 4 → Tầng 3 → Tầng 2 → Tầng 1.
**Cấm** circular import và **cấm** import chéo giữa các domain trong Tầng 3 (chia sẻ logic thì đưa xuống `services/`).

```text
altp/
├── app.py                          # Tầng 4 – WSGI root (Gunicorn/Docker)
├── database.py                     # Tầng 1 – ThreadedConnectionPool, schema 8 bảng, index, trigger trg_win_rate
├── .env.example                    # Tầng 1 – mẫu biến môi trường (KHÔNG commit .env)
├── requirements.txt
├── Dockerfile                      # (B38)
├── docker-compose.yml              # (B38)
├── docker-entrypoint.sh            # (B38)
├── PLAN.md                         # copy plan gốc
├── backend/
│   ├── __init__.py
│   ├── app.py                      # Tầng 4 – create_app(), đăng ký blueprints, PWA routes
│   ├── config.py                   # Tầng 1 – class Config, clean_env()
│   ├── core/                       # Tầng 2A
│   │   ├── __init__.py
│   │   ├── extensions.py           # get_db/close_db (flask.g), standalone_db_connection(), CORS
│   │   ├── security.py             # bcrypt, @login_required, @debug_access_required
│   │   └── constants.py            # PRIZE_LEVELS, MILESTONES, SHOP_PRICES, regex SePay
│   ├── services/                   # Tầng 2B
│   │   ├── __init__.py
│   │   ├── mail_service.py
│   │   ├── wallet_service.py
│   │   ├── game_service.py         # GameSessionStore, record_game_result()
│   │   ├── gemini_service.py       # Lazy Singleton Gemini client
│   │   └── question_bank.py        # 45 câu offline + fallback
│   └── domains/                    # Tầng 3
│       ├── __init__.py             # register_blueprints(app)
│       ├── auth/       (auth_bp)       __init__, register, login, logout, forgotpass
│       ├── gameplay/   (game_bp)       __init__, game_session, qa, supports, stopped, endtime
│       ├── ai/         (ai_bp)         __init__, chatbot, translate
│       ├── ranking/    (ranking_bp)    __init__, history, rank
│       ├── shop/       (shop_bp)       __init__, shop, bank
│       └── debug/      (debug_bp)      __init__, debug
├── templates/                      # signin.html, index.html, shop.html (B37)
├── static/                         # js/game.js, manifest.json, sw.js (B36–B37)
└── tests/                          # test theo từng domain
```

Khung này dựng bằng `scripts/scaffold.sh` (chỉ tạo file rỗng có docstring TODO, không có code giải).

**Stack:** Python 3.11+, Flask (Blueprints + Application Factory), PostgreSQL (`psycopg2` ThreadedConnectionPool), `bcrypt`, `google-genai`, SePay VietQR webhook, Docker, Gunicorn, port **5002**.

---

## 5. Lộ trình 38 buổi (khớp ticket Trello)

| Buổi | Ngày | Nội dung | File chính |
|---|---|---|---|
| B01 | 27/11 | Config & DB Pool | `backend/config.py`, `database.py` |
| B02 | 28/11 | Core extensions, vòng đời DB | `core/extensions.py` |
| B03 | 29/11 | bcrypt, `@login_required`, `@debug_access_required` | `core/security.py` |
| B04 | 30/11 | Auth Blueprint + Đăng ký | `domains/auth/register.py` |
| B05 | 01/12 | Đăng nhập, session, `/api/auth/me` | `domains/auth/login.py` |
| B06 | 02/12 | Application Factory + WSGI | `backend/app.py`, `app.py`, `domains/__init__.py` |
| B07 | 03/12 | Ôn tập tuần 1 | — |
| B08 | 04/12 | Đăng xuất | `domains/auth/logout.py` |
| B09 | 05/12 | Mail service SMTP | `services/mail_service.py` |
| B10 | 06/12 | Quên MK – gửi OTP | `domains/auth/forgotpass.py` |
| B11 | 07/12 | Quên MK – xác thực & đổi MK | `domains/auth/forgotpass.py` |
| B12 | 08/12 | Constants + Wallet service | `core/constants.py`, `services/wallet_service.py` |
| B13 | 09/12 | Game service | `services/game_service.py` |
| B14 | 10/12 | `POST /api/game/start` | `domains/gameplay/game_session.py` |
| B15 | 11/12 | Trả lời ĐÚNG | `domains/gameplay/qa.py` |
| B16 | 12/12 | Trả lời SAI, mốc an toàn, thắng câu 15 | `domains/gameplay/qa.py` |
| B17 | 13/12 | 50:50 + bonus lifeline | `domains/gameplay/supports.py` |
| B18 | 14/12 | Gọi điện & Khán giả | `domains/gameplay/supports.py` |
| B19 | 15/12 | Dừng cuộc chơi | `domains/gameplay/stopped.py` |
| B20 | 16/12 | Hết giờ 30s | `domains/gameplay/endtime.py` |
| B21 | 17/12 | Test liên hoàn Gameplay | `tests/` |
| B22 | 18/12 | Gemini Lazy Singleton | `services/gemini_service.py` |
| B23 | 19/12 | Prompt + validate JSON 15 câu | `services/gemini_service.py` |
| B24 | 20/12 | Question bank offline | `services/question_bank.py` |
| B25 | 21/12 | Nối AI + fallback vào game start | `domains/gameplay/game_session.py` |
| B26 | 22/12 | Chatbot MC | `domains/ai/chatbot.py` |
| B27 | 23/12 | Dịch câu hỏi | `domains/ai/translate.py` |
| B28 | 24/12 | Test & tối ưu AI (mock) | `tests/` |
| B29 | 25/12 | Lịch sử đấu | `domains/ranking/history.py` |
| B30 | 26/12 | Bảng xếp hạng Top 10 | `domains/ranking/rank.py` |
| B31 | 27/12 | Ví, check-status, lịch sử nạp | `domains/shop/shop.py` |
| B32 | 28/12 | Tạo đơn + VietQR | `domains/shop/shop.py` |
| B33 | 29/12 | Xác thực SePay webhook + log độc lập | `domains/shop/bank.py` |
| B34 | 30/12 | Đối soát regex, idempotency, cộng lượt | `domains/shop/bank.py` |
| B35 | 31/12 | Debug endpoints + khóa production | `domains/debug/debug.py` |
| B36 | 01/01 | Đọc hiểu `static/js/game.js` | `static/js/game.js` |
| B37 | 02/01 | Templates + PWA | `templates/`, `static/` |
| B38 | 03/01 | Docker, Gunicorn, regression 28 endpoint, deploy | `Dockerfile`, `docker-compose.yml` |

Chi tiết từng buổi: xem ticket Trello tương ứng hoặc `PLAN.md`.

### 28 endpoint
Auth: `GET /`, `GET /auth`, `POST /api/auth/register|login|logout|forgot-password|verify-reset-code`, `GET /api/auth/me`
Gameplay: `POST /api/game/start|answer|lifeline|stop|timeout`
AI: `POST /api/chatbot`, `POST /api/translate`
Ranking: `GET /api/game/history`, `GET /api/leaderboard`
Shop: `GET /api/shop/wallet|check-status|history`, `POST /api/shop/create-order`, `POST /api/shop/webhook`, `POST /api/webhook/sepay`
Debug: `GET /api/debug/status|webhooks|transaction/<ref>`
PWA: `GET /manifest.json`, `GET /sw.js`

---

## 6. Tiêu chí review code

- **Kiến trúc:** đúng tầng, không import ngược tầng, không import chéo domain.
- **Đặt tên:** rõ nghĩa; trong gameplay dùng `game_sess`, không ghi đè `flask.session`.
- **Hàm:** mỗi hàm 1 việc, ≲ 30 dòng.
- **Lỗi & HTTP status:** 400/401/403/404 đúng chỗ, JSON response thống nhất.
- **DB:** dùng `get_db()`, không leak connection, transaction đúng; ghi log độc lập dùng `standalone_db_connection()`.
- **Bảo mật:** không commit `.env`/secret; bcrypt; check quyền sở hữu `session_id`/đơn hàng theo `user_id`.
- **Commit:** nhỏ, message rõ, không dồn 1 cục.
- **Hiểu code:** em phải giải thích được từng dòng.

---

## 7. Việc còn mở

- [ ] Đổi repo theo dõi trong scheduled task 22h sang `kratosvn/altp` (làm trên claude.ai).
- [ ] Cấp quyền push repo `kratosvn/altp` cho `baongocdev304` (collaborator).
- [ ] Copy `PLAN.md` vào repo.
- [ ] Sau OJT: quay lại board "Lộ trình Backend Python 3 tháng".
