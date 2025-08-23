"""Configuration facade.

This module re-exports configuration from the legacy implementation in
`app.main` to keep compatibility while we progressively refactor.
"""

import os
from dataclasses import dataclass
import json

@dataclass
class Config:
    """Cấu hình ứng dụng"""
    DRIVER_LINK: str = "https://kpp.bankplus.vn"
    FOLDER_RESULT: str = "ket_qua"
    TITLE: str = "Thông báo"
    CONFIG_FILE: str = "config.json"
    ICON_FILE: str = "viettelpay.ico"
    COPYRIGHT_KEY: bytes = b"h_ThisAAutoToolVjppro-CopyRight-ByCAOAC7690="
    STATUS_COMPLETE: str = "Đã xử lý"
    STATUS_INCOMPLETE: str = "Chưa xử lý"
    
    # Service types
    SERVICES = {
        'payment_internet': 'payment_internet',
        'payment_card': 'deb_cart', 
        'lookup_card': 'lookup_cart',
        'lookup_ftth': 'lookup_ftth',
        'payment_evn': 'deb_evn'
    }
    
    # API Configuration
    API_BASE_URL: str = os.getenv('API_BASE_URL', "http://127.0.0.1:8080")
    NODE_SERVER_URL: str = os.getenv('NODE_SERVER_URL', "http://127.0.0.1:5000")
    API_TIMEOUT: int = 10
    
    # PIN Configuration
    DEFAULT_PIN: str = os.getenv('APP_DEFAULT_PIN', '686886')
    
    @classmethod
    def load_from_config(cls):
        """Load cấu hình từ file config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if 'default_pin' in config_data:
                        cls.DEFAULT_PIN = config_data['default_pin']
                        print(f"[CONFIG] Đã load PIN từ config: {cls.DEFAULT_PIN}")
            else:
                print(f"[CONFIG] Không tìm thấy file config.json tại {config_path}")
        except Exception as e:
            print(f"[CONFIG] Lỗi load config: {e}")

# Other globals
LOGIN_USERNAME = os.getenv('APP_LOGIN_USERNAME', '1000460100_VTP_00073_DB')
LOGIN_PASSWORD = os.getenv('APP_LOGIN_PASSWORD', '686886')

DB_DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres:123456@localhost:5432/autogachno')
DB_MAIN_USER_ID = os.getenv('MAIN_USER_ID', 'admin-local')
DB_MAIN_USER_EMAIL = os.getenv('MAIN_USER_EMAIL', 'Demodiemthu')

AUTOMATION_MAX_RETRIES = 1
DIRECT_DB_MODE = True

# Load on module import
Config.load_from_config()

__all__ = [
    "Config",
    "LOGIN_USERNAME",
    "LOGIN_PASSWORD",
    "DB_DATABASE_URL",
    "DB_MAIN_USER_ID",
    "DB_MAIN_USER_EMAIL",
    "AUTOMATION_MAX_RETRIES",
    "DIRECT_DB_MODE",
]


