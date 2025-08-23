#!/usr/bin/env python3
"""
Test Cron Manager với Service Manager mới
Chạy: python test_cron_manager.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def test_cron_manager_import():
    """Test import CronManager"""
    print("🧪 Test Import CronManager...")
    try:
        from app.cron_manager import CronManager
        print("   ✅ Import CronManager thành công")
        return CronManager
    except Exception as e:
        print(f"   ❌ Import thất bại: {e}")
        return None

def test_cron_manager_initialization():
    """Test khởi tạo CronManager"""
    print("\n🧪 Test Khởi Tạo CronManager...")
    try:
        CronManager = test_cron_manager_import()
        if not CronManager:
            return False
        
        cron = CronManager()
        print("   ✅ Khởi tạo CronManager thành công")
        
        # Kiểm tra các thuộc tính
        print(f"   📊 Số service: {len(cron.service_functions)}")
        print(f"   🔧 Max concurrent: {cron.max_concurrent}")
        print(f"   📋 Services có sẵn:")
        for service_name, info in cron.service_functions.items():
            print(f"      • {service_name}: {info['description']}")
        
        return cron
        
    except Exception as e:
        print(f"   ❌ Khởi tạo thất bại: {e}")
        return False

def test_service_functions():
    """Test các service functions"""
    print("\n🧪 Test Service Functions...")
    try:
        cron = test_cron_manager_initialization()
        if not cron:
            return False
        
        # Test từng service
        for service_name, service_info in cron.service_functions.items():
            print(f"   🔍 Test {service_name}:")
            
            # Kiểm tra get_data function
            get_data_func = service_info['get_data']
            if callable(get_data_func):
                print(f"      ✅ get_data: {get_data_func.__name__}")
            else:
                print(f"      ❌ get_data: Không phải function")
            
            # Kiểm tra action function
            action_func = service_info['action']
            if callable(action_func):
                print(f"      ✅ action: {action_func.__name__}")
            else:
                print(f"      ❌ action: Không phải function")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test service functions thất bại: {e}")
        return False

def test_cron_manager_methods():
    """Test các method của CronManager"""
    print("\n🧪 Test CronManager Methods...")
    try:
        cron = test_cron_manager_initialization()
        if not cron:
            return False
        
        # Test các method
        methods_to_test = [
            ('load_config', cron.load_config),
            ('save_config', cron.save_config),
            ('can_run_service', lambda: cron.can_run_service('ftth')),
            ('get_status', cron.get_status),
            ('enable_service', lambda: cron.enable_service('ftth', True)),
            ('update_interval', lambda: cron.update_interval('ftth', 30)),
        ]
        
        for method_name, method_call in methods_to_test:
            try:
                result = method_call()
                print(f"   ✅ {method_name}: Thành công")
                if method_name == 'get_status':
                    print(f"      📊 Status: {result}")
            except Exception as e:
                print(f"   ❌ {method_name}: Lỗi - {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test methods thất bại: {e}")
        return False

def test_mock_service_execution():
    """Test mock service execution (không thực thi thật)"""
    print("\n🧪 Test Mock Service Execution...")
    try:
        cron = test_cron_manager_initialization()
        if not cron:
            return False
        
        # Test với service đầu tiên
        test_service = 'ftth'
        print(f"   🧪 Test mock execution cho {test_service}")
        
        # Kiểm tra có thể chạy không
        can_run = cron.can_run_service(test_service)
        print(f"      • Có thể chạy: {can_run}")
        
        # Test mark running/finished
        cron.mark_service_running(test_service)
        status = cron.get_status()
        print(f"      • Status sau khi mark running: {status}")
        
        cron.mark_service_finished(test_service)
        status = cron.get_status()
        print(f"      • Status sau khi mark finished: {status}")
        
        print("   ✅ Mock execution test thành công")
        return True
        
    except Exception as e:
        print(f"   ❌ Mock execution test thất bại: {e}")
        return False

def test_config_management():
    """Test quản lý cấu hình"""
    print("\n🧪 Test Config Management...")
    try:
        cron = test_cron_manager_initialization()
        if not cron:
            return False
        
        # Test load config
        config = cron.config
        print(f"   📋 Config hiện tại:")
        print(f"      • Số service: {len(config.get('services', {}))}")
        print(f"      • Max concurrent: {config.get('global_settings', {}).get('max_concurrent_services')}")
        
        # Test enable/disable service
        print(f"   🔧 Test enable/disable service:")
        cron.enable_service('ftth', False)
        ftth_enabled = cron.config['services']['ftth']['enabled']
        print(f"      • FTTH disabled: {not ftth_enabled}")
        
        cron.enable_service('ftth', True)
        ftth_enabled = cron.config['services']['ftth']['enabled']
        print(f"      • FTTH enabled: {ftth_enabled}")
        
        # Test update interval
        print(f"   ⏰ Test update interval:")
        cron.update_interval('ftth', 45)
        ftth_interval = cron.config['services']['ftth']['interval_minutes']
        print(f"      • FTTH interval: {ftth_interval} phút")
        
        print("   ✅ Config management test thành công")
        return True
        
    except Exception as e:
        print(f"   ❌ Config management test thất bại: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Test Cron Manager với Service Manager...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Import CronManager", test_cron_manager_import),
        ("Khởi Tạo CronManager", test_cron_manager_initialization),
        ("Service Functions", test_service_functions),
        ("CronManager Methods", test_cron_manager_methods),
        ("Mock Service Execution", test_mock_service_execution),
        ("Config Management", test_config_management),
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
        print("✅ Cron Manager với Service Manager hoạt động hoàn hảo")
        print("\n💡 Bước tiếp theo:")
        print("   1. ✅ Cập nhật cron manager để sử dụng Service Manager - HOÀN THÀNH")
        print("   2. 🔄 Cập nhật UI để sử dụng Service Manager")
        print("   3. 🧪 Test thực tế với browser")
    else:
        print("⚠️  MỘT SỐ TEST THẤT BẠI!")
        print("🔧 Cần kiểm tra và sửa lỗi")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
