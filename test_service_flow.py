#!/usr/bin/env python3
"""
Test quy trình chạy service với get_data trước
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def test_ftth_flow():
    """Test quy trình FTTH"""
    print("🧪 Test FTTH Service Flow")
    try:
        from app.services import ftth
        from tkinter import Text
        
        # Tạo mock UI elements
        mock_ctm = Text()
        
        # 1. Gọi get_data trước
        print("   📥 Gọi get_data_ftth...")
        ftth.get_data_ftth(mock_ctm, None)
        
        # 2. Kiểm tra dữ liệu
        data = mock_ctm.get("1.0", "end-1c").strip()
        if not data:
            print("   📭 Không có dữ liệu FTTH để xử lý")
            return False
        
        print(f"   📊 Đã lấy {len(data.splitlines())} mã FTTH để xử lý")
        print(f"   📝 Dữ liệu: {data[:100]}...")
        
        # 3. Nếu có dữ liệu thì chạy service chính
        print("   🚀 Chạy lookup_ftth...")
        mock_ctmed = Text()
        ftth.lookup_ftth(mock_ctm, mock_ctmed, None)
        
        print("   ✅ FTTH service flow thành công!")
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi FTTH service flow: {e}")
        return False

def test_evn_flow():
    """Test quy trình EVN"""
    print("\n🧪 Test EVN Service Flow")
    try:
        from app.services import evn
        from tkinter import Text, Entry
        
        # Tạo mock UI elements
        mock_ctm = Text()
        mock_phone = Entry()
        mock_pin = Entry()
        
        # 1. Gọi get_data trước
        print("   📥 Gọi get_data_evn...")
        evn.get_data_evn(mock_ctm, mock_phone, mock_pin)
        
        # 2. Kiểm tra dữ liệu
        data = mock_ctm.get("1.0", "end-1c").strip()
        if not data:
            print("   📭 Không có dữ liệu EVN để xử lý")
            return False
        
        print(f"   📊 Đã lấy {len(data.splitlines())} mã EVN để xử lý")
        print(f"   📝 Dữ liệu: {data[:100]}...")
        
        # 3. Nếu có dữ liệu thì chạy service chính
        print("   🚀 Chạy debt_electric...")
        mock_ctmed = Text()
        evn.debt_electric(mock_ctm, mock_ctmed, mock_phone, mock_pin)
        
        print("   ✅ EVN service flow thành công!")
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi EVN service flow: {e}")
        return False

def test_topup_multi_flow():
    """Test quy trình Topup Multi"""
    print("\n🧪 Test Topup Multi Service Flow")
    try:
        from app.services import topup_multi
        from tkinter import Text, Entry, ttk
        
        # Tạo mock UI elements
        mock_ctm = Text()
        mock_pin = Entry()
        mock_form = ttk.Combobox()
        mock_amount = ttk.Combobox()
        
        # 1. Gọi get_data trước
        print("   📥 Gọi get_data_multi_network...")
        topup_multi.get_data_multi_network(mock_ctm, mock_pin, mock_form, mock_amount, "prepaid")
        
        # 2. Kiểm tra dữ liệu
        data = mock_ctm.get("1.0", "end-1c").strip()
        if not data:
            print("   📭 Không có dữ liệu topup_multi để xử lý")
            return False
        
        print(f"   📊 Đã lấy {len(data.splitlines())} mã topup_multi để xử lý")
        print(f"   📝 Dữ liệu: {data[:100]}...")
        
        # 3. Nếu có dữ liệu thì chạy service chính
        print("   🚀 Chạy payment_phone...")
        mock_ctmed = Text()
        topup_multi.payment_phone(mock_ctm, mock_ctmed, mock_pin, mock_form, mock_amount)
        
        print("   ✅ Topup Multi service flow thành công!")
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi Topup Multi service flow: {e}")
        return False

def main():
    """Hàm chính test"""
    print("🚀 Bắt đầu test Service Flow...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        test_ftth_flow,
        test_evn_flow,
        test_topup_multi_flow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test bị lỗi: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Kết quả test: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 Tất cả service flow đều thành công!")
        print("✅ Cron Manager đã sẵn sàng chạy với quy trình đúng!")
    else:
        print("⚠️ Một số service flow thất bại, cần kiểm tra lại")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
