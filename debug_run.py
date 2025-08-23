#!/usr/bin/env python3
"""
Debug runner với Python debugger
Chạy: python debug_run.py
"""

import os
import sys
import pdb

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def debug_main():
    """Chạy main với debugger"""
    print("🐛 [DEBUG] Khởi động chế độ debug...")
    print("   📍 Breakpoint tại main() function")
    print("   🔍 Sử dụng các lệnh debug:")
    print("      • n (next): Bước tiếp theo")
    print("      • s (step): Bước vào function")
    print("      • c (continue): Tiếp tục chạy")
    print("      • p <variable>: In giá trị biến")
    print("      • l (list): Hiển thị code xung quanh")
    print("      • q (quit): Thoát debugger")
    print()
    
    try:
        # Import và chạy main với debugger
        from app.main import main
        
        # Đặt breakpoint tại đây
        pdb.set_trace()
        
        print("🚀 Bắt đầu chạy main()...")
        main()
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        # Vào debugger khi có lỗi
        pdb.post_mortem()

if __name__ == "__main__":
    debug_main()
