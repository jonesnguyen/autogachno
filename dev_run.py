#!/usr/bin/env python3
"""
Development runner với auto-reload
Chạy: python dev_run.py
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def run_with_reload():
    """Chạy ứng dụng với auto-reload khi có thay đổi file"""
    print("🚀 [DEV] Khởi động chế độ phát triển với auto-reload...")
    print("   📁 Theo dõi thay đổi trong thư mục: app/")
    print("   🔄 Tự động restart khi có thay đổi")
    print("   ⏹️  Nhấn Ctrl+C để dừng")
    print()
    
    # Đường dẫn đến main.py
    main_file = Path("app/main.py")
    
    if not main_file.exists():
        print(f"❌ Không tìm thấy {main_file}")
        return
    
    process = None
    last_modified = 0
    
    try:
        while True:
            # Kiểm tra thay đổi file
            current_modified = main_file.stat().st_mtime
            
            if current_modified > last_modified:
                # Có thay đổi, dừng process cũ nếu có
                if process:
                    print(f"\n🔄 [DEV] Phát hiện thay đổi, restarting...")
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    print("   ✅ Process cũ đã dừng")
                
                # Khởi động process mới
                print(f"   🚀 Khởi động process mới...")
                process = subprocess.Popen([
                    sys.executable, str(main_file)
                ], cwd=os.getcwd())
                
                last_modified = current_modified
                print(f"   ✅ Process mới đã khởi động (PID: {process.pid})")
                print(f"   📝 Sẵn sàng nhận thay đổi...")
            
            # Chờ 1 giây trước khi kiểm tra lại
            time.sleep(1)
            
            # Kiểm tra process có còn chạy không
            if process and process.poll() is not None:
                print(f"   ⚠️  Process đã dừng (exit code: {process.returncode})")
                process = None
            
    except KeyboardInterrupt:
        print(f"\n⏹️  [DEV] Nhận tín hiệu dừng...")
        if process:
            print(f"   🛑 Dừng process (PID: {process.pid})...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("   ✅ Process đã dừng an toàn")
            except subprocess.TimeoutExpired:
                process.kill()
                print("   ⚠️  Process bị force kill")
        print("   👋 Tạm biệt!")

if __name__ == "__main__":
    run_with_reload()
