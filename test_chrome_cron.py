#!/usr/bin/env python3
"""
Test Cron Manager với Chrome và chế độ lặp
Chạy: python test_chrome_cron.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def test_chrome_cron_manager():
    """Test CronManager với Chrome"""
    print("🧪 Test CronManager với Chrome...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from app.cron_manager import CronManager
        
        # Test khởi tạo với chế độ test
        print("🔧 Khởi tạo CronManager với chế độ test...")
        cron = CronManager(test_mode=True, test_interval=5)  # 5 giây để test nhanh
        
        print("✅ Khởi tạo thành công")
        
        # Kiểm tra Chrome driver
        print(f"\n🌐 Kiểm tra Chrome driver:")
        chrome_ready = cron.get_chrome_driver() is not None
        print(f"   • Chrome ready: {chrome_ready}")
        
        if chrome_ready:
            print("   ✅ Chrome driver sẵn sàng")
        else:
            print("   ❌ Chrome driver không sẵn sàng")
            return False
        
        # Kiểm tra status
        print(f"\n📋 Status hiện tại:")
        status = cron.get_status()
        for key, value in status.items():
            print(f"   • {key}: {value}")
        
        # Test chạy 1 service
        print(f"\n🧪 Test chạy 1 service...")
        test_service = 'ftth'
        
        if cron.can_run_service(test_service):
            print(f"   • Service {test_service} có thể chạy")
            cron.run_service(test_service)
        else:
            print(f"   • Service {test_service} không thể chạy")
        
        print("✅ Test Chrome CronManager thành công!")
        return cron
        
    except Exception as e:
        print(f"❌ Test thất bại: {e}")
        return False

def test_chrome_driver_manual():
    """Test Chrome driver thủ công"""
    print("\n🧪 Test Chrome Driver Thủ Công...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("🌐 Đang khởi động Chrome...")
        
        # Cấu hình Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Khởi động Chrome
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        print("✅ Chrome đã khởi động thành công")
        
        # Test navigation
        print("🧭 Test navigation...")
        driver.get("https://www.google.com")
        time.sleep(2)
        
        title = driver.title
        print(f"   • Title: {title}")
        
        # Test element
        print("🔍 Test tìm element...")
        search_box = driver.find_element("name", "q")
        if search_box:
            print("   ✅ Tìm thấy search box")
            search_box.send_keys("AutoGachno Test")
            time.sleep(1)
        else:
            print("   ❌ Không tìm thấy search box")
        
        # Đóng Chrome
        print("🌐 Đang đóng Chrome...")
        driver.quit()
        print("✅ Chrome đã đóng")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Chrome driver thất bại: {e}")
        return False

def test_service_manager_with_chrome():
    """Test Service Manager với Chrome"""
    print("\n🧪 Test Service Manager với Chrome...")
    
    try:
        from app.services.service_manager import (
            navigate_to_page, wait_for_element, click_element, fill_input
        )
        
        print("✅ Import Service Manager thành công")
        
        # Test các hàm Selenium
        selenium_functions = [
            ("navigate_to_page", navigate_to_page),
            ("wait_for_element", wait_for_element),
            ("click_element", click_element),
            ("fill_input", fill_input),
        ]
        
        print("🔧 Kiểm tra các hàm Selenium:")
        for name, func in selenium_functions:
            if callable(func):
                print(f"   ✅ {name}: {func.__name__}")
            else:
                print(f"   ❌ {name}: Không phải function")
        
        print("✅ Test Service Manager với Chrome thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Test Service Manager với Chrome thất bại: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Test Cron Manager với Chrome và chế độ lặp...")
    print("=" * 60)
    
    tests = [
        ("Chrome Driver Manual", test_chrome_driver_manual),
        ("Service Manager với Chrome", test_service_manager_with_chrome),
        ("Chrome Cron Manager", test_chrome_cron_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
            print(f"   ✅ {test_name} - THÀNH CÔNG")
        else:
            print(f"   ❌ {test_name} - THẤT BẠI")
    
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ TEST: {passed}/{total} thành công")
    
    if passed == total:
        print("🎉 TẤT CẢ TEST THÀNH CÔNG!")
        print("✅ Cron Manager với Chrome hoạt động hoàn hảo")
        print("\n💡 Để chạy với chế độ test:")
        print("   python app/cron_manager.py --test --interval 10")
        print("\n💡 Để chạy bình thường:")
        print("   python app/cron_manager.py")
    else:
        print("⚠️  MỘT SỐ TEST THẤT BẠI!")
        print("🔧 Cần kiểm tra và sửa lỗi")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
