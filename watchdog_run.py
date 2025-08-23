#!/usr/bin/env python3
"""
Watchdog runner với auto-reload nâng cao
Cần cài: pip install watchdog
Chạy: python watchdog_run.py
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeChangeHandler(FileSystemEventHandler):
    """Xử lý sự kiện thay đổi file"""
    
    def __init__(self, main_file, callback):
        self.main_file = main_file
        self.callback = callback
        self.last_modified = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Chỉ xử lý file Python
        if not event.src_path.endswith('.py'):
            return
            
        # Tránh spam khi có nhiều thay đổi liên tiếp
        current_time = time.time()
        if current_time - self.last_modified < 1:
            return
            
        self.last_modified = current_time
        print(f"\n🔄 [WATCHDOG] Phát hiện thay đổi: {event.src_path}")
        self.callback()

def run_with_watchdog():
    """Chạy ứng dụng với watchdog auto-reload"""
    print("🚀 [WATCHDOG] Khởi động chế độ phát triển với auto-reload...")
    print("   📁 Theo dõi thay đổi trong thư mục: app/")
    print("   🔄 Tự động restart khi có thay đổi file .py")
    print("   ⏹️  Nhấn Ctrl+C để dừng")
    print()
    
    # Đường dẫn đến main.py
    main_file = Path("app/main.py")
    
    if not main_file.exists():
        print(f"❌ Không tìm thấy {main_file}")
        return
    
    process = None
    
    def restart_app():
        nonlocal process
        # Dừng process cũ nếu có
        if process:
            print("   🛑 Dừng process cũ...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("   ✅ Process cũ đã dừng")
            except subprocess.TimeoutExpired:
                process.kill()
                print("   ⚠️  Process cũ bị force kill")
        
        # Khởi động process mới
        print("   🚀 Khởi động process mới...")
        process = subprocess.Popen([
            sys.executable, str(main_file)
        ], cwd=os.getcwd())
        
        print(f"   ✅ Process mới đã khởi động (PID: {process.pid})")
        print("   📝 Sẵn sàng nhận thay đổi...")
    
    # Khởi động lần đầu
    restart_app()
    
    # Thiết lập watchdog observer
    event_handler = CodeChangeHandler(main_file, restart_app)
    observer = Observer()
    observer.schedule(event_handler, 'app', recursive=True)
    observer.start()
    
    try:
        print("   👀 Đang theo dõi thay đổi...")
        while True:
            time.sleep(1)
            
            # Kiểm tra process có còn chạy không
            if process and process.poll() is not None:
                print(f"   ⚠️  Process đã dừng (exit code: {process.returncode})")
                process = None
                # Tự động restart nếu process bị crash
                print("   🔄 Tự động restart do process crash...")
                restart_app()
                
    except KeyboardInterrupt:
        print(f"\n⏹️  [WATCHDOG] Nhận tín hiệu dừng...")
        observer.stop()
        
        if process:
            print(f"   🛑 Dừng process (PID: {process.pid})...")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("   ✅ Process đã dừng an toàn")
            except subprocess.TimeoutExpired:
                process.kill()
                print("   ⚠️  Process bị force kill")
        
        observer.join()
        print("   👋 Tạm biệt!")

if __name__ == "__main__":
    try:
        run_with_watchdog()
    except ImportError:
        print("❌ Cần cài đặt watchdog: pip install watchdog")
        print("   Hoặc sử dụng: python dev_run.py")
