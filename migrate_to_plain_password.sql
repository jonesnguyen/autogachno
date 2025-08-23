-- Migration script: Chuyển từ password hash sang password thuần túy
-- Chạy script này để cập nhật database

-- 1. Thêm cột password mới
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_new VARCHAR;

-- 2. Cập nhật password cho admin user (nếu có)
UPDATE users 
SET password_new = '123456' 
WHERE email = 'admin@local' OR email = 'Demodiemthu';

-- 3. Xóa các cột cũ
ALTER TABLE users DROP COLUMN IF EXISTS password_hash;
ALTER TABLE users DROP COLUMN IF EXISTS password_salt;

-- 4. Đổi tên cột password_new thành password
ALTER TABLE users RENAME COLUMN password_new TO password;

-- 5. Kiểm tra kết quả
SELECT id, email, password, role, status FROM users;
