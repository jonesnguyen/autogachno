#!/usr/bin/env python3
"""
Demo Cron Manager với quy trình mới
Chạy: python demo_cron.py
"""

import os
import sys
import time
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def demo_cron_manager():
    """Demo cron manager"""
    print("🚀 Demo Cron Manager với quy trình mới...")
    print(f"📅 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        from app.cron_manager import CronManager
        
        print("🔧 Khởi tạo CronManager...")
        cron = CronManager()
        
        print("📊 Trạng thái ban đầu:")
        status = cron.get_status()
        print(f"   • Dịch vụ đang chạy: {status['active_count']}/{status['max_concurrent']}")
        print(f"   • Timestamp: {status['timestamp']}")
        
        print("\n⚙️ Cấu hình dịch vụ:")
        config = cron.config
        for service_name, service_config in config.get('services', {}).items():
            if service_config.get('enabled', False):
                interval = service_config.get('interval_minutes', 60)
                priority = service_config.get('priority', 0)
                description = service_config.get('description', '')
                print(f"   • {service_name}: mỗi {interval} phút (ưu tiên {priority})")
                print(f"     {description}")
        
        print("\n🧪 Test chạy dịch vụ FTTH...")
        print("   📝 Lưu ý: Cần có UI và browser driver sẵn sàng")
        
        # Test chạy FTTH service
        try:
            cron.run_service('ftth')
            print("   ✅ FTTH service test hoàn thành")
        except Exception as e:
            print(f"   ❌ FTTH service test thất bại: {e}")
        
        print("\n🎯 Cron Manager đã sẵn sàng!")
        print("💡 Để chạy đầy đủ:")
        print("   1. Chạy main.py để khởi tạo UI và browser")
        print("   2. Chạy cron_runner.py để bắt đầu cron manager")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi demo: {e}")
        return False

def main():
    """Hàm chính"""
    success = demo_cron_manager()
    
    if success:
        print("\n🎉 Demo thành công!")
    else:
        print("\n⚠️ Demo thất bại!")
    
    return success

if __name__ == "__main__":
    main()
