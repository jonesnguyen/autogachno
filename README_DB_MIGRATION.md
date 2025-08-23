# Database Migration - Thêm cột expires_at

## Tổng quan
Đã thêm cột `expires_at` vào bảng `users` để quản lý thời hạn sử dụng của user.

## Cách thực hiện migration

### 1. Sử dụng Drizzle (Khuyến nghị)
```bash
npm run db:push
```

Lệnh này sẽ:
- Tự động đọc schema từ `shared/schema.ts`
- So sánh với database hiện tại
- Tạo cột `expires_at` nếu chưa tồn tại
- Tạo index `idx_users_expires_at` để tối ưu hiệu suất

### 2. Reset hoàn toàn database (Nếu cần)
Nếu bạn muốn xóa toàn bộ database và tạo lại từ đầu:

#### Sử dụng script tự động:
```bash
# Windows (PowerShell)
.\reset_database.ps1

# Windows (Command Prompt)
reset_database.bat

# Linux/Mac
chmod +x reset_database.sh
./reset_database.sh
```

#### Sử dụng SQL thủ công:
```sql
-- Xóa tất cả bảng
DROP TABLE IF EXISTS service_transactions CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS admin_logs CASCADE;
DROP TABLE IF EXISTS user_registrations CASCADE;
DROP TABLE IF EXISTS system_config CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Xóa tất cả enum types
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS service_type CASCADE;
DROP TYPE IF EXISTS order_status CASCADE;
DROP TYPE IF EXISTS transaction_status CASCADE;

-- Sau đó chạy: npm run db:push
```

## Cấu trúc cột mới

```typescript
// Trong shared/schema.ts
export const users = pgTable("users", {
  // ... các cột khác
  expiresAt: timestamp("expires_at"), // Thời hạn sử dụng user
  // ... các cột khác
});
```

## Tính năng mới

### 1. Hook useAuth
```typescript
const { user, isAuthenticated, isExpired, expiresAt } = useAuth();
```

### 2. Kiểm tra hết hạn tự động
- User chỉ được xem là authenticated nếu không hết hạn
- Trả về `isExpired: boolean` để kiểm tra trạng thái
- Trả về `expiresAt: Date | null` để hiển thị thời hạn

### 3. UI thông báo
- Trang Login hiển thị alert khi user hết hạn
- Trang Register có trường chọn thời hạn (tùy chọn)

## Lưu ý
- Cột `expires_at` có thể NULL (không có thời hạn)
- Khi NULL, user sẽ không bao giờ hết hạn
- Index được tạo tự động để tối ưu query kiểm tra hết hạn
- Tất cả thay đổi đã được tích hợp vào schema và sẽ được áp dụng khi chạy `npm run db:push`

## Troubleshooting

### Nếu gặp lỗi khi chạy db:push:
1. Kiểm tra `DATABASE_URL` có đúng không
2. Đảm bảo database có quyền tạo bảng
3. Nếu cần, sử dụng script reset để tạo lại từ đầu

### Nếu muốn giữ dữ liệu cũ:
- Chỉ chạy `npm run db:push` (không reset)
- Drizzle sẽ tự động thêm cột mới mà không mất dữ liệu
