#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File test đơn giản để test từng dịch vụ riêng lẻ
"""

import os
import sys

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import_functions():
    """Test import các hàm từ main.py"""
    print("🧪 [TEST] Import các hàm từ main.py")
    print("=" * 50)
    
    try:
        from main import (
            update_database_immediately,
            send_callback_with_retry,
            Config
        )
        print("✅ Import thành công các hàm cần thiết")
        print(f"   📋 Config.TITLE: {Config.TITLE}")
        print(f"   🌐 Config.NODE_SERVER_URL: {Config.NODE_SERVER_URL}")
        return True
    except ImportError as e:
        print(f"❌ Import thất bại: {e}")
        return False

def test_single_service(service_name: str, order_id: str, codes: list):
    """Test một dịch vụ cụ thể"""
    print(f"\n🔍 [TEST] {service_name}")
    print("=" * 50)
    
    try:
        from main import update_database_immediately
        
        print(f"📋 Order ID: {order_id}")
        print(f"📱 Số mã: {len(codes)}")
        
        results = []
        for idx, code in enumerate(codes, 1):
            print(f"\n📱 [MÃ {idx}/{len(codes)}] {code}")
            
            try:
                # Test update database
                success = update_database_immediately(
                    order_id, code, "success", 100000, f"{service_name} test ok", None
                )
                
                if success:
                    print(f"   ✅ Database updated thành công")
                    results.append({"code": code, "status": "success"})
                else:
                    print(f"   ❌ Database update thất bại")
                    results.append({"code": code, "status": "failed"})
                    
            except Exception as e:
                print(f"   💥 Lỗi: {e}")
                results.append({"code": code, "status": "error", "error": str(e)})
        
        # Tổng kết
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        error_count = len([r for r in results if r['status'] == 'error'])
        
        print(f"\n📊 Kết quả {service_name}:")
        print(f"   ✅ Thành công: {success_count}")
        print(f"   ❌ Thất bại: {failed_count}")
        print(f"   💥 Lỗi: {error_count}")
        
        return results
        
    except Exception as e:
        print(f"❌ Lỗi test {service_name}: {e}")
        return []

def main():
    """Hàm chính để chạy test"""
    print("🧪 [SIMPLE TEST] Test các dịch vụ cơ bản")
    print("=" * 80)
    
    # Test import
    if not test_import_functions():
        print("❌ Không thể import, dừng test")
        return
    
    # Test từng dịch vụ
    services = [
        {
            "name": "Tra cứu FTTH",
            "order_id": "test_ftth_001",
            "codes": ["t074_gftth_test1", "t074_gftth_test2"]
        },
        {
            "name": "Gạch điện EVN",
            "order_id": "test_evn_001", 
            "codes": ["EVN001", "EVN002"]
        },
        {
            "name": "Nạp tiền đa mạng",
            "order_id": "test_topup_multi_001",
            "codes": ["0123456789", "0987654321"]
        },
        {
            "name": "Nạp tiền Viettel",
            "order_id": "test_topup_viettel_001",
            "codes": ["0321234567", "0334567890"]
        },
        {
            "name": "TV-Internet",
            "order_id": "test_tv_internet_001",
            "codes": ["TV001", "TV002"]
        },
        {
            "name": "Tra cứu trả sau",
            "order_id": "test_postpaid_001",
            "codes": ["POST001", "POST002"]
        }
    ]
    
    all_results = {}
    
    for service in services:
        results = test_single_service(
            service["name"],
            service["order_id"], 
            service["codes"]
        )
        all_results[service["name"]] = results
    
    # Tổng kết cuối cùng
    print("\n" + "="*80)
    print("🎯 [TỔNG KẾT] Kết quả test tất cả dịch vụ")
    print("=" * 80)
    
    total_success = 0
    total_failed = 0
    total_error = 0
    
    for service_name, results in all_results.items():
        if isinstance(results, list):
            success_count = len([r for r in results if r.get('status') == 'success'])
            failed_count = len([r for r in results if r.get('status') == 'failed'])
            error_count = len([r for r in results if r.get('status') == 'error'])
            
            total_success += success_count
            total_failed += failed_count
            total_error += error_count
            
            print(f"📊 {service_name}: ✅ {success_count} | ❌ {failed_count} | 💥 {error_count}")
    
    print(f"\n🏆 TỔNG CỘNG: ✅ {total_success} | ❌ {total_failed} | 💥 {total_error}")
    
    if total_failed == 0 and total_error == 0:
        print("🎉 Tất cả test đều thành công!")
    else:
        print(f"⚠️  Có {total_failed + total_error} test thất bại, cần kiểm tra lại")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Test bị dừng bởi người dùng")
    except Exception as e:
        print(f"\n💥 Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
