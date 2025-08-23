#!/usr/bin/env python3
"""
Test Service Manager - Kiểm tra tất cả 12 hàm chính và 4 hàm Selenium chung
Chạy: python test_service_manager.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def test_import_service_manager():
    """Test import Service Manager"""
    print("🧪 Test Import Service Manager...")
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
        functions_list = [
            get_data_ftth, lookup_ftth,
            get_data_evn, debt_electric,
            get_data_multi_network, payment_phone_multi,
            get_data_viettel, payment_phone_viettel,
            get_data_tv_internet, payment_internet,
            get_data_postpaid, payment_phone_postpaid,
            navigate_to_page, wait_for_element, click_element, fill_input
        ]
        print(f"   📊 Tổng số hàm: {len(functions_list)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import thất bại: {e}")
        return False

def test_function_signatures():
    """Test function signatures"""
    print("\n🧪 Test Function Signatures...")
    
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
        
        # Test Get Data functions
        get_data_functions = [
            ("get_data_ftth", get_data_ftth),
            ("get_data_evn", get_data_evn),
            ("get_data_multi_network", get_data_multi_network),
            ("get_data_viettel", get_data_viettel),
            ("get_data_tv_internet", get_data_tv_internet),
            ("get_data_postpaid", get_data_postpaid),
        ]
        
        print("   📥 Get Data Functions:")
        for name, func in get_data_functions:
            try:
                # Kiểm tra function có thể gọi được
                if callable(func):
                    print(f"      ✅ {name}: {func.__name__}")
                else:
                    print(f"      ❌ {name}: Không phải function")
            except Exception as e:
                print(f"      ❌ {name}: Lỗi - {e}")
        
        # Test Action functions
        action_functions = [
            ("lookup_ftth", lookup_ftth),
            ("debt_electric", debt_electric),
            ("payment_phone_multi", payment_phone_multi),
            ("payment_phone_viettel", payment_phone_viettel),
            ("payment_internet", payment_internet),
            ("payment_phone_postpaid", payment_phone_postpaid),
        ]
        
        print("   🚀 Action Functions:")
        for name, func in action_functions:
            try:
                if callable(func):
                    print(f"      ✅ {name}: {func.__name__}")
                else:
                    print(f"      ❌ {name}: Không phải function")
            except Exception as e:
                print(f"      ❌ {name}: Lỗi - {e}")
        
        # Test Selenium functions
        selenium_functions = [
            ("navigate_to_page", navigate_to_page),
            ("wait_for_element", wait_for_element),
            ("click_element", click_element),
            ("fill_input", fill_input),
        ]
        
        print("   🔧 Selenium Control Functions:")
        for name, func in selenium_functions:
            try:
                if callable(func):
                    print(f"      ✅ {name}: {func.__name__}")
                else:
                    print(f"      ❌ {name}: Không phải function")
            except Exception as e:
                print(f"      ❌ {name}: Lỗi - {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test function signatures thất bại: {e}")
        return False

def test_function_docs():
    """Test function documentation"""
    print("\n🧪 Test Function Documentation...")
    
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
        
        functions = [
            ("get_data_ftth", get_data_ftth),
            ("lookup_ftth", lookup_ftth),
            ("get_data_evn", get_data_evn),
            ("debt_electric", debt_electric),
            ("get_data_multi_network", get_data_multi_network),
            ("payment_phone_multi", payment_phone_multi),
            ("get_data_viettel", get_data_viettel),
            ("payment_phone_viettel", payment_phone_viettel),
            ("get_data_tv_internet", get_data_tv_internet),
            ("payment_internet", payment_internet),
            ("get_data_postpaid", get_data_postpaid),
            ("payment_phone_postpaid", payment_phone_postpaid),
            ("navigate_to_page", navigate_to_page),
            ("wait_for_element", wait_for_element),
            ("click_element", click_element),
            ("fill_input", fill_input),
        ]
        
        documented_count = 0
        for name, func in functions:
            if func.__doc__ and func.__doc__.strip():
                documented_count += 1
                print(f"      ✅ {name}: Có docstring")
            else:
                print(f"      ⚠️  {name}: Thiếu docstring")
        
        print(f"   📊 Tổng số hàm có docstring: {documented_count}/{len(functions)}")
        
        if documented_count == len(functions):
            print("   🎉 Tất cả hàm đều có docstring!")
            return True
        else:
            print("   ⚠️  Một số hàm thiếu docstring")
            return False
        
    except Exception as e:
        print(f"   ❌ Test function documentation thất bại: {e}")
        return False

def test_service_manager_structure():
    """Test cấu trúc Service Manager"""
    print("\n🧪 Test Cấu Trúc Service Manager...")
    
    try:
        from app.services.service_manager import __all__
        
        expected_functions = [
            # FTTH Service
            "get_data_ftth", "lookup_ftth",
            
            # EVN Service  
            "get_data_evn", "debt_electric",
            
            # Topup Multi Service
            "get_data_multi_network", "payment_phone_multi",
            
            # Topup Viettel Service
            "get_data_viettel", "payment_phone_viettel",
            
            # TV-Internet Service
            "get_data_tv_internet", "payment_internet",
            
            # Postpaid Service
            "get_data_postpaid", "payment_phone_postpaid",
            
            # Selenium Control Functions
            "navigate_to_page", "wait_for_element", "click_element", "fill_input"
        ]
        
        print("   📋 Kiểm tra __all__:")
        for func_name in expected_functions:
            if func_name in __all__:
                print(f"      ✅ {func_name}: Có trong __all__")
            else:
                print(f"      ❌ {func_name}: Thiếu trong __all__")
        
        missing_functions = set(expected_functions) - set(__all__)
        extra_functions = set(__all__) - set(expected_functions)
        
        if not missing_functions and not extra_functions:
            print("   🎉 __all__ hoàn hảo - đúng 16 hàm!")
            return True
        else:
            if missing_functions:
                print(f"   ⚠️  Thiếu functions: {missing_functions}")
            if extra_functions:
                print(f"   ⚠️  Thừa functions: {extra_functions}")
            return False
        
    except Exception as e:
        print(f"   ❌ Test cấu trúc thất bại: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Test Service Manager Mới...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Import Service Manager", test_import_service_manager),
        ("Function Signatures", test_function_signatures),
        ("Function Documentation", test_function_docs),
        ("Service Manager Structure", test_service_manager_structure),
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
        print("✅ Service Manager đã sẵn sàng sử dụng")
        print("\n💡 Để sử dụng:")
        print("   1. Import từ app.services.service_manager")
        print("   2. Sử dụng 12 hàm chính cho các service")
        print("   3. Sử dụng 4 hàm Selenium chung")
    else:
        print("⚠️  MỘT SỐ TEST THẤT BẠI!")
        print("🔧 Cần kiểm tra và sửa lỗi")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
