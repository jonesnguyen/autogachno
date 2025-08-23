# Cấu Trúc Service Manager Mới

## 🎯 Tổng Quan

Thay vì có 6 file service riêng biệt, chúng ta đã tạo **1 file chung** `service_manager.py` chứa:

- **12 hàm chính** (2 hàm cho mỗi service)
- **4 hàm điều khiển Selenium chung**
- **Cấu trúc thống nhất** cho tất cả service

## 📋 Danh Sách 12 Hàm Chính

### 1. **FTTH Service** (2 hàm)
- `get_data_ftth()` - Get dữ liệu từ database
- `lookup_ftth()` - Bắt đầu tra cứu FTTH

### 2. **EVN Service** (2 hàm)  
- `get_data_evn()` - Get dữ liệu từ database
- `debt_electric()` - Bắt đầu gạch điện EVN

### 3. **Topup Multi Service** (2 hàm)
- `get_data_multi_network()` - Get dữ liệu từ database
- `payment_phone_multi()` - Bắt đầu nạp tiền đa mạng

### 4. **Topup Viettel Service** (2 hàm)
- `get_data_viettel()` - Get dữ liệu từ database
- `payment_phone_viettel()` - Bắt đầu nạp tiền Viettel

### 5. **TV-Internet Service** (2 hàm)
- `get_data_tv_internet()` - Get dữ liệu từ database
- `payment_internet()` - Bắt đầu thanh toán TV-Internet

### 6. **Postpaid Service** (2 hàm)
- `get_data_postpaid()` - Get dữ liệu từ database
- `payment_phone_postpaid()` - Bắt đầu tra cứu nợ trả sau

## 🔧 4 Hàm Điều Khiển Selenium Chung

### 1. `navigate_to_page(service_name, target_url)`
- Điều hướng đến trang service
- Kiểm tra driver có sẵn không
- Xử lý lỗi chung

### 2. `wait_for_element(element_id, timeout)`
- Chờ element xuất hiện
- Sử dụng WebDriverWait
- Trả về element hoặc None

### 3. `click_element(element_id, timeout)`
- Click vào element
- Tự động chờ element xuất hiện
- Xử lý lỗi click

### 4. `fill_input(element_id, value, timeout)`
- Điền giá trị vào input
- Tự động clear trước khi điền
- Xử lý lỗi điền

## 🏗️ Cấu Trúc Mỗi Hàm

### Hàm Get Data (6 hàm)
```python
def get_data_[service_name](text_widget, ...):
    try:
        # 1. Lấy dữ liệu từ database/API
        data = db_fetch_service_data(service_key)
        
        # 2. Xử lý dữ liệu
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # 3. Ghép code|order_id
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = m.get("code", "").strip()
                oid = m.get("orderId", "")
                display_codes.append(f"{code_clean}|{oid}")
            
            # 4. Hiển thị lên UI
            populate_text_widget(text_widget, display_codes)
            
            # 5. Log kết quả
            logger.info(f"Đã tải {len(codes)} mã {service_name}")
        else:
            logger.info(f"Không có dữ liệu {service_name} từ DB")
            
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu {service_name}: {e}")
```

### Hàm Bắt Đầu (6 hàm)
```python
def [action_name](tkinp_ctm, tkinp_ctmed, ...):
    try:
        # 1. Chuẩn bị UI
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        # 2. Lấy dữ liệu từ text widget
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # 3. Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                # 4. Xử lý mã cụ thể
                logger.info(f"Đang xử lý {service_name}: {cbil}")
                # TODO: Gọi hàm xử lý cụ thể
                data_rows.append([cbil, "Đã xử lý", f"{service_name} ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý {service_name} {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # 5. Xuất Excel
        if data_rows:
            export_excel(data_rows, f"Tên thư mục {service_name}")
            
    except Exception as e:
        logger.error(f"Lỗi {service_name}: {e}")
```

## ✅ Lợi Ích Của Cấu Trúc Mới

### 1. **Tập trung hóa**
- Tất cả logic trong 1 file
- Dễ bảo trì và cập nhật
- Không bị phân tán

### 2. **Thống nhất**
- Cấu trúc giống nhau cho tất cả service
- Xử lý lỗi thống nhất
- Logging thống nhất

### 3. **Tái sử dụng**
- Hàm Selenium chung cho tất cả service
- Không duplicate code
- Dễ mở rộng

### 4. **Quản lý dễ dàng**
- Import từ 1 nơi duy nhất
- Dependencies rõ ràng
- Testing đơn giản

## 🔄 Cách Sử Dụng

### 1. Import tất cả hàm
```python
from app.services.service_manager import (
    # FTTH
    get_data_ftth, lookup_ftth,
    
    # EVN
    get_data_evn, debt_electric,
    
    # Topup Multi
    get_data_multi_network, payment_phone_multi,
    
    # Topup Viettel
    get_data_viettel, payment_phone_viettel,
    
    # TV-Internet
    get_data_tv_internet, payment_internet,
    
    # Postpaid
    get_data_postpaid, payment_phone_postpaid,
    
    # Selenium Control
    navigate_to_page, wait_for_element, click_element, fill_input
)
```

### 2. Sử dụng trong UI
```python
# Button Get dữ liệu
tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", 
                           command=lambda: get_data_ftth(tkinp_ctm, None))

# Button Bắt đầu  
tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu",
                          command=lambda: lookup_ftth(tkinp_ctm, tkinp_ctmed, None))
```

### 3. Sử dụng Selenium chung
```python
# Điều hướng
navigate_to_page("FTTH", "https://example.com/ftth")

# Chờ element
element = wait_for_element("input_id", 10)

# Click element
click_element("button_id", 5)

# Điền input
fill_input("input_id", "value", 5)
```

## 🎯 Kết Luận

Cấu trúc mới này giúp:

- ✅ **Tập trung hóa** tất cả service vào 1 file
- ✅ **Thống nhất** cấu trúc và xử lý lỗi
- ✅ **Tái sử dụng** code Selenium chung
- ✅ **Dễ bảo trì** và mở rộng
- ✅ **Quản lý** dependencies đơn giản

Thay vì 6 file riêng biệt, giờ chỉ cần 1 file `service_manager.py` chứa tất cả 16 hàm (12 hàm chính + 4 hàm Selenium chung)!
