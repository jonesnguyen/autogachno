@echo off
REM Script batch để reset database và chạy lại npm run db:push
REM Chạy script này để refresh hoàn toàn database

echo 🚀 Bắt đầu reset database...

REM Bước 1: Kiểm tra xem có đang ở thư mục gốc không
if not exist "package.json" (
    echo ❌ Không tìm thấy package.json. Hãy chạy script này từ thư mục gốc của project.
    pause
    exit /b 1
)

REM Bước 2: Kiểm tra DATABASE_URL
if "%DATABASE_URL%"=="" (
    echo ❌ Không tìm thấy DATABASE_URL. Hãy set environment variable này trước.
    echo Ví dụ: set DATABASE_URL=your_database_url_here
    pause
    exit /b 1
)

echo ✅ Tìm thấy DATABASE_URL

REM Bước 3: Chạy npm run db:push để tạo lại database
echo 🔄 Đang chạy npm run db:push...
call npm run db:push

if %ERRORLEVEL% EQU 0 (
    echo ✅ Database đã được tạo lại thành công!
    echo 🎉 Cột expires_at đã được thêm vào bảng users
) else (
    echo ❌ Có lỗi xảy ra khi chạy db:push
    pause
    exit /b 1
)

echo ✨ Hoàn thành! Database đã được refresh với cấu trúc mới.
pause
