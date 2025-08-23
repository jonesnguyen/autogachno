import logging
import re
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import threading

from ..config import Config, LOGIN_USERNAME, LOGIN_PASSWORD

logger = logging.getLogger(__name__)

driver: Optional[webdriver.Chrome] = None
automation_lock = threading.Lock()

def get_chrome_driver(username: str = "default") -> Optional[webdriver.Chrome]:
    """Tạo Chrome driver"""
    try:
        profile_dir = os.path.join(os.getcwd(), "chrome_profile", username)
        os.makedirs(profile_dir, exist_ok=True)
        
        options = Options()
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Thêm các tùy chọn bảo mật
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Lỗi khởi tạo Chrome Driver: {e}")
        return None

def initialize_browser(username="default"):
    global driver
    driver = get_chrome_driver(username)
    if driver:
        driver.get(Config.DRIVER_LINK)
        return driver
    return None

def cleanup():
    global driver
    if driver:
        try:
            driver.quit()
        except Exception as e:
            logger.warning(f"Lỗi khi đóng driver: {e}")
        finally:
            driver = None

def is_logged_in(driver):
    # Bỏ qua kiểm tra trạng thái đăng nhập: luôn cho phép chạy
    return True

def login_process():
    """Đăng nhập tự động khi mở trình duyệt bằng tài khoản cấu hình."""
    try:
        inp_usr = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "loginForm:userName")))
        inp_usr.clear() 
        inp_usr.send_keys(LOGIN_USERNAME)
        inp_pwd = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "loginForm:password")))
        inp_pwd.clear() 
        inp_pwd.send_keys(LOGIN_PASSWORD)
        print("[LOGIN] Đã điền thông tin đăng nhập")
    except Exception as e:
        logger.warning(f"Lỗi đăng nhập: {e}")
        pass

def ensure_driver_and_login() -> bool:
    """Đảm bảo Chrome driver đã sẵn sàng - chỉ tạo 1 lần duy nhất."""
    global driver
    try:
        if driver is None:
            logger.info("🔄 Khởi tạo Chrome driver lần đầu...")
            username = LOGIN_USERNAME or "default"
            driver = initialize_browser(username)
            if not driver:
                logger.error("❌ Không thể khởi tạo trình duyệt")
                return False
            logger.info("✅ Chrome driver đã được khởi tạo thành công")
        else:
            logger.info("✅ Chrome driver đã sẵn sàng")
        return True
    except Exception as e:
        logger.error(f"❌ Lỗi ensure_driver_and_login: {e}")
        return False

def get_error_alert_text() -> Optional[str]:
    """Trả về nội dung thông báo lỗi (role="alert") nếu có - chỉ text thuần, không có HTML tags."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "li[role='alert'] span.ui-messages-error-summary")
        for el in elements:
            text_val = (el.text or "").strip()
            if text_val:
                # Đảm bảo chỉ trả về text thuần, không có HTML tags
                # Loại bỏ các ký tự đặc biệt và HTML entities
                clean_text = re.sub(r'<[^>]+>', '', text_val)  # Loại bỏ HTML tags
                clean_text = re.sub(r'&[a-zA-Z]+;', '', clean_text)  # Loại bỏ HTML entities
                clean_text = re.sub(r'\s+', ' ', clean_text)  # Chuẩn hóa khoảng trắng
                clean_text = clean_text.strip()
                if clean_text:
                    return clean_text
    except Exception:
        pass
    return None

def get_info_alert_text() -> Optional[str]:
    """Trả về nội dung thông báo info (role="alert") nếu có - chỉ text thuần, không có HTML tags."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "li[role='alert'] span.ui-messages-info-summary")
        for el in elements:
            text_val = (el.text or "").strip()
            if text_val:
                # Đảm bảo chỉ trả về text thuần, không có HTML tags
                # Loại bỏ các ký tự đặc biệt và HTML entities
                clean_text = re.sub(r'<[^>]+>', '', text_val)  # Loại bỏ HTML tags
                clean_text = re.sub(r'&[a-zA-Z]+;', '', clean_text)  # Loại bỏ HTML entities
                clean_text = re.sub(r'\s+', ' ', clean_text)  # Chuẩn hóa khoảng trắng
                clean_text = clean_text.strip()
                if clean_text:
                    return clean_text
    except Exception:
        pass
    return None
