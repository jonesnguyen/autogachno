#!/usr/bin/env python3
"""
Demo Cron Manager với Chrome và chế độ test
Chạy: python demo_chrome_test.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def demo_chrome_test_mode():
    """Demo chế độ test với Chrome"""
    print("🚀 Demo Cron Manager với Chrome và chế độ test...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from app.cron_manager import CronManager
        
        # Khởi tạo với chế độ test
        print("🔧 Khởi tạo CronManager với chế độ test...")
        cron = CronManager(test_mode=True, test_interval=10)
        
        print("✅ Khởi tạo thành công")
        
        # Hiển thị thông tin
        print(f"\n📊 Thông tin CronManager:")
        print(f"   • Số service: {len(cron.service_functions)}")
        print(f"   • Max concurrent: {cron.max_concurrent}")
        print(f"   • Test mode: {cron.test_mode}")
        print(f"   • Test interval: {cron.test_interval} giây")
        print(f"   • Chrome ready: {cron.chrome_driver is not None}")
        
        # Hiển thị services
        print(f"\n📋 Services có sẵn:")
        for service_name, info in cron.service_functions.items():
            print(f"   • {service_name}: {info['description']}")
        
        # Test status
        print(f"\n📋 Status hiện tại:")
        status = cron.get_status()
        for key, value in status.items():
            print(f"   • {key}: {value}")
        
        print("\n✅ Demo Chrome test mode thành công!")
        return cron
        
    except Exception as e:
        print(f"❌ Demo thất bại: {e}")
        return False

def demo_single_service_test():
    """Demo test 1 service"""
    print("\n🧪 Demo Test 1 Service...")
    
    try:
        cron = demo_chrome_test_mode()
        if not cron:
            return False
        
        # Test với service đầu tiên
        test_service = 'ftth'
        print(f"\n🔍 Test service: {test_service}")
        
        # Kiểm tra có thể chạy không
        can_run = cron.can_run_service(test_service)
        print(f"   • Có thể chạy: {can_run}")
        
        if can_run:
            # Test chạy service
            print(f"   🚀 Bắt đầu test {test_service}...")
            cron.run_service(test_service)
            print(f"   ✅ Hoàn thành test {test_service}")
        else:
            print(f"   ⏸️ Service {test_service} không thể chạy ngay")
        
        print("✅ Demo single service test thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Demo single service test thất bại: {e}")
        return False

def demo_chrome_navigation():
    """Demo Chrome navigation"""
    print("\n🧭 Demo Chrome Navigation...")
    
    try:
        cron = demo_chrome_test_mode()
        if not cron:
            return False
        
        # Lấy Chrome driver
        driver = cron.get_chrome_driver()
        if not driver:
            print("   ❌ Chrome driver không sẵn sàng")
            return False
        
        print("   🌐 Test navigation...")
        
        # Test navigation
        driver.get("https://www.google.com")
        time.sleep(2)
        
        title = driver.title
        print(f"   • Title: {title}")
        
        # Test tìm element
        print("   🔍 Test tìm element...")
        try:
            search_box = driver.find_element("name", "q")
            if search_box:
                print("   ✅ Tìm thấy search box")
                search_box.send_keys("AutoGachno Test")
                time.sleep(1)
            else:
                print("   ❌ Không tìm thấy search box")
        except Exception as e:
            print(f"   ⚠️ Lỗi tìm element: {e}")
        
        print("✅ Demo Chrome navigation thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Demo Chrome navigation thất bại: {e}")
        return False

def demo_test_loop_preview():
    """Demo preview của test loop"""
    print("\n🔄 Demo Test Loop Preview...")
    
    try:
        cron = demo_chrome_test_mode()
        if not cron:
            return False
        
        print("   🧪 Preview test loop:")
        print("   • Vòng 1: Chạy tất cả service")
        print("   • Chờ 10 giây")
        print("   • Vòng 2: Chạy tất cả service")
        print("   • Chờ 10 giây")
        print("   • Vòng 3: Chạy tất cả service")
        print("   • ... (lặp vô hạn)")
        
        print("\n   📋 Thứ tự service:")
        for i, service_name in enumerate(['ftth', 'evn', 'topup_multi', 'topup_viettel', 'tv_internet', 'postpaid'], 1):
            service_info = cron.service_functions.get(service_name, {})
            description = service_info.get('description', 'Unknown')
            print(f"   {i}. {service_name}: {description}")
        
        print("\n   ⏰ Thời gian:")
        print(f"   • Test interval: {cron.test_interval} giây")
        print(f"   • Delay giữa service: 2 giây")
        print(f"   • Tổng thời gian mỗi vòng: ~12 giây")
        
        print("✅ Demo test loop preview thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Demo test loop preview thất bại: {e}")
        return False

def main():
    """Hàm chính"""
    print("🎯 Demo Cron Manager với Chrome và chế độ test...")
    print("=" * 60)
    
    demos = [
        ("Chrome Test Mode", demo_chrome_test_mode),
        ("Single Service Test", demo_single_service_test),
        ("Chrome Navigation", demo_chrome_navigation),
        ("Test Loop Preview", demo_test_loop_preview),
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        print(f"\n🔍 {demo_name}...")
        if demo_func():
            passed += 1
            print(f"   ✅ {demo_name} - THÀNH CÔNG")
        else:
            print(f"   ❌ {demo_name} - THẤT BẠI")
    
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ DEMO: {passed}/{total} thành công")
    
    if passed == total:
        print("🎉 TẤT CẢ DEMO THÀNH CÔNG!")
        print("✅ Cron Manager với Chrome hoạt động hoàn hảo")
        print("\n💡 Để chạy với chế độ test thực tế:")
        print("   python app/cron_manager.py --test --interval 10")
        print("\n💡 Để chạy bình thường:")
        print("   python app/cron_manager.py")
        print("\n💡 Để test nhanh (5 giây):")
        print("   python app/cron_manager.py --test --interval 5")
    else:
        print("⚠️  MỘT SỐ DEMO THẤT BẠI!")
        print("🔧 Cần kiểm tra và sửa lỗi")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
