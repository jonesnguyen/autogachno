#!/usr/bin/env python3
"""
Cron Runner - Khởi chạy Cron Manager
Chạy: python cron_runner.py
"""

import os
import sys
import signal
import time
import logging
from datetime import datetime

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

def setup_logging():
    """Thiết lập logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('cron.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Xử lý signal để dừng chương trình"""
    logger.info(f"📡 Nhận signal {signum}, đang dừng...")
    sys.exit(0)

def check_dependencies():
    """Kiểm tra các dependency cần thiết"""
    try:
        import schedule
        logger.info("✅ Thư viện schedule đã sẵn sàng")
    except ImportError:
        logger.error("❌ Thiếu thư viện schedule. Cài đặt: pip install schedule")
        return False
    
    try:
        from app.cron_manager import CronManager
        logger.info("✅ CronManager đã sẵn sàng")
    except ImportError as e:
        logger.error(f"❌ Không thể import CronManager: {e}")
        return False
    
    return True

def main():
    """Hàm chính"""
    global logger
    logger = setup_logging()
    
    logger.info("🚀 Khởi động Cron Runner...")
    logger.info(f"📅 Thời gian hiện tại: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Kiểm tra dependencies
    if not check_dependencies():
        logger.error("❌ Thiếu dependencies, không thể tiếp tục")
        return 1
    
    # Thiết lập signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Import và khởi tạo CronManager
        from app.cron_manager import CronManager
        
        logger.info("🔧 Khởi tạo CronManager...")
        cron_manager = CronManager()
        
        # Hiển thị trạng thái ban đầu
        status = cron_manager.get_status()
        logger.info(f"📊 Trạng thái ban đầu: {status['active_count']}/{status['max_concurrent']} dịch vụ")
        
        # Hiển thị cấu hình
        config = cron_manager.config
        logger.info("⚙️ Cấu hình dịch vụ:")
        for service_name, service_config in config.get('services', {}).items():
            if service_config.get('enabled', False):
                interval = service_config.get('interval_minutes', 60)
                priority = service_config.get('priority', 0)
                description = service_config.get('description', '')
                logger.info(f"   • {service_name}: mỗi {interval} phút (ưu tiên {priority}) - {description}")
        
        logger.info("🎯 Bắt đầu chạy cron manager...")
        logger.info("💡 Nhấn Ctrl+C để dừng")
        
        # Bắt đầu cron manager
        cron_manager.start()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Dừng theo yêu cầu người dùng")
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn: {e}")
        return 1
    
    logger.info("👋 Cron Runner đã kết thúc")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
