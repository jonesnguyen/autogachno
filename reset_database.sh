#!/bin/bash
# Script shell để reset database và chạy lại npm run db:push
# Chạy script này để refresh hoàn toàn database

echo "🚀 Bắt đầu reset database..."

# Bước 1: Kiểm tra xem có đang ở thư mục gốc không
if [ ! -f "package.json" ]; then
    echo "❌ Không tìm thấy package.json. Hãy chạy script này từ thư mục gốc của project."
    exit 1
fi

# Bước 2: Kiểm tra DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Không tìm thấy DATABASE_URL. Hãy set environment variable này trước."
    echo "Ví dụ: export DATABASE_URL='your_database_url_here'"
    exit 1
fi

echo "✅ Tìm thấy DATABASE_URL"

# Bước 3: Chạy npm run db:push để tạo lại database
echo "🔄 Đang chạy npm run db:push..."
if npm run db:push; then
    echo "✅ Database đã được tạo lại thành công!"
    echo "🎉 Cột expires_at đã được thêm vào bảng users"
else
    echo "❌ Có lỗi xảy ra khi chạy db:push"
    exit 1
fi

echo "✨ Hoàn thành! Database đã được refresh với cấu trúc mới."
