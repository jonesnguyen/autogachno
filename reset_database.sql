-- Script để xóa toàn bộ database và tái tạo lại
-- Chạy script này để refresh hoàn toàn database

-- Xóa tất cả bảng theo thứ tự dependency
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

-- Xóa tất cả index (nếu có)
-- DROP INDEX IF EXISTS idx_users_expires_at CASCADE;
-- DROP INDEX IF EXISTS IDX_session_expire CASCADE;

-- Thông báo hoàn thành
SELECT 'Database đã được xóa hoàn toàn. Bây giờ chạy npm run db:push để tái tạo.' as message;
