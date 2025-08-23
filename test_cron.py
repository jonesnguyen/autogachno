#!/usr/bin/env python3
"""
Test script cho Cron Manager
Chạy: python test_cron.py
"""

import os
import sys
import time
import json
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def test_config_loading():
    """Test việc tải cấu hình"""
    print("🧪 Test 1: Tải cấu hình")
    try:
        with open('cron_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        services = config.get('services', {})
        print(f"✅ Đã tải {len(services)} dịch vụ")
        
        for name, service in services.items():
            enabled = service.get('enabled', False)
            interval = service.get('interval_minutes', 0)
            priority = service.get('priority', 0)
            print(f"   • {name}: {'🟢' if enabled else '🔴'} - {interval} phút - ưu tiên {priority}")
        
        return True
    except Exception as e:
        print(f"❌ Lỗi tải cấu hình: {e}")
        return False

def test_cron_manager_import():
    """Test việc import CronManager"""
    print("\n🧪 Test 2: Import CronManager")
    try:
        from app.cron_manager import CronManager
        print("✅ Import CronManager thành công")
        
        # Test khởi tạo
        cron = CronManager()
        print("✅ Khởi tạo CronManager thành công")
        
        # Test lấy trạng thái
        status = cron.get_status()
        print(f"✅ Trạng thái: {status['active_count']}/{status['max_concurrent']} dịch vụ")
        
        return True
    except Exception as e:
        print(f"❌ Lỗi import CronManager: {e}")
        return False

def test_service_control():
    """Test việc điều khiển dịch vụ"""
    print("\n🧪 Test 3: Điều khiển dịch vụ")
    try:
        from app.cron_manager import CronManager
        cron = CronManager()
        
        # Test bật/tắt dịch vụ
        cron.enable_service('evn', False)
        print("✅ Tắt dịch vụ EVN thành công")
        
        cron.enable_service('evn', True)
        print("✅ Bật dịch vụ EVN thành công")
        
        # Test cập nhật interval
        cron.update_interval('ftth', 25)
        print("✅ Cập nhật interval FTTH thành công")
        
        return True
    except Exception as e:
        print(f"❌ Lỗi điều khiển dịch vụ: {e}")
        return False

def test_schedule_setup():
    """Test việc thiết lập lịch trình"""
    print("\n🧪 Test 4: Thiết lập lịch trình")
    try:
        from app.cron_manager import CronManager
        cron = CronManager()
        
        # Test setup schedule
        cron.setup_schedule()
        print("✅ Thiết lập lịch trình thành công")
        
        # Test can_run_service
        can_run = cron.can_run_service('ftth')
        print(f"✅ Kiểm tra có thể chạy FTTH: {can_run}")
        
        return True
    except Exception as e:
        print(f"❌ Lỗi thiết lập lịch trình: {e}")
        return False

def test_dependencies():
    """Test các dependency"""
    print("\n🧪 Test 5: Kiểm tra dependencies")
    
    dependencies = [
        ('schedule', 'schedule'),
        ('json', 'json'),
        ('threading', 'threading'),
        ('datetime', 'datetime')
    ]
    
    all_ok = True
    for module_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {module_name}")
        except ImportError:
            print(f"❌ {module_name}")
            all_ok = False
    
    return all_ok

def main():
    """Hàm chính test"""
    print("🚀 Bắt đầu test Cron Manager...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_cron_manager_import,
        test_service_control,
        test_schedule_setup,
        test_dependencies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test bị lỗi: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Kết quả test: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 Tất cả test đều thành công!")
        print("✅ Cron Manager đã sẵn sàng sử dụng")
        print("\n💡 Để chạy cron manager:")
        print("   python cron_runner.py")
    else:
        print("⚠️ Một số test thất bại, cần kiểm tra lại")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
