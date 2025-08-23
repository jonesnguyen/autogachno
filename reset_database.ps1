# Script PowerShell để reset database và chạy lại npm run db:push
# Chạy script này để refresh hoàn toàn database

Write-Host "🚀 Bắt đầu reset database..." -ForegroundColor Green

# Bước 1: Kiểm tra xem có đang ở thư mục gốc không
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Không tìm thấy package.json. Hãy chạy script này từ thư mục gốc của project." -ForegroundColor Red
    exit 1
}

# Bước 2: Kiểm tra DATABASE_URL
if (-not $env:DATABASE_URL) {
    Write-Host "❌ Không tìm thấy DATABASE_URL. Hãy set environment variable này trước." -ForegroundColor Red
    Write-Host "Ví dụ: `$env:DATABASE_URL='your_database_url_here'" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Tìm thấy DATABASE_URL" -ForegroundColor Green

# Bước 3: Chạy npm run db:push để tạo lại database
Write-Host "🔄 Đang chạy npm run db:push..." -ForegroundColor Yellow
try {
    npm run db:push
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database đã được tạo lại thành công!" -ForegroundColor Green
        Write-Host "🎉 Cột expires_at đã được thêm vào bảng users" -ForegroundColor Green
    } else {
        Write-Host "❌ Có lỗi xảy ra khi chạy db:push" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Lỗi: $_" -ForegroundColor Red
    exit 1
}

Write-Host "✨ Hoàn thành! Database đã được refresh với cấu trúc mới." -ForegroundColor Green
