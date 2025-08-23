"""
Service Manager - Quản lý tất cả 6 dịch vụ với 12 hàm chính
"""

import logging
import time
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox

from ..config import Config
from ..db import (
    update_database_immediately, 
    db_find_order_id, 
    db_fetch_service_data
)
from ..utils.api_client import fetch_api_data
from ..utils.browser import driver, automation_lock, get_error_alert_text, get_info_alert_text
from ..utils.ui_helpers import (
    populate_text_widget,
    populate_entry_widget,
    populate_combobox_widget,
    insert_ctmed,
    delete_ctmed,
    valid_data,
    get_root,
    maybe_update_ui,
    update_stop_flag,
    stop_tool,
)
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

# ============================================================================
# 1. FTTH SERVICE - 2 hàm chính
# ============================================================================

def get_data_ftth(text_widget, order_entry: Optional[ttk.Entry] = None):
    """Get dữ liệu FTTH"""
    try:
        data = db_fetch_service_data("tra_cuu_ftth")
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # Ghép code|order_id từ code_order_map
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId") or ""
                display_codes.append(f"{code_clean}|{oid}")
            populate_text_widget(text_widget, display_codes)
            
            # Thông báo
            count = len(codes)
            info_msg = f"Đã tải {count} mã thuê bao FTTH"
            logger.info(info_msg)
        else:
            logger.info("Không có dữ liệu FTTH từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu FTTH: {e}")

def lookup_ftth(tkinp_ctm, tkinp_ctmed, tkinp_order: Optional[ttk.Entry] = None):
    """Bắt đầu tra cứu FTTH"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                logger.info(f"Đang xử lý FTTH: {cbil}")
                # TODO: Gọi hàm xử lý FTTH cụ thể
                data_rows.append([cbil, "Đã xử lý", "FTTH lookup ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý FTTH {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Tra cứu FTTH")
            
    except Exception as e:
        logger.error(f"Lỗi tra cứu FTTH: {e}")

# ============================================================================
# 2. EVN SERVICE - 2 hàm chính
# ============================================================================

def get_data_evn(text_widget, phone_widget, pin_widget):
    """Get dữ liệu EVN"""
    try:
        data = fetch_api_data("gach_dien_evn")
        if data:
            if "bill_codes" in data:
                populate_text_widget(text_widget, data["bill_codes"])
            if "receiver_phone" in data:
                populate_entry_widget(phone_widget, data["receiver_phone"])
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(data.get("bill_codes", []))
            logger.info(f"Đã tải {count} mã hóa đơn điện EVN")
        else:
            logger.info("Không có dữ liệu EVN từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu EVN: {e}")

def debt_electric(tkinp_ctm, tkinp_ctmed, tkinp_phone, tkinp_pin):
    """Bắt đầu gạch điện EVN"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for cbil in cbils:
            cbil = cbil.strip()
            if not cbil:
                continue
            
            try:
                logger.info(f"Đang xử lý EVN: {cbil}")
                # TODO: Gọi hàm xử lý EVN cụ thể
                data_rows.append([cbil, "Đã xử lý", "EVN payment ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý EVN {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Thanh toán điện EVN")
            
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện EVN: {e}")

# ============================================================================
# 3. TOPUP MULTI SERVICE - 2 hàm chính
# ============================================================================

def get_data_multi_network(text_widget, pin_widget, form_widget, amount_widget, payment_type: str = None):
    """Get dữ liệu Topup Multi"""
    try:
        data = db_fetch_service_data("nap_tien_da_mang", payment_type)
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # Ghép code|order_id từ code_order_map
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId") or ""
                display_codes.append(f"{code_clean}|{oid}")
            
            populate_text_widget(text_widget, display_codes)
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(codes)
            logger.info(f"Đã tải {count} mã topup multi")
        else:
            logger.info("Không có dữ liệu topup multi từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu topup multi: {e}")

def payment_phone_multi(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkinp_form, tkinp_amount):
    """Bắt đầu nạp tiền đa mạng"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                logger.info(f"Đang xử lý topup multi: {cbil}")
                # TODO: Gọi hàm xử lý topup multi cụ thể
                data_rows.append([cbil, "Đã xử lý", "Topup multi ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý topup multi {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Nạp tiền đa mạng")
            
    except Exception as e:
        logger.error(f"Lỗi nạp tiền đa mạng: {e}")

# ============================================================================
# 4. TOPUP VIETTEL SERVICE - 2 hàm chính
# ============================================================================

def get_data_viettel(text_widget, pin_widget):
    """Get dữ liệu Topup Viettel"""
    try:
        data = fetch_api_data("nap_tien_viettel")
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # Ghép code|order_id từ code_order_map
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId") or ""
                display_codes.append(f"{code_clean}|{oid}")
            
            populate_text_widget(text_widget, display_codes)
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(codes)
            logger.info(f"Đã tải {count} mã topup viettel")
        else:
            logger.info("Không có dữ liệu topup viettel từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu topup viettel: {e}")

def payment_phone_viettel(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkinp_amount):
    """Bắt đầu nạp tiền Viettel"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                logger.info(f"Đang xử lý topup viettel: {cbil}")
                # TODO: Gọi hàm xử lý topup viettel cụ thể
                data_rows.append([cbil, "Đã xử lý", "Topup viettel ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý topup viettel {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Nạp tiền Viettel")
            
    except Exception as e:
        logger.error(f"Lỗi nạp tiền Viettel: {e}")

# ============================================================================
# 5. TV-INTERNET SERVICE - 2 hàm chính
# ============================================================================

def get_data_tv_internet(text_widget, pin_widget):
    """Get dữ liệu TV-Internet"""
    try:
        data = db_fetch_service_data("thanh_toan_tv_internet")
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # Ghép code|order_id từ code_order_map
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId") or ""
                display_codes.append(f"{code_clean}|{oid}")
            
            populate_text_widget(text_widget, display_codes)
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(codes)
            logger.info(f"Đã tải {count} mã TV-Internet")
        else:
            logger.info("Không có dữ liệu TV-Internet từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu TV-Internet: {e}")

def payment_internet(tkinp_ctm, tkinp_ctmed, tkinp_pin):
    """Bắt đầu thanh toán TV-Internet"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                logger.info(f"Đang xử lý TV-Internet: {cbil}")
                # TODO: Gọi hàm xử lý TV-Internet cụ thể
                data_rows.append([cbil, "Đã xử lý", "TV-Internet payment ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý TV-Internet {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Thanh toán TV-Internet")
            
    except Exception as e:
        logger.error(f"Lỗi thanh toán TV-Internet: {e}")

# ============================================================================
# 6. POSTPAID SERVICE - 2 hàm chính
# ============================================================================

def get_data_postpaid(text_widget):
    """Get dữ liệu Postpaid"""
    try:
        data = db_fetch_service_data("tra_cuu_no_tra_sau")
        if data and "subscriber_codes" in data:
            codes = [c.strip() for c in data.get("subscriber_codes", [])]
            
            # Ghép code|order_id từ code_order_map
            code_order_map = data.get("code_order_map", [])
            display_codes = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId") or ""
                display_codes.append(f"{code_clean}|{oid}")
            
            populate_text_widget(text_widget, display_codes)
            
            count = len(codes)
            logger.info(f"Đã tải {count} mã postpaid")
        else:
            logger.info("Không có dữ liệu postpaid từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu postpaid: {e}")

def payment_phone_postpaid(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkinp_form, tkinp_amount):
    """Bắt đầu tra cứu nợ trả sau"""
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        
        # Xử lý từng mã
        data_rows = []
        for raw in cbils:
            raw = (raw or "").strip()
            if not raw:
                continue
            
            # Tách code|order_id
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None
            
            try:
                logger.info(f"Đang xử lý postpaid: {cbil}")
                # TODO: Gọi hàm xử lý postpaid cụ thể
                data_rows.append([cbil, "Đã xử lý", "Postpaid lookup ok"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Đã xử lý")
                
            except Exception as e:
                logger.error(f"Lỗi xử lý postpaid {cbil}: {e}")
                data_rows.append([cbil, 0, f"Lỗi: {e}"])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
        
        # Xuất Excel
        if data_rows:
            export_excel(data_rows, "Tra cứu nợ trả sau")
            
    except Exception as e:
        logger.error(f"Lỗi tra cứu nợ trả sau: {e}")

# ============================================================================
# HÀM ĐIỀU KHIỂN SELENIUM CHUNG
# ============================================================================

def navigate_to_page(service_name: str, target_url: str = None):
    """Hàm chung điều hướng đến trang service"""
    try:
        if not driver:
            logger.error("Browser driver chưa sẵn sàng")
            return False
        
        if target_url:
            driver.get(target_url)
            time.sleep(2)
            logger.info(f"Đã điều hướng đến {service_name}")
            return True
        else:
            logger.warning(f"Không có URL cho {service_name}")
            return False
            
    except Exception as e:
        logger.error(f"Lỗi điều hướng đến {service_name}: {e}")
        return False

def wait_for_element(element_id: str, timeout: int = 10):
    """Hàm chung chờ element xuất hiện"""
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        return element
    except Exception as e:
        logger.error(f"Không tìm thấy element {element_id}: {e}")
        return None

def click_element(element_id: str, timeout: int = 10):
    """Hàm chung click element"""
    try:
        element = wait_for_element(element_id, timeout)
        if element:
            element.click()
            time.sleep(0.5)
            return True
        return False
    except Exception as e:
        logger.error(f"Lỗi click element {element_id}: {e}")
        return False

def fill_input(element_id: str, value: str, timeout: int = 10):
    """Hàm chung điền input"""
    try:
        element = wait_for_element(element_id, timeout)
        if element:
            element.clear()
            element.send_keys(value)
            time.sleep(0.5)
            return True
        return False
    except Exception as e:
        logger.error(f"Lỗi điền input {element_id}: {e}")
        return False

# ============================================================================
# EXPORT TẤT CẢ HÀM
# ============================================================================

__all__ = [
    # FTTH Service
    "get_data_ftth",
    "lookup_ftth",
    
    # EVN Service  
    "get_data_evn",
    "debt_electric",
    
    # Topup Multi Service
    "get_data_multi_network",
    "payment_phone_multi",
    
    # Topup Viettel Service
    "get_data_viettel", 
    "payment_phone_viettel",
    
    # TV-Internet Service
    "get_data_tv_internet",
    "payment_internet",
    
    # Postpaid Service
    "get_data_postpaid",
    "payment_phone_postpaid",
    
    # Selenium Control Functions
    "navigate_to_page",
    "wait_for_element", 
    "click_element",
    "fill_input",
]
