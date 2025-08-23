# 🚀 API Proxy Server Solution

Giải pháp để bypass browser CORS và network connectivity issues khi gọi API `thuhohpk.com`

## 🎯 **Vấn đề hiện tại:**

- ❌ **Browser Error:** `net::ERR_CONNECTION_RESET`
- ❌ **Network Issue:** `Failed to fetch`
- ❌ **Firewall/Proxy:** Chặn kết nối từ browser
- ✅ **Python Test:** Hoạt động bình thường

## 🔧 **Giải pháp:**

### **1. Multiple Proxy Endpoints (Đã implement):**
```typescript
const proxyEndpoints = [
  // Direct API (có thể bị chặn)
  `https://thuhohpk.com/api/list-bill-not-completed?service_type=${apiServiceType}`,
  // Public CORS proxies
  `https://cors-anywhere.herokuapp.com/...`,
  `https://api.allorigins.win/raw?url=...`,
  `https://thingproxy.freeboard.io/fetch/...`,
  // Local proxy server
  `http://localhost:5000/api/proxy/thuhohpk/${serviceType}`
];
```

### **2. Local Proxy Server (Khuyến nghị):**
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy proxy server
python server_api_proxy.py
```

## 🚀 **Cách sử dụng:**

### **Bước 1: Chạy Proxy Server**
```bash
cd "D:\PROJECT\2025\AutoGachno (1)\AutoGachno"
python server_api_proxy.py
```

**Output:**
```
🚀 Starting API Proxy Server...
🔐 Credentials: Demodiemthu:123456
📡 Available services: ['tra_cuu_ftth', 'gach_dien_evn', ...]
🌐 Server will run on http://localhost:5000
```

### **Bước 2: Test Proxy Server**
```bash
# Test proxy hoạt động
curl http://localhost:5000/api/proxy/test

# Health check
curl http://localhost:5000/api/proxy/health

# Call external API qua proxy
curl http://localhost:5000/api/proxy/thuhohpk/nap_tien_da_mang
```

### **Bước 3: Sử dụng trong React App**
Nút "Lấy dữ liệu từ thuhohpk.com" sẽ tự động thử các proxy endpoints theo thứ tự:

1. **Direct API** → Có thể bị chặn
2. **Public CORS proxies** → Có thể chậm/unreliable
3. **Local proxy server** → Nhanh và ổn định nhất

## 📊 **Proxy Server Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/proxy/test` | GET | Test proxy server |
| `/api/proxy/health` | GET | Health check |
| `/api/proxy/thuhohpk/{service_type}` | GET | Call external API |

## 🔍 **Service Types Supported:**

| Service Name | API Parameter | Status |
|--------------|---------------|---------|
| Tra cứu FTTH | `check_ftth` | ✅ |
| Gạch điện EVN | `env` | ✅ |
| Nạp tiền đa mạng | `deposit` | ✅ |
| Nạp tiền Viettel | `deposit_viettel` | ✅ |
| Thanh toán TV-Internet | `payment_tv` | ✅ |
| Tra cứu nợ trả sau | `check_debt` | ✅ |

## 💡 **Lợi ích của Proxy Server:**

1. **Bypass CORS:** Không có CORS issues
2. **Bypass Firewall:** Server-to-server communication
3. **Reliable:** Ổn định hơn public proxies
4. **Fast:** Local network, không có latency
5. **Secure:** Credentials được bảo vệ ở server side

## 🚨 **Lưu ý quan trọng:**

### **1. Firewall/Network Policy:**
- Nếu Python script hoạt động → Network policy chặn browser
- Nếu Python script không hoạt động → Vấn đề khác

### **2. CORS vs Network:**
- **CORS Error:** `Access to fetch at '...' from origin '...' has been blocked`
- **Network Error:** `net::ERR_CONNECTION_RESET` → Firewall/Proxy issue

### **3. Giải pháp theo thứ tự ưu tiên:**
1. ✅ **Local Proxy Server** (khuyến nghị)
2. 🔄 **Public CORS Proxies** (fallback)
3. ❌ **Direct API Call** (có thể bị chặn)

## 🔧 **Troubleshooting:**

### **Proxy Server không start:**
```bash
# Kiểm tra port 5000 có bị chiếm không
netstat -an | findstr :5000

# Kill process nếu cần
taskkill /F /PID <PID>
```

### **API call vẫn fail:**
```bash
# Test từ command line
curl -H "Authorization: Basic <base64_credentials>" \
     "https://thuhohpk.com/api/list-bill-not-completed?service_type=deposit"
```

### **Network connectivity:**
```bash
# Test DNS resolution
nslookup thuhohpk.com

# Test basic connectivity
ping thuhohpk.com
```

## 📞 **Support:**

Nếu gặp vấn đề:
1. **Chạy proxy server** trước
2. **Test endpoints** với curl
3. **Kiểm tra console logs** trong React app
4. **So sánh với Python test** để xác định vấn đề

## 🎯 **Kết luận:**

**Local Proxy Server** là giải pháp tốt nhất để bypass browser network issues. Nó sẽ:

- ✅ Bypass CORS restrictions
- ✅ Bypass firewall/proxy blocks  
- ✅ Cung cấp API endpoint ổn định
- ✅ Bảo vệ credentials
- ✅ Tăng performance

Hãy chạy `python server_api_proxy.py` và test lại nút "Lấy dữ liệu từ thuhohpk.com"! 🚀
