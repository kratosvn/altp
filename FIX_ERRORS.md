# Hướng Dẫn Khắc Phục 5 Test FAIL (B01 – B02 – B03)

Tài liệu này tổng hợp **3 nguyên nhân gốc** gây ra **5/11 test FAIL** khi chạy [test_core.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/test_core.py), kèm checklist để bạn tự sửa lần lượt theo đúng thứ tự phụ thuộc (Tầng 1 → Tầng 2).

---

## Tóm tắt ánh xạ lỗi

| Nhóm lỗi | Test case bị FAIL | File cần kiểm tra / sửa |
| :--- | :--- | :--- |
| **Lỗi 1:** Chưa có code `database.py` ở nhánh hiện tại | • `test_b02_standalone_db_connection_select_1_and_error_recovery`<br>• `test_b02_ping_db_route_and_teardown`<br>• `test_b02_cors_headers_on_valid_origin` | [database.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/database.py#L1)<br>[extensions.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/extensions.py#L6-L11) |
| **Lỗi 2:** Thiếu biến `DATABASE_URL` trong `.env` | • `test_b01_config_database_url`<br>• *(Ảnh hưởng trực tiếp đến `init_pool()` ở B02 sau khi sửa Lỗi 1)* | [.env](file:///Users/nguyenbaongoc/TUHOCGAME/altp/.env#L1-L12)<br>[config.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/config.py#L29) |
| **Lỗi 3:** `hash_password()` chưa chặn đầu vào `""` / `None` | • `test_b03_hash_password_empty_and_none` | [security.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/security.py#L7-L10) |

---

## Chi tiết cách khắc phục từng lỗi

### 1. Lỗi 1 — Gộp code `database.py` từ nhánh B01 (Giải quyết 3 lỗi `ImportError` ở B02)

- **Triệu chứng:**
  ```text
  ImportError: cannot import name 'get_db_connection' from 'database'
  ```
  tại [extensions.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/extensions.py#L6-L11).
- **Nguyên nhân:**
  Nhánh hiện tại (`feat/core_extentions_n_vong_doi_database`) được rẽ từ `main` trước khi nhánh `feat/config_database_pool` (commit `2db1523`) được gộp vào. Vì vậy [database.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/database.py#L1) ở nhánh này vẫn đang là file khung rỗng 1 dòng.
- **Cách sửa:**
  - [x] Gộp nhánh `feat/config_database_pool` vào nhánh hiện tại:
    ```zsh
    git merge feat/config_database_pool
    ```
  - [x] Mở lại [database.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/database.py) xác nhận đã có đủ 4 hàm mà [extensions.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/extensions.py#L6-L11) đang import: `init_pool`, `get_db_connection`, `release_db_connection`, `init_db`.

---

### 2. Lỗi 2 — Bổ sung `DATABASE_URL` vào `.env` (Giải quyết lỗi B01 & kết nối PostgreSQL cho B02)

- **Triệu chứng:**
  ```text
  AssertionError: Config.DATABASE_URL đang rỗng ('') — thiếu biến DATABASE_URL trong .env
  ```
  tại [config.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/config.py#L29).
- **Nguyên nhân:**
  File [.env](file:///Users/nguyenbaongoc/TUHOCGAME/altp/.env#L1-L12) hiện chưa có khai báo `DATABASE_URL`. Khi `clean_env("DATABASE_URL")` chạy sẽ trả về giá trị mặc định `""`.
- **Cách sửa:**
  - [x] Mở [.env](file:///Users/nguyenbaongoc/TUHOCGAME/altp/.env) và thêm dòng cấu hình PostgreSQL thật trên máy của bạn:
    ```env
    DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<ten_db>
    ```
    *(Ví dụ: `postgresql://postgres:123456@localhost:5432/altp` — không để comment `# ...` trên cùng dòng với `DATABASE_URL` vì `database.py` đang đọc bằng `os.getenv("DATABASE_URL")`).*
  - [x] Đảm bảo PostgreSQL service trên máy đang bật và database `<ten_db>` đã được tạo sẵn.
  - [x] *(Lưu ý Git)*: Bạn đã đổi tên `.env.example` thành `.env` nên Git đang ghi nhận `D .env.example`. Hãy khôi phục lại file mẫu để không làm mất `.env.example` trên repo:
    ```zsh
    git restore .env.example
    ```

---

### 3. Lỗi 3 — Validate đầu vào trong `hash_password()` (Giải quyết lỗi B03)

- **Triệu chứng:**
  ```text
  AttributeError: 'NoneType' object has no attribute 'encode'
  ```
  tại [security.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/security.py#L9) khi gọi `hash_password(None)`, và không ném `ValueError` khi gọi `hash_password("")`.
- **Nguyên nhân:**
  - Ở `check_password()` (dòng 15–16), bạn đã chặn tốt trường hợp rỗng/`None` (`if not plain_text or not hashed_text: return False`).
  - Tuy nhiên ở `hash_password()` (dòng 7–10), bạn gọi thẳng `plain_text.encode("utf-8")` mà chưa kiểm tra `plain_text`. Hậu quả:
    1. Truyền `None` làm chương trình crash `AttributeError` thay vì báo lỗi dữ liệu đầu vào hợp lệ (`ValueError`).
    2. Truyền `""` vẫn băm ra chuỗi hash, nhưng sau đó `check_password("", hashed)` luôn trả về `False` (bất nhất logic).
- **Hướng tự sửa tại [security.py](file:///Users/nguyenbaongoc/TUHOCGAME/altp/backend/core/security.py#L7-L10):**
  - [x] Ngay đầu hàm `hash_password(plain_text: str) -> str`, thêm câu lệnh kiểm tra: nếu `plain_text` không phải `str` (`not isinstance(plain_text, str)`) **hoặc** là chuỗi rỗng (`not plain_text`) thì chủ động `raise ValueError(...)` với thông báo rõ ràng trước khi gọi `bcrypt.hashpw(...)`.

---

## Bước kiểm tra lại sau khi sửa xong

Chạy lại bộ kiểm thử bằng Python trong `.venv`:

```zsh
.venv/bin/python test_core.py
```

- [x] Xác nhận toàn bộ **11/11 test cases báo `PASSED`**.
- [x] Kiểm tra `git status` & `git diff` trước khi commit (đảm bảo không commit nhầm `.env`).
