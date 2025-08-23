#!/usr/bin/env python3
"""
Cron Manager - Quản lý lịch chạy các service
Sử dụng Service Manager mới để gọi tất cả hàm
Khởi động Chrome sẵn và chế độ lặp test
"""

import os
import sys
import time
import json
import logging
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Thêm thư mục gốc vào sys.path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from app.config import Config

# Import tất cả hàm từ Service Manager
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

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CronManager:
    """Quản lý cron jobs cho các service"""
    
    def __init__(self, test_mode: bool = False, test_interval: int = 10):
        self.config = self.load_config()
        self.running_services = set()
        self.global_lock = False
        self.max_concurrent = self.config.get('global_settings', {}).get('max_concurrent_services', 2)
        
        # Chế độ test
        self.test_mode = test_mode
        self.test_interval = test_interval
        
        # Khởi động Chrome sẵn
        self.chrome_driver = None
        self.init_chrome_driver()
        
        # Mapping service names với functions
        self.service_functions = {
            'ftth': {
                'get_data': get_data_ftth,
                'action': lookup_ftth,
                'description': 'Tra cứu FTTH'
            },
            'evn': {
                'get_data': get_data_evn,
                'action': debt_electric,
                'description': 'Gạch điện EVN'
            },
            'topup_multi': {
                'get_data': get_data_multi_network,
                'action': payment_phone_multi,
                'description': 'Nạp tiền đa mạng'
            },
            'topup_viettel': {
                'get_data': get_data_viettel,
                'action': payment_phone_viettel,
                'description': 'Nạp tiền Viettel'
            },
            'tv_internet': {
                'get_data': get_data_tv_internet,
                'action': payment_internet,
                'description': 'Thanh toán TV-Internet'
            },
            'postpaid': {
                'get_data': get_data_postpaid,
                'action': payment_phone_postpaid,
                'description': 'Tra cứu nợ trả sau'
            }
        }
        
        logger.info("🚀 CronManager đã khởi tạo với Service Manager mới")
        logger.info(f"📊 Tổng số service: {len(self.service_functions)}")
        logger.info(f"🔧 Max concurrent: {self.max_concurrent}")
        if self.test_mode:
            logger.info(f"🧪 Chế độ TEST: lặp sau {self.test_interval} giây")
        if self.chrome_driver:
            logger.info("🌐 Chrome driver đã sẵn sàng")
        else:
            logger.warning("⚠️ Chrome driver chưa sẵn sàng")
    
    def init_chrome_driver(self):
        """Khởi động Chrome driver sẵn"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Cấu hình Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            
            # Khởi động Chrome
            logger.info("🌐 Đang khởi động Chrome...")
            self.chrome_driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Test Chrome
            self.chrome_driver.get("https://www.google.com")
            time.sleep(2)
            logger.info("✅ Chrome đã khởi động thành công")
            
            # Đóng tab test
            self.chrome_driver.close()
            self.chrome_driver.switch_to.window(self.chrome_driver.window_handles[0])
            
        except Exception as e:
            logger.error(f"❌ Lỗi khởi động Chrome: {e}")
            self.chrome_driver = None
    
    def get_chrome_driver(self):
        """Lấy Chrome driver"""
        if self.chrome_driver is None:
            logger.warning("⚠️ Chrome driver chưa sẵn sàng, thử khởi động lại...")
            self.init_chrome_driver()
        return self.chrome_driver
    
    def load_config(self) -> Dict[str, Any]:
        """Load cấu hình từ file"""
        try:
            config_path = os.path.join(os.getcwd(), 'cron_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info("✅ Đã load cấu hình cron")
                    return config
            else:
                logger.warning("⚠️ Không tìm thấy cron_config.json, sử dụng cấu hình mặc định")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"❌ Lỗi load cấu hình: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Cấu hình mặc định"""
        return {
            "services": {
                "ftth": {"enabled": True, "interval_minutes": 25, "priority": 1},
                "evn": {"enabled": True, "interval_minutes": 60, "priority": 5},
                "topup_multi": {"enabled": True, "interval_minutes": 15, "priority": 2},
                "topup_viettel": {"enabled": True, "interval_minutes": 15, "priority": 3},
                "tv_internet": {"enabled": True, "interval_minutes": 45, "priority": 4},
                "postpaid": {"enabled": True, "interval_minutes": 60, "priority": 6}
            },
            "global_settings": {
                "max_concurrent_services": 2,
                "sequential_execution": True
            }
        }
    
    def save_config(self):
        """Lưu cấu hình"""
        try:
            config_path = os.path.join(os.getcwd(), 'cron_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("✅ Đã lưu cấu hình cron")
        except Exception as e:
            logger.error(f"❌ Lỗi lưu cấu hình: {e}")
    
    def can_run_service(self, service_name: str) -> bool:
        """Kiểm tra service có thể chạy không"""
        if self.global_lock:
            return False
        
        if len(self.running_services) >= self.max_concurrent:
            return False
        
        if service_name in self.running_services:
            return False
        
        return True
    
    def mark_service_running(self, service_name: str):
        """Đánh dấu service đang chạy"""
        self.running_services.add(service_name)
        logger.info(f"🟢 Service {service_name} đã bắt đầu chạy")
    
    def mark_service_finished(self, service_name: str):
        """Đánh dấu service đã hoàn thành"""
        self.running_services.discard(service_name)
        logger.info(f"🔴 Service {service_name} đã hoàn thành")
    
    def run_service(self, service_name: str):
        """Chạy service cụ thể"""
        if not self.can_run_service(service_name):
            logger.warning(f"⚠️ Service {service_name} không thể chạy ngay bây giờ")
            return
        
        try:
            self.mark_service_running(service_name)
            
            # Lấy thông tin service
            service_info = self.service_functions.get(service_name)
            if not service_info:
                logger.error(f"❌ Không tìm thấy thông tin service: {service_name}")
                return
            
            logger.info(f"🚀 Bắt đầu chạy {service_info['description']}")
            
            # Kiểm tra Chrome driver
            if not self.get_chrome_driver():
                logger.error(f"❌ Chrome driver không sẵn sàng, bỏ qua {service_name}")
                return
            
            # Gọi hàm get_data trước
            self._call_get_data(service_name, service_info['get_data'])
            
            # Gọi hàm action chính
            self._call_action(service_name, service_info['action'])
            
            logger.info(f"✅ Hoàn thành {service_info['description']}")
            
        except Exception as e:
            logger.error(f"❌ Lỗi chạy service {service_name}: {e}")
        finally:
            self.mark_service_finished(service_name)
    
    def _call_get_data(self, service_name: str, get_data_func):
        """Gọi hàm get_data của service"""
        try:
            logger.info(f"📥 Gọi get_data cho {service_name}")
            
            # Tạo mock UI elements cho get_data
            from tkinter import Text, Entry
            mock_text = Text()
            mock_entry = Entry()
            
            # Gọi get_data function với mock UI
            if service_name == 'ftth':
                get_data_func(mock_text, None)
            elif service_name == 'evn':
                get_data_func(mock_text, mock_entry, mock_entry)
            elif service_name in ['topup_multi', 'topup_viettel']:
                get_data_func(mock_text, mock_entry)
            elif service_name == 'tv_internet':
                get_data_func(mock_text, mock_entry)
            elif service_name == 'postpaid':
                get_data_func(mock_text)
            
            logger.info(f"✅ get_data cho {service_name} thành công")
            
        except Exception as e:
            logger.error(f"❌ Lỗi get_data cho {service_name}: {e}")
    
    def _call_action(self, service_name: str, action_func):
        """Gọi hàm action chính của service"""
        try:
            logger.info(f"🚀 Gọi action cho {service_name}")
            
            # Tạo mock UI elements cho action
            from tkinter import Text, Entry
            mock_text_input = Text()
            mock_text_output = Text()
            mock_entry = Entry()
            
            # Gọi action function với mock UI
            if service_name == 'ftth':
                action_func(mock_text_input, mock_text_output, None)
            elif service_name == 'evn':
                action_func(mock_text_input, mock_text_output, mock_entry, mock_entry)
            elif service_name in ['topup_multi', 'topup_viettel']:
                action_func(mock_text_input, mock_text_output, mock_entry, mock_entry, mock_entry)
            elif service_name == 'tv_internet':
                action_func(mock_text_input, mock_text_output, mock_entry)
            elif service_name == 'postpaid':
                action_func(mock_text_input, mock_text_output, mock_entry, mock_entry, mock_entry)
            
            logger.info(f"✅ action cho {service_name} thành công")
            
        except Exception as e:
            logger.error(f"❌ Lỗi action cho {service_name}: {e}")
    
    def setup_schedule(self):
        """Thiết lập lịch chạy"""
        try:
            # Xóa tất cả job cũ
            schedule.clear()
            
            # Thiết lập job cho từng service
            for service_name, service_config in self.config.get('services', {}).items():
                if service_config.get('enabled', False):
                    interval = service_config.get('interval_minutes', 60)
                    schedule.every(interval).minutes.do(self.run_service, service_name)
                    logger.info(f"⏰ Đã lên lịch {service_name}: mỗi {interval} phút")
            
            logger.info("✅ Đã thiết lập lịch chạy cho tất cả service")
            
        except Exception as e:
            logger.error(f"❌ Lỗi thiết lập lịch: {e}")
    
    def run_test_loop(self):
        """Chạy vòng lặp test"""
        if not self.test_mode:
            logger.warning("⚠️ Không phải chế độ test")
            return
        
        logger.info(f"🧪 Bắt đầu chế độ TEST - lặp sau {self.test_interval} giây")
        
        try:
            while True:
                logger.info("🔄 Bắt đầu vòng test mới...")
                
                # Chạy tất cả service theo thứ tự
                for service_name in ['ftth', 'evn', 'topup_multi', 'topup_viettel', 'tv_internet', 'postpaid']:
                    if self.can_run_service(service_name):
                        logger.info(f"🧪 Test service: {service_name}")
                        self.run_service(service_name)
                        time.sleep(2)  # Chờ giữa các service
                    else:
                        logger.info(f"⏸️ Service {service_name} không thể chạy ngay")
                
                logger.info(f"⏳ Chờ {self.test_interval} giây trước vòng tiếp theo...")
                time.sleep(self.test_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Dừng chế độ test...")
        except Exception as e:
            logger.error(f"❌ Lỗi trong chế độ test: {e}")
    
    def start(self):
        """Bắt đầu cron manager"""
        try:
            logger.info("🚀 Bắt đầu Cron Manager...")
            
            if self.test_mode:
                # Chế độ test
                self.run_test_loop()
            else:
                # Chế độ cron bình thường
                self.setup_schedule()
                
                while True:
                    schedule.run_pending()
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Dừng Cron Manager...")
        except Exception as e:
            logger.error(f"❌ Lỗi Cron Manager: {e}")
        finally:
            # Đóng Chrome driver
            if self.chrome_driver:
                try:
                    self.chrome_driver.quit()
                    logger.info("🌐 Đã đóng Chrome driver")
                except:
                    pass
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại"""
        return {
            'active_count': len(self.running_services),
            'max_concurrent': self.max_concurrent,
            'running_services': list(self.running_services),
            'test_mode': self.test_mode,
            'chrome_ready': self.chrome_driver is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def enable_service(self, service_name: str, enabled: bool):
        """Bật/tắt service"""
        if service_name in self.config.get('services', {}):
            self.config['services'][service_name]['enabled'] = enabled
            self.save_config()
            logger.info(f"✅ Service {service_name}: {'đã bật' if enabled else 'đã tắt'}")
        else:
            logger.warning(f"⚠️ Không tìm thấy service: {service_name}")
    
    def update_interval(self, service_name: str, interval_minutes: int):
        """Cập nhật interval cho service"""
        if service_name in self.config.get('services', {}):
            self.config['services'][service_name]['interval_minutes'] = interval_minutes
            self.save_config()
            logger.info(f"✅ Service {service_name}: interval = {interval_minutes} phút")
        else:
            logger.warning(f"⚠️ Không tìm thấy service: {service_name}")

def main():
    """Hàm chính"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cron Manager với Service Manager')
    parser.add_argument('--test', action='store_true', help='Chế độ test (lặp sau 10 giây)')
    parser.add_argument('--interval', type=int, default=10, help='Khoảng thời gian giữa các vòng test (giây)')
    
    args = parser.parse_args()
    
    try:
        cron = CronManager(test_mode=args.test, test_interval=args.interval)
        cron.start()
    except Exception as e:
        logger.error(f"❌ Lỗi chính: {e}")

if __name__ == "__main__":
    main()
