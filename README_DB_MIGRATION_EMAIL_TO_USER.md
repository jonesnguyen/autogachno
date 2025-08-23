# Database Migration - Thay đổi từ email thành user

## Tổng quan
Đã thay đổi cột `email` thành `user` trong bảng `users` và `user_registrations` để phù hợp với yêu cầu sử dụng tên đăng nhập thay vì email.

## Thay đổi chính

### 1. Bảng `users`
- Thay đổi: `email` → `user`
- Trạng thái mặc định: `active` → `pending`
- Mục đích: Tài khoản mới đăng ký sẽ ở trạng thái chờ xét duyệt

### 2. Bảng `user_registrations`
- Thay đổi: `email` → `user`
- Mục đích: Đồng bộ với bảng users

## Cách thực hiện migration

### 1. Sử dụng Drizzle (Khuyến nghị)
```bash
npm run db:push
```

Lệnh này sẽ:
- Tự động đọc schema từ `shared/schema.ts`
- So sánh với database hiện tại
- Thay đổi cột `email` thành `user`
- Cập nhật trạng thái mặc định thành `pending`

### 2. Reset hoàn toàn database (Nếu cần)
Nếu bạn muốn xóa toàn bộ database và tạo lại từ đầu:

```bash
# Windows (PowerShell)
.\reset_database.ps1

# Windows (Command Prompt)
reset_database.bat

# Linux/Mac
chmod +x reset_database.sh
./reset_database.sh
```

### 3. SQL thủ công (Nếu cần giữ dữ liệu)
```sql
-- Thay đổi cột email thành user trong bảng users
ALTER TABLE users RENAME COLUMN email TO user;

-- Thay đổi cột email thành user trong bảng user_registrations
ALTER TABLE user_registrations RENAME COLUMN email TO user;

-- Cập nhật trạng thái mặc định cho tài khoản mới
ALTER TABLE users ALTER COLUMN status SET DEFAULT 'pending';

-- Cập nhật các tài khoản hiện có từ 'active' thành 'pending' (nếu cần)
UPDATE users SET status = 'pending' WHERE status = 'active' AND role = 'user';
```

## Cấu trúc mới

```typescript
// Trong shared/schema.ts
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  user: varchar("user").unique(), // Thay đổi từ email
  firstName: varchar("first_name"),
  lastName: varchar("last_name"),
  password: varchar("password"),
  profileImageUrl: varchar("profile_image_url"),
  role: userRoleEnum("role").default('user').notNull(),
  status: userStatusEnum("status").default('pending').notNull(), // Thay đổi từ 'active'
  expiresAt: timestamp("expires_at"),
  lastLoginAt: timestamp("last_login_at"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const userRegistrations = pgTable("user_registrations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  user: varchar("user").notNull().unique(), // Thay đổi từ email
  firstName: varchar("first_name").notNull(),
  lastName: varchar("last_name").notNull(),
  // ... các cột khác
});
```

## Thay đổi trong code

### 1. Frontend (Register.tsx)
- Thay đổi: `email` → `user`
- Placeholder: "your.email@example.com" → "Tên đăng nhập"
- Label: "Email *" → "User *"

### 2. Backend (Storage & Routes)
- Method: `getUserByEmail` → `getUserByUser`
- Field: `userData.email` → `userData.user`
- Validation: Kiểm tra tên đăng nhập thay vì email

### 3. API Endpoints
- `/api/users/:user/status` (thay vì `/api/auth/status/:email`)
- `/api/dev/login` sử dụng `user` thay vì `email`

## Lưu ý quan trọng

### 1. Trạng thái mặc định
- Tài khoản mới đăng ký sẽ có trạng thái `pending`
- Cần admin phê duyệt trước khi có thể sử dụng
- Tránh tình trạng tài khoản tự động active

### 2. Validation
- Tên đăng nhập phải là duy nhất
- Không cần format email
- Có thể sử dụng bất kỳ ký tự nào

### 3. Migration dữ liệu
- Nếu có dữ liệu cũ, cần backup trước khi migration
- Kiểm tra tính duy nhất của tên đăng nhập
- Cập nhật các foreign key references nếu cần

## Troubleshooting

### Nếu gặp lỗi khi chạy db:push:
1. Kiểm tra `DATABASE_URL` có đúng không
2. Đảm bảo database có quyền thay đổi cấu trúc bảng
3. Kiểm tra xem có dữ liệu nào vi phạm ràng buộc unique không

### Nếu muốn giữ dữ liệu cũ:
- Sử dụng SQL thủ công để rename cột
- Cập nhật dữ liệu nếu cần
- Chạy `npm run db:push` để đồng bộ schema

### Nếu cần rollback:
- Đổi tên cột từ `user` về `email`
- Cập nhật code về phiên bản cũ
- Chạy lại migration cũ
