# Test Server Status Script
# Chạy script này để kiểm tra server có hoạt động đúng không

Write-Host "🔍 Testing Server Status..." -ForegroundColor Green

$baseUrl = "http://localhost:5000"

# Test 1: Health check
Write-Host "`n1️⃣ Testing server health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/health" -Method Get
    Write-Host "✅ Server health OK: $($response.status)" -ForegroundColor Green
    Write-Host "   Uptime: $([math]::Round($response.uptime, 2)) seconds" -ForegroundColor Gray
    Write-Host "   Timestamp: $($response.timestamp)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Server health failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Database connection
Write-Host "`n2️⃣ Testing database connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/test/db" -Method Get
    Write-Host "✅ Database OK: $($response.message)" -ForegroundColor Green
    Write-Host "   User count: $($response.userCount)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Database failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test the problematic endpoint directly
Write-Host "`n3️⃣ Testing expiration endpoint structure..." -ForegroundColor Yellow
try {
    $testUrl = "$baseUrl/api/admin/users/test-id/expiration"
    $response = Invoke-WebRequest -Uri $testUrl -Method PATCH -Body '{"expiresAt":"2025-12-31"}' -ContentType "application/json"
    
    if ($response.StatusCode -eq 401) {
        Write-Host "✅ Endpoint exists but requires authentication (401)" -ForegroundColor Green
    } elseif ($response.StatusCode -eq 403) {
        Write-Host "✅ Endpoint exists but requires admin access (403)" -ForegroundColor Green
    } elseif ($response.StatusCode -eq 404) {
        Write-Host "❌ Endpoint not found (404)" -ForegroundColor Red
    } else {
        Write-Host "✅ Endpoint responded with status: $($response.StatusCode)" -ForegroundColor Green
    }
    
    Write-Host "   Response length: $($response.Content.Length) characters" -ForegroundColor Gray
    Write-Host "   Content-Type: $($response.Headers.'Content-Type')" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ Endpoint test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check if server is returning HTML instead of JSON
Write-Host "`n4️⃣ Checking response format..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/api/health" -Method Get
    $contentType = $response.Headers.'Content-Type'
    $content = $response.Content
    
    if ($contentType -and $contentType.Contains('application/json')) {
        Write-Host "✅ Health endpoint returns JSON correctly" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Health endpoint returns: $contentType" -ForegroundColor Yellow
    }
    
    if ($content.StartsWith('<!DOCTYPE') -or $content.StartsWith('<html')) {
        Write-Host "❌ WARNING: Server returning HTML instead of JSON!" -ForegroundColor Red
        Write-Host "   This indicates server error or misconfiguration" -ForegroundColor Red
    } else {
        Write-Host "✅ Response is not HTML" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Format check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 Diagnosis:" -ForegroundColor Cyan
Write-Host "1. If server health fails: Server is down" -ForegroundColor White
Write-Host "2. If database fails: Database connection issue" -ForegroundColor White
Write-Host "3. If endpoint 404: Route not defined" -ForegroundColor White
Write-Host "4. If HTML returned: Server error page" -ForegroundColor White

Write-Host "`n🔧 Next steps:" -ForegroundColor Cyan
Write-Host "1. Check server console for errors" -ForegroundColor White
Write-Host "2. Restart server if needed" -ForegroundColor White
Write-Host "3. Check database connection" -ForegroundColor White
Write-Host "4. Verify all routes are loaded" -ForegroundColor White

Write-Host "`n✨ Test completed!" -ForegroundColor Green
