# Quy Trình Cron Manager Mới

## 🎯 Tổng Quan

Cron Manager đã được cập nhật để chạy theo đúng quy trình thực tế:
1. **Gọi hàm get_data trước** để lấy dữ liệu từ database
2. **Kiểm tra dữ liệu** - chỉ chạy service khi có dữ liệu
3. **Chạy service chính** với dữ liệu đã lấy được

## 🔧 Thay Đổi Chính

### 1. Sử dụng UI và Browser hiện có
- **Không tạo mock UI** - sử dụng UI từ `main.py`
- **Không tạo browser mới** - sử dụng driver từ `browser.py`
- **Đảm bảo không mở nhiều giao diện**

### 2. Quy trình chạy service
```python
def _run_ftth_service(self):
    # 1. Kiểm tra driver có sẵn không
    if driver is None:
        logger.warning("❌ Browser driver chưa sẵn sàng, bỏ qua FTTH service")
        return
    
    # 2. Lấy root window hiện có
    root = get_root()
    if root is None:
        logger.warning("❌ UI root chưa sẵn sàng, bỏ qua FTTH service")
        return
    
    # 3. Gọi get_data trước để lấy dữ liệu
    ftth.get_data_ftth(root, None)
    
    # 4. Kiểm tra xem có dữ liệu không
    data_widget = self._find_ftth_data_widget(root)
    if not data_widget:
        logger.info("📭 Không tìm thấy widget dữ liệu FTTH")
        return
    
    data = data_widget.get("1.0", "end-1c").strip()
    if not data:
        logger.info("📭 Không có dữ liệu FTTH để xử lý")
        return
    
    # 5. Nếu có dữ liệu thì chạy service chính
    ftth.lookup_ftth(data_widget, root, None)
```

## 📋 Danh Sách Service

| Service | Function get_data | Function chính | Mô tả |
|---------|------------------|----------------|-------|
| **FTTH** | `get_data_ftth()` | `lookup_ftth()` | Tra cứu FTTH |
| **EVN** | `get_data_evn()` | `debt_electric()` | Gạch điện EVN |
| **Topup Multi** | `get_data_multi_network()` | `payment_phone()` | Nạp tiền đa mạng |
| **Topup Viettel** | `get_data_viettel()` | `payment_phone()` | Nạp tiền Viettel |
| **TV-Internet** | `get_data_tv_internet()` | `payment_internet()` | Thanh toán TV-Internet |
| **Postpaid** | `get_data_postpaid()` | `payment_phone()` | Tra cứu nợ trả sau |

## 🚀 Cách Sử Dụng

### 1. Khởi động UI và Browser
```bash
python app/main.py
```

### 2. Chạy Cron Manager
```bash
python cron_runner.py
```

### 3. Test quy trình
```bash
python demo_cron.py
```

## ⚠️ Lưu Ý Quan Trọng

### 1. Thứ tự khởi động
- **Bắt buộc**: Chạy `main.py` trước để khởi tạo UI và browser
- **Sau đó**: Chạy `cron_runner.py` để bắt đầu cron manager

### 2. Kiểm tra trạng thái
- Cron manager sẽ kiểm tra driver và UI trước khi chạy service
- Nếu không có driver/UI, service sẽ bị bỏ qua với cảnh báo

### 3. Logging chi tiết
- Mỗi bước đều có log rõ ràng
- Dễ dàng debug khi có lỗi

## 📊 Cấu Hình

### Global Settings
```json
{
  "max_concurrent_services": 2,
  "sequential_execution": true,
  "retry_failed_codes": true,
  "max_retries": 3
}
```

### Service Priority
1. **FTTH** (ưu tiên 1) - mỗi 25 phút
2. **Topup Multi** (ưu tiên 2) - mỗi 15 phút  
3. **Topup Viettel** (ưu tiên 3) - mỗi 15 phút
4. **TV-Internet** (ưu tiên 4) - mỗi 45 phút
5. **EVN** (ưu tiên 5) - mỗi 60 phút
6. **Postpaid** (ưu tiên 6) - mỗi 60 phút

## 🔍 Debug và Monitoring

### 1. Log files
- `app.log` - Log chính của ứng dụng
- `cron.log` - Log của cron manager

### 2. Trạng thái real-time
```python
status = cron.get_status()
print(f"Dịch vụ đang chạy: {status['active_count']}/{status['max_concurrent']}")
```

### 3. Kiểm tra service
```python
# Bật/tắt service
cron.enable_service('ftth', False)

# Cập nhật interval
cron.update_interval('ftth', 30)
```

## ✅ Kết Quả

- **Không mở nhiều giao diện** - sử dụng UI hiện có
- **Quy trình đúng** - get_data → kiểm tra → chạy service
- **Kiểm soát tốt** - chỉ chạy khi có dữ liệu
- **Logging rõ ràng** - dễ debug và monitor
- **Tương thích hoàn toàn** với code hiện tại

## 🎉 Kết Luận

Cron Manager mới đã hoàn thiện và sẵn sàng sử dụng với:
- ✅ Quy trình chạy service đúng chuẩn
- ✅ Sử dụng UI và browser hiện có
- ✅ Kiểm soát dữ liệu trước khi chạy
- ✅ Logging và monitoring chi tiết
- ✅ Cấu hình linh hoạt và dễ sử dụng
