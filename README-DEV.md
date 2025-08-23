# 🚀 Hướng dẫn Môi trường Phát triển

## 📁 Các file runner có sẵn

### 1. **Auto-reload cơ bản** (Không cần cài thêm)
```bash
python dev_run.py
```
- ✅ Tự động restart khi thay đổi `app/main.py`
- ✅ Không cần cài đặt package nào thêm
- ✅ Phù hợp cho phát triển nhanh

### 2. **Debug mode với pdb**
```bash
python debug_run.py
```
- 🐛 Vào Python debugger tại `main()` function
- 🔍 Có thể debug từng bước
- 📍 Hữu ích khi cần kiểm tra biến và logic

### 3. **Auto-reload nâng cao với Watchdog**
```bash
# Cài đặt watchdog trước
pip install watchdog

# Chạy với auto-reload
python watchdog_run.py
```
- 🔄 Theo dõi tất cả file `.py` trong thư mục `app/`
- 🚀 Auto-restart ngay lập tức khi có thay đổi
- 💪 Tự động restart nếu process bị crash

## 🛠️ Cài đặt môi trường phát triển

### Cài đặt tất cả dependencies dev:
```bash
pip install -r requirements-dev.txt
```

### Hoặc cài từng package:
```bash
pip install watchdog python-dotenv
pip install pytest black flake8
pip install ipython jupyter
```

## 🎯 Cách sử dụng

### **Phát triển thường xuyên:**
```bash
# Terminal 1: Chạy auto-reload
python watchdog_run.py

# Terminal 2: Chỉnh sửa code
# Ứng dụng sẽ tự động restart!
```

### **Debug khi có lỗi:**
```bash
python debug_run.py
# Sử dụng các lệnh debug:
# n (next), s (step), c (continue), p <var>, l (list), q (quit)
```

### **Phát triển nhanh:**
```bash
python dev_run.py
# Chỉ restart khi thay đổi main.py
```

## 🔧 Lệnh debug cơ bản

Khi vào debugger (pdb):
```python
n           # Next - Bước tiếp theo
s           # Step - Bước vào function
c           # Continue - Tiếp tục chạy
p variable  # Print - In giá trị biến
l           # List - Hiển thị code xung quanh
q           # Quit - Thoát debugger
h           # Help - Hiển thị trợ giúp
```

## 💡 Tips phát triển

1. **Sử dụng `watchdog_run.py`** cho phát triển hàng ngày
2. **Sử dụng `debug_run.py`** khi cần debug logic
3. **Sử dụng `dev_run.py`** nếu không muốn cài thêm package
4. **Luôn có 2 terminal**: 1 chạy auto-reload, 1 chỉnh sửa code
5. **Sử dụng breakpoint** trong code: `import pdb; pdb.set_trace()`

## 🚨 Lưu ý

- **Auto-reload** chỉ restart ứng dụng, không giữ state
- **Debug mode** có thể làm chậm ứng dụng
- **Watchdog** cần quyền truy cập file system
- **Luôn test** trước khi commit code

## 🔄 Workflow phát triển

1. **Khởi động:** `python watchdog_run.py`
2. **Chỉnh sửa code** trong editor
3. **Lưu file** → Ứng dụng tự động restart
4. **Test** → Chỉnh sửa → Lặp lại
5. **Debug** khi cần: `python debug_run.py`
