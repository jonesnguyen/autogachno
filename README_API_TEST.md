# 🧪 API Testing Tools

Các file Python để test và debug API `thuhohpk.com`

**⚠️ QUAN TRỌNG:** Hệ thống hiện tại CHỈ sử dụng API external `thuhohpk.com`, KHÔNG sử dụng API local.

## 📁 Files

- **`test_api.py`** - Test đầy đủ với tất cả service types
- **`test_simple.py`** - Test đơn giản và nhanh
- **`requirements.txt`** - Dependencies cần thiết
- **`test_browser.html`** - Test từ browser

## 🚀 Cài đặt

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Hoặc cài đặt trực tiếp
pip install requests urllib3
```

## 🔧 Sử dụng

### Test đơn giản (khuyến nghị)
```bash
python test_simple.py
```

### Test đầy đủ
```bash
python test_api.py
```

### Test từ browser
Mở file `test_browser.html` trong browser

## 📊 Các test được thực hiện

### 1. Basic Connectivity
- ✅ Kiểm tra kết nối cơ bản đến `thuhohpk.com`
- ✅ DNS resolution
- ✅ HTTP response status

### 2. API Endpoint Test
- ✅ Test tất cả service types
- ✅ Kiểm tra response format
- ✅ Parse dữ liệu JSON
- ✅ Xử lý lỗi HTTP

### 3. CORS Test
- ✅ OPTIONS request (preflight)
- ✅ CORS headers
- ✅ Cross-origin compatibility

## 🎯 Service Types Mapping

| Service Name | API Parameter |
|--------------|---------------|
| Tra cứu FTTH | `check_ftth` |
| Gạch điện EVN | `env` |
| Nạp tiền đa mạng | `deposit` |
| Nạp tiền Viettel | `deposit_viettel` |
| Thanh toán TV-Internet | `payment_tv` |
| Tra cứu nợ trả sau | `check_debt` |

## 🔍 Debug Information

### Authentication
API sử dụng **Basic Authentication**:
- **Username:** `Demodiemthu`
- **Password:** `123456`
- **Header:** `Authorization: Basic <base64_encoded_credentials>`

### Expected Response Format
```json
{
  "data": "0912345618,0912345618,0912345618,0912345618"
}
```

### Common Issues & Solutions

#### 1. Authentication Error (401 Unauthorized)
```
❌ HTTP 401: Unauthorized - {"message":"Unauthorized"}
```
**Giải pháp:**
- Sử dụng Basic Authentication thay vì Token header
- Kiểm tra username/password
- Đảm bảo credentials được encode base64 đúng cách

#### 2. CORS Error
```
❌ Network error - Không thể kết nối đến API. Có thể do CORS hoặc network issues.
```
**Giải pháp:**
- API server không cho phép cross-origin requests
- Cần proxy server hoặc backend API
- Xóa Origin header để tránh CORS preflight

#### 3. Network Error
```
❌ Connection error: [Errno 11001] getaddrinfo failed
```
**Giải pháp:**
- Kiểm tra internet connection
- Kiểm tra firewall/proxy
- Server có thể down

#### 4. Timeout Error
```
⏰ Timeout error - API không phản hồi trong 30 giây
```
**Giải pháp:**
- Server quá tải
- Network chậm
- Tăng timeout value

## 💡 Tips

1. **Chạy test_simple.py trước** để kiểm tra cơ bản
2. **Kiểm tra console output** để xem chi tiết lỗi
3. **So sánh với Postman** để đảm bảo API hoạt động
4. **Kiểm tra network** nếu có lỗi connection
5. **Test từ server** nếu có vấn đề CORS

## 🔄 Next Steps

**⚠️ LƯU Ý:** Hệ thống hiện tại CHỈ sử dụng API external `thuhohpk.com`

Sau khi xác định được lỗi cụ thể:

1. **CORS Issue** → Implement proxy server hoặc backend API
2. **Network Issue** → Kiểm tra infrastructure
3. **Auth Issue** → Refresh/update credentials
4. **Server Issue** → Liên hệ API provider

## 📞 Support

Nếu gặp vấn đề:
1. Chạy test và copy output
2. Kiểm tra console logs
3. So sánh với Postman collection
4. Kiểm tra network connectivity
5. **KHÔNG sử dụng API local** - chỉ dùng external API
