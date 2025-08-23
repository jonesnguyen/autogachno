# 🚀 Quick Reset Database

## Cách nhanh nhất để reset database:

### 1. Chạy script tự động (Khuyến nghị)
```bash
# Windows PowerShell
.\reset_database.ps1

# Windows Command Prompt  
reset_database.bat

# Linux/Mac
chmod +x reset_database.sh
./reset_database.sh
```

### 2. Chạy thủ công
```bash
# Bước 1: Đảm bảo DATABASE_URL đã set
echo $DATABASE_URL

# Bước 2: Chạy db:push
npm run db:push
```

### 3. Nếu muốn xóa database trước (SQL)
```sql
-- Kết nối vào database và chạy:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Sau đó chạy: npm run db:push
```

## ✅ Kết quả mong đợi:
- Database được tạo lại hoàn toàn
- Cột `expires_at` có trong bảng `users`
- Tất cả enum types và indexes được tạo
- Schema mới nhất được áp dụng

## 🔧 Nếu gặp lỗi:
1. Kiểm tra `DATABASE_URL`
2. Đảm bảo có quyền tạo database
3. Kiểm tra kết nối database
4. Chạy script reset tự động
