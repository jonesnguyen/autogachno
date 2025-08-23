# Script test Admin API endpoints
# Chạy script này để test tính năng update user expiration

Write-Host "🧪 Testing Admin API Endpoints..." -ForegroundColor Green

$baseUrl = "http://localhost:5000"

# Test 1: Database connection
Write-Host "`n1️⃣ Testing database connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/test/db" -Method Get
    Write-Host "✅ Database connection successful" -ForegroundColor Green
    Write-Host "   Message: $($response.message)" -ForegroundColor Gray
    Write-Host "   User count: $($response.userCount)" -ForegroundColor Gray
    Write-Host "   Timestamp: $($response.timestamp)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Database connection failed" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Test update user (cần userId thực tế)
Write-Host "`n2️⃣ Testing user update..." -ForegroundColor Yellow
Write-Host "   Note: This test requires a valid userId from your database" -ForegroundColor Gray
Write-Host "   You can get userId from the admin panel or database" -ForegroundColor Gray

$testUserId = Read-Host "Enter a valid userId to test (or press Enter to skip)"
if ($testUserId) {
    try {
        $testData = @{
            userId = $testUserId
            expiresAt = "2025-12-31"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/test/update-user" -Method Post -Body $testData -ContentType "application/json"
        Write-Host "✅ Test update successful" -ForegroundColor Green
        Write-Host "   Message: $($response.message)" -ForegroundColor Gray
        Write-Host "   Method: $($response.method)" -ForegroundColor Gray
        Write-Host "   User ID: $($response.user.id)" -ForegroundColor Gray
        Write-Host "   Expires At: $($response.user.expiresAt)" -ForegroundColor Gray
    } catch {
        Write-Host "❌ Test update failed" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⏭️ Skipping user update test" -ForegroundColor Gray
}

Write-Host "`n🎯 Next steps:" -ForegroundColor Cyan
Write-Host "1. Check server console for detailed logs" -ForegroundColor White
Write-Host "2. Test admin panel in browser" -ForegroundColor White
Write-Host "3. Check database for actual changes" -ForegroundColor White
Write-Host "4. Verify expires_at column exists in users table" -ForegroundColor White

Write-Host "`n✨ Testing completed!" -ForegroundColor Green
