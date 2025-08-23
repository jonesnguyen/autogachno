@echo off
chcp 65001 >nul
title AutoGachno Cron Manager

echo.
echo ========================================
echo    AutoGachno Cron Manager
echo ========================================
echo.

echo 🚀 Đang khởi động Cron Manager...
echo 📅 Thời gian: %date% %time%
echo.

echo 🔍 Kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Không tìm thấy Python. Vui lòng cài đặt Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python đã sẵn sàng
echo.

echo 🔍 Kiểm tra dependencies...
python -c "import schedule" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Thiếu thư viện schedule. Đang cài đặt...
    pip install schedule
    if errorlevel 1 (
        echo ❌ Không thể cài đặt schedule
        pause
        exit /b 1
    )
)

echo ✅ Dependencies đã sẵn sàng
echo.

echo 🧪 Chạy test...
python test_cron.py
if errorlevel 1 (
    echo ❌ Test thất bại
    pause
    exit /b 1
)

echo.
echo 🎯 Bắt đầu Cron Manager...
echo 💡 Nhấn Ctrl+C để dừng
echo.

python cron_runner.py

echo.
echo 👋 Cron Manager đã kết thúc
pause
