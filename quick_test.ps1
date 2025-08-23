# Quick test script for Admin API
Write-Host "🧪 Quick Admin API Test" -ForegroundColor Green

$baseUrl = "http://localhost:5000"

# Test 1: Database connection
Write-Host "`n1️⃣ Testing database connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/test/db" -Method Get
    Write-Host "✅ Database OK: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "❌ Database failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Get admin users (cần đăng nhập)
Write-Host "`n2️⃣ Testing admin users endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/admin/users" -Method Get
    Write-Host "✅ Admin users OK: Found $($response.users.Count) users" -ForegroundColor Green
} catch {
    Write-Host "❌ Admin users failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 Next steps:" -ForegroundColor Cyan
Write-Host "1. Check browser console for frontend logs" -ForegroundColor White
Write-Host "2. Check server console for backend logs" -ForegroundColor White
Write-Host "3. Try updating user expiration in admin panel" -ForegroundColor White
Write-Host "4. Look for detailed logging messages" -ForegroundColor White

Write-Host "`n✨ Test completed!" -ForegroundColor Green
