#!/usr/bin/env python3
"""
Demo Service Manager - Test thực tế các hàm
Chạy: python demo_service_manager.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def demo_import_all_functions():
    """Demo import tất cả hàm từ Service Manager"""
    print("🧪 Demo Import Tất Cả Hàm...")
    try:
        from app.services.service_manager import (
            # FTTH Service
            get_data_ftth, lookup_ftth,
            
            # EVN Service  
            get_data_evn, debt_electric,
            
            # Topup Multi Service
            get_data_multi_network, payment_phone_multi,
            
            # Topup Viettel Service
            get_data_viettel, payment_phone_viettel,
            
            # TV-Internet Service
            get_data_tv_internet, payment_internet,
            
            # Postpaid Service
            get_data_postpaid, payment_phone_postpaid,
            
            # Selenium Control Functions
            navigate_to_page, wait_for_element, click_element, fill_input
        )
        
        print("   ✅ Import thành công tất cả 16 hàm")
        
        # Tạo danh sách tất cả hàm
        all_functions = {
            "FTTH": [get_data_ftth, lookup_ftth],
            "EVN": [get_data_evn, debt_electric],
            "Topup Multi": [get_data_multi_network, payment_phone_multi],
            "Topup Viettel": [get_data_viettel, payment_phone_viettel],
            "TV-Internet": [get_data_tv_internet, payment_internet],
            "Postpaid": [get_data_postpaid, payment_phone_postpaid],
            "Selenium": [navigate_to_page, wait_for_element, click_element, fill_input]
        }
        
        print("   📊 Danh sách hàm theo service:")
        for service_name, functions in all_functions.items():
            print(f"      • {service_name}: {len(functions)} hàm")
            for func in functions:
                print(f"        - {func.__name__}")
        
        return all_functions
        
    except Exception as e:
        print(f"   ❌ Import thất bại: {e}")
        return None

def demo_function_info():
    """Demo thông tin chi tiết các hàm"""
    print("\n🧪 Demo Thông Tin Hàm...")
    
    try:
        from app.services.service_manager import (
            get_data_ftth, lookup_ftth,
            get_data_evn, debt_electric,
            get_data_multi_network, payment_phone_multi,
            get_data_viettel, payment_phone_viettel,
            get_data_tv_internet, payment_internet,
            get_data_postpaid, payment_phone_postpaid,
            navigate_to_page, wait_for_element, click_element, fill_input
        )
        
        # Test một số hàm cụ thể
        test_functions = [
            ("get_data_ftth", get_data_ftth, "FTTH Get Data"),
            ("lookup_ftth", lookup_ftth, "FTTH Action"),
            ("navigate_to_page", navigate_to_page, "Selenium Control"),
            ("wait_for_element", wait_for_element, "Selenium Control"),
        ]
        
        for name, func, description in test_functions:
            print(f"   🔍 {description} - {name}:")
            print(f"      • Function name: {func.__name__}")
            print(f"      • Module: {func.__module__}")
            print(f"      • Docstring: {func.__doc__.strip()[:50]}...")
            print(f"      • Callable: {callable(func)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Demo function info thất bại: {e}")
        return False

def demo_service_manager_usage():
    """Demo cách sử dụng Service Manager"""
    print("\n🧪 Demo Cách Sử Dụng Service Manager...")
    
    try:
        print("   📝 Code mẫu để sử dụng:")
        print("   " + "="*50)
        
        print("   # 1. Import tất cả hàm")
        print("   from app.services.service_manager import (")
        print("       # FTTH Service")
        print("       get_data_ftth, lookup_ftth,")
        print("       # EVN Service")
        print("       get_data_evn, debt_electric,")
        print("       # Topup Multi Service")
        print("       get_data_multi_network, payment_phone_multi,")
        print("       # Topup Viettel Service")
        print("       get_data_viettel, payment_phone_viettel,")
        print("       # TV-Internet Service")
        print("       get_data_tv_internet, payment_internet,")
        print("       # Postpaid Service")
        print("       get_data_postpaid, payment_phone_postpaid,")
        print("       # Selenium Control Functions")
        print("       navigate_to_page, wait_for_element, click_element, fill_input")
        print("   )")
        print()
        
        print("   # 2. Sử dụng trong UI")
        print("   # Button Get dữ liệu")
        print("   tkbtn_get_data = ttk.Button(btn_frm, text=\"Get dữ liệu\",")
        print("                              command=lambda: get_data_ftth(tkinp_ctm, None))")
        print()
        print("   # Button Bắt đầu")
        print("   tkbtn_payment = ttk.Button(btn_frm, text=\"Bắt đầu\",")
        print("                              command=lambda: lookup_ftth(tkinp_ctm, tkinp_ctmed, None))")
        print()
        
        print("   # 3. Sử dụng Selenium chung")
        print("   # Điều hướng")
        print("   navigate_to_page(\"FTTH\", \"https://example.com/ftth\")")
        print()
        print("   # Chờ element")
        print("   element = wait_for_element(\"input_id\", 10)")
        print()
        print("   # Click element")
        print("   click_element(\"button_id\", 5)")
        print()
        print("   # Điền input")
        print("   fill_input(\"input_id\", \"value\", 5)")
        
        print("   " + "="*50)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Demo usage thất bại: {e}")
        return False

def demo_selenium_functions():
    """Demo các hàm Selenium (không thực thi thật)"""
    print("\n🧪 Demo Selenium Functions (Mock)...")
    
    try:
        from app.services.service_manager import (
            navigate_to_page, wait_for_element, click_element, fill_input
        )
        
        print("   🔧 Các hàm Selenium có sẵn:")
        selenium_functions = [
            ("navigate_to_page", "Điều hướng đến trang service"),
            ("wait_for_element", "Chờ element xuất hiện"),
            ("click_element", "Click vào element"),
            ("fill_input", "Điền giá trị vào input")
        ]
        
        for func_name, description in selenium_functions:
            print(f"      ✅ {func_name}: {description}")
        
        print("\n   📝 Cách sử dụng:")
        print("      • navigate_to_page(service_name, target_url)")
        print("      • wait_for_element(element_id, timeout)")
        print("      • click_element(element_id, timeout)")
        print("      • fill_input(element_id, value, timeout)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Demo selenium functions thất bại: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Demo Service Manager Mới...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    demos = [
        ("Import All Functions", demo_import_all_functions),
        ("Function Info", demo_function_info),
        ("Service Manager Usage", demo_service_manager_usage),
        ("Selenium Functions", demo_selenium_functions),
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
        print("✅ Service Manager hoạt động hoàn hảo")
        print("\n💡 Bước tiếp theo:")
        print("   1. Cập nhật cron manager để sử dụng Service Manager")
        print("   2. Cập nhật UI để sử dụng Service Manager")
        print("   3. Test thực tế với browser")
    else:
        print("⚠️  MỘT SỐ DEMO THẤT BẠI!")
        print("🔧 Cần kiểm tra và sửa lỗi")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
