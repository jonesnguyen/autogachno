
# thuhohpk-like API (FastAPI)

Mô phỏng các endpoint từ Postman collection:
- GET /api/list-bill-not-completed
- POST /api/tool-bill-completed

## Yêu cầu
- Python 3.9+

## Cài đặt & chạy
```bash
cd thuhohpk_like_api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Tuỳ chọn: tạo file .env từ mẫu
copy .env.example .env  # trên Windows
# hoặc: cp .env.example .env  # trên Linux/macOS

# Chạy server
python main.py
# hoặc
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Xác thực
- Basic Auth: username/password (mặc định: Demodiemthu / 123456)
- Header: Token: c0d2e27448f511b41dd1477781025053

## Thử nhanh với curl
```bash
# Liệt kê bill chưa hoàn thành
curl -u Demodiemthu:123456 -H "Token: c0d2e27448f511b41dd1477781025053" "http://localhost:8000/api/list-bill-not-completed"

# Lọc theo service_type
curl -u Demodiemthu:123456 -H "Token: c0d2e27448f511b41dd1477781025053" "http://localhost:8000/api/list-bill-not-completed?service_type=deposit"

# Đánh dấu hoàn thành theo account
curl -u Demodiemthu:123456 -H "Token: c0d2e27448f511b41dd1477781025053" -X POST "http://localhost:8000/api/tool-bill-completed" -H "Content-Type: application/json" -d "{\"account\": \"0912345618\"}"
```

## Ghi chú
- Ứng dụng dùng bộ nhớ tạm thời (in-memory). Hãy thay bằng DB thật (SQLite/MySQL...) nếu cần.
- Các giá trị xác thực có thể chỉnh trong `.env`.
- Tài liệu Swagger: http://localhost:8000/docs
```
