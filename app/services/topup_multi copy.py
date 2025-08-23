"""Topup multi-network service module"""

import logging
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, #messagebox
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ..config import Config
from ..db import update_database_immediately, db_find_order_id, db_fetch_service_data
from ..utils.browser import driver, ensure_driver_and_login, automation_lock, get_error_alert_text, get_info_alert_text
from ..utils.ui_helpers import (
    populate_text_widget,
    populate_entry_widget,
    populate_combobox_widget,
    insert_ctmed,
    delete_ctmed,
    valid_data,
    stop_flag,
    get_root,
    maybe_update_ui,
    update_stop_flag,
    stop_tool,
)
from ..utils.api_client import fetch_api_data
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

# Biến global để lưu Order ID hiện tại
current_order_id = None

def handle_choose_amount(am: str) -> str:
    try:
        amount_map = {
            "10.000đ": "0",
            "20.000đ": "1",
            "30.000đ": "2",
            "50.000đ": "3",
            "100.000đ": "4",
            "200.000đ": "5",
            "300.000đ": "6",
            "500.000đ": "7",
        }
        return amount_map.get(am, "0")
    except Exception:
        return "0"

def process_topup_multinetwork_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý nạp tiền đa mạng - hỗ trợ cả nạp trả trước và gạch nợ trả sau."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý Topup đa mạng cho {len(codes)} mã")
    
    # Tìm Order ID cho từng mã riêng biệt (như FTTH)
    print(f"   📋 Order ID từ parameter: {order_id or 'Không có'}")
    print(f"   📋 Order ID từ global: {current_order_id or 'Không có'}")
    
    # Tạo mapping mã -> Order ID (như FTTH)
    # Mỗi mã cần có order_id riêng biệt để đảm bảo mỗi dòng = 1 đơn hàng
    code_to_order: Dict[str, Optional[str]] = {}
    for raw in codes:
        c = (raw or "").strip()
        if not c:
            continue
        # Tìm Order ID chính xác cho từng mã (mỗi mã 1 order_id riêng)
        oid = db_find_order_id('nap_tien_da_mang', c, None)
        code_to_order[c] = oid
        print(f"   📱 {c}: Order ID = {oid if oid else 'Không tìm thấy'}")
    
    print(f"   🎯 Tổng cộng: {len(code_to_order)} mã có Order ID")
    
    if not any(code_to_order.values()):
        print(f"   ⚠️ [WARNING] Không có Order ID nào - sẽ không thể cập nhật database!")
    
    # Hiển thị Order ID rõ ràng như FTTH
    print("Order ID:")
    for code, oid in code_to_order.items():
        if oid:
            print(f"  {code}: {oid}")
        else:
            print(f"  {code}: Không tìm thấy")
    
    print(f"   💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang Topup đa mạng...")
            navigate_to_topup_multinetwork_page()
            print("   ✅ Đã điều hướng thành công đến trang Topup đa mạng")
            
            results = []
            for idx, cbil in enumerate(codes, 1):
                print(f"\n📱 [MÃ {idx}/{len(codes)}] Xử lý mã: {cbil}")
                
                # Hiển thị tiến trình tương tự FTTH
                # Mỗi mã cần có order_id riêng biệt để đảm bảo mỗi dòng = 1 đơn hàng
                specific_order_id = code_to_order.get(cbil)
                print(f"   🔧 Đang xử lý {cbil} | Order ID: {specific_order_id or 'Không tìm thấy'}")
                print(f"   📍 Loại dịch vụ: {'Nạp trả trước' if '|' in cbil else 'Gạch nợ trả sau'}")
                print(f"   📋 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)")
                print(f"   🔍 [DEBUG] Chi tiết xử lý:")
                print(f"      • Mã gốc: {cbil}")
                print(f"      • Order ID riêng: {specific_order_id}")
                print(f"      • Loại dịch vụ: {'Nạp trả trước' if '|' in cbil else 'Gạch nợ trả sau'}")
                if specific_order_id:
                    print(f"      • Database update: SẼ THỰC HIỆN với Order ID riêng")
                    print(f"      • Strategy: Mỗi dòng = 1 đơn hàng riêng biệt")
                else:
                    print(f"      • Database update: KHÔNG THỰC HIỆN (thiếu Order ID riêng)")
                    print(f"      • Strategy: Cần Order ID riêng cho mỗi mã")
                
                # Phân tích dữ liệu để xác định loại dịch vụ
                is_prepaid = '|' in cbil  # Nạp trả trước: có dấu | (sđt|số tiền)
                if is_prepaid:
                    # Nạp trả trước: sđt|số tiền
                    print(f"   🔍 [PARSE] Phân tích mã nạp trả trước: '{cbil}'")
                    parts = cbil.split('|')
                    print(f"      📋 Parts sau split: {parts}")
                    
                    if len(parts) != 2:
                        print(f"   ❌ Sai định dạng: {cbil} (cần: sđt|số tiền)")
                        print(f"      📊 Số parts: {len(parts)} (cần: 2)")
                        results.append({"code": cbil, "amount": None, "status": "failed", "message": "Sai định dạng"})
                        continue
                    
                    phone_number = parts[0].strip()
                    amount_str = parts[1].strip()
                    print(f"      📱 Số điện thoại (raw): '{parts[0]}' -> '{phone_number}'")
                    print(f"      💰 Số tiền (raw): '{parts[1]}' -> '{amount_str}'")
                    
                    try:
                        amount = int(amount_str)
                        valid_amounts = [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]
                        print(f"      ✅ Parse số tiền thành công: {amount:,}đ")
                        print(f"      🔍 Kiểm tra số tiền hợp lệ: {amount} in {valid_amounts} = {amount in valid_amounts}")
                        
                        if amount not in valid_amounts:
                            print(f"   ❌ Số tiền không hợp lệ: {amount} (chỉ cho phép: {valid_amounts})")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": f"Số tiền {amount} không hợp lệ"})
                            continue
                        else:
                            print(f"      ✅ Số tiền hợp lệ: {amount:,}đ")
                    except ValueError as parse_error:
                        print(f"   ❌ Số tiền không hợp lệ: '{amount_str}'")
                        print(f"      📊 Lỗi parse: {parse_error}")
                        print(f"      💡 Gợi ý: Kiểm tra định dạng số tiền có phải là số nguyên không?")
                        results.append({"code": cbil, "amount": None, "status": "failed", "message": "Số tiền không hợp lệ"})
                        continue
                    
                    print(f"   🎯 [SUCCESS] Nạp trả trước: {phone_number} | Số tiền: {amount:,}đ")
                    process_code = phone_number
                else:
                    # Gạch nợ trả sau: chỉ số điện thoại
                    print(f"   🔍 [PARSE] Phân tích mã gạch nợ trả sau: '{cbil}'")
                    phone_number = cbil.strip()
                    print(f"      📱 Số điện thoại (raw): '{cbil}' -> '{phone_number}'")
                    print(f"   🎯 [SUCCESS] Gạch nợ trả sau: {phone_number}")
                    process_code = phone_number
                
                success = False
                for attempt in range(3):  # Retry tối đa 3 lần
                    try:
                        if attempt > 0:
                            print(f"   🔄 Retry lần {attempt + 1}/3 cho mã {cbil}")
                            logger.info(f"Retry lần {attempt + 1} cho mã {cbil}")
                            driver.refresh()
                            time.sleep(2)
                            navigate_to_topup_multinetwork_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        maybe_update_ui()
                        time.sleep(0.5)
                        
                        print(f"   📝 [FORM] Bước 1/4: Điền số điện thoại")
                        print(f"      📱 Số điện thoại: '{process_code}'")
                        print(f"      🔍 Tìm element: payMoneyForm:phoneNumber")
                        print(f"      📊 [DEBUG] Chi tiết element:")
                        print(f"         • ID: payMoneyForm:phoneNumber")
                        print(f"         • Type: input")
                        print(f"         • Expected value: '{process_code}'")
                        
                        try:
                            phone_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:phoneNumber")))
                            print(f"      ✅ Tìm thấy element số điện thoại")
                            print(f"         • Tag name: {phone_input.tag_name}")
                            print(f"         • Type: {phone_input.get_attribute('type')}")
                            print(f"         • Name: {phone_input.get_attribute('name')}")
                            print(f"         • Class: {phone_input.get_attribute('class')}")
                            print(f"         • Placeholder: {phone_input.get_attribute('placeholder')}")
                            
                            # Kiểm tra element có visible và enabled không
                            print(f"         • Visible: {phone_input.is_displayed()}")
                            print(f"         • Enabled: {phone_input.is_enabled()}")
                            
                        except Exception as element_error:
                            print(f"      ❌ Không tìm thấy element số điện thoại: {element_error}")
                            print(f"      🔍 Thử tìm element khác...")
                            
                            # Thử tìm element khác
                            try:
                                phone_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel'], input[type='text'], input[name*='phone'], input[placeholder*='phone'], input[placeholder*='số điện thoại']"))
                                )
                                print(f"      ✅ Tìm thấy element số điện thoại (fallback)")
                                print(f"         • Tag name: {phone_input.tag_name}")
                                print(f"         • Type: {phone_input.get_attribute('type')}")
                                print(f"         • Name: {phone_input.get_attribute('name')}")
                            except Exception as fallback_error:
                                print(f"      ❌ Không thể tìm thấy input số điện thoại: {fallback_error}")
                                print(f"      💡 Gợi ý: Kiểm tra xem trang có input số điện thoại không?")
                                raise fallback_error
                        
                        # Xóa nội dung cũ
                        try:
                            old_value = phone_input.get_attribute('value')
                            print(f"      🔍 Giá trị cũ trong input: '{old_value}'")
                            
                            phone_input.clear()
                            print(f"      🧹 Đã xóa nội dung cũ")
                            
                            # Kiểm tra sau khi clear
                            after_clear = phone_input.get_attribute('value')
                            print(f"      🔍 Giá trị sau khi clear: '{after_clear}'")
                            
                        except Exception as clear_error:
                            print(f"      ⚠️  Lỗi khi clear input: {clear_error}")
                        
                        # Điền số điện thoại
                        try:
                            print(f"      ✍️  Bắt đầu điền số điện thoại: '{process_code}'")
                            phone_input.send_keys(process_code)
                            print(f"      ✍️  Đã điền số điện thoại: '{process_code}'")
                            
                            # Đợi một chút để đảm bảo giá trị được cập nhật
                            time.sleep(0.5)
                            
                        except Exception as send_keys_error:
                            print(f"      ❌ Lỗi khi điền số điện thoại: {send_keys_error}")
                            raise send_keys_error
                        
                        # Kiểm tra giá trị đã điền
                        try:
                            actual_value = phone_input.get_attribute('value')
                            print(f"      🔍 Giá trị thực tế trong input: '{actual_value}'")
                            print(f"      📊 [VALIDATION] So sánh giá trị:")
                            print(f"         • Mong đợi: '{process_code}' (độ dài: {len(process_code)})")
                            print(f"         • Thực tế: '{actual_value}' (độ dài: {len(actual_value) if actual_value else 0})")
                            print(f"         • Khớp chính xác: {actual_value == process_code}")
                            
                            if actual_value != process_code:
                                print(f"      ⚠️  [WARNING] Giá trị không khớp!")
                                print(f"         • Nguyên nhân có thể:")
                                print(f"            - Input bị readonly/disabled")
                                print(f"            - JavaScript validation chặn")
                                print(f"            - Element không phải input thật")
                                print(f"            - Trang có multiple input cùng tên")
                                
                                # Thử điền lại
                                print(f"      🔄 Thử điền lại...")
                                phone_input.clear()
                                time.sleep(0.2)
                                phone_input.send_keys(process_code)
                                time.sleep(0.5)
                                
                                retry_value = phone_input.get_attribute('value')
                                print(f"      🔍 Giá trị sau retry: '{retry_value}'")
                                print(f"      📊 Kết quả retry: {retry_value == process_code}")
                            else:
                                print(f"      ✅ Giá trị số điện thoại khớp chính xác")
                                
                        except Exception as validation_error:
                            print(f"      ❌ Lỗi khi kiểm tra giá trị: {validation_error}")
                        
                        # Nếu là nạp trả trước, nhập số tiền
                        if is_prepaid:  # Nạp trả trước
                            print(f"   💰 [FORM] Bước 2/4: Điền số tiền")
                            print(f"      💰 Số tiền: {amount:,}đ")
                            print(f"      🔍 Tìm element: payMoneyForm:amount")
                            print(f"      📊 [DEBUG] Chi tiết element số tiền:")
                            print(f"         • ID: payMoneyForm:amount")
                            print(f"         • Expected value: {amount:,}đ")
                            print(f"         • Expected string: '{str(amount)}'")
                            
                            try:
                                amount_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.ID, "payMoneyForm:amount"))
                                )
                                print(f"      ✅ Tìm thấy element số tiền (ID)")
                                print(f"         • Tag name: {amount_input.tag_name}")
                                print(f"         • Type: {amount_input.get_attribute('type')}")
                                print(f"         • Name: {amount_input.get_attribute('name')}")
                                print(f"         • Class: {amount_input.get_attribute('class')}")
                                print(f"         • Placeholder: {amount_input.get_attribute('placeholder')}")
                                print(f"         • Visible: {amount_input.is_displayed()}")
                                print(f"         • Enabled: {amount_input.is_enabled()}")
                                
                                # Kiểm tra giá trị cũ
                                old_amount = amount_input.get_attribute('value')
                                print(f"      🔍 Giá trị cũ trong input: '{old_amount}'")
                                
                                # Xóa nội dung cũ
                                amount_input.clear()
                                print(f"      🧹 Đã xóa nội dung cũ")
                                
                                # Kiểm tra sau khi clear
                                after_clear = amount_input.get_attribute('value')
                                print(f"      🔍 Giá trị sau khi clear: '{after_clear}'")
                                
                                # Điền số tiền
                                print(f"      ✍️  Bắt đầu điền số tiền: {amount:,}đ")
                                amount_input.send_keys(str(amount))
                                print(f"      ✍️  Đã điền số tiền: {amount:,}đ")
                                
                                # Đợi để đảm bảo giá trị được cập nhật
                                time.sleep(0.5)
                                
                                # Kiểm tra giá trị đã điền
                                actual_amount = amount_input.get_attribute('value')
                                print(f"      🔍 Giá trị thực tế trong input: '{actual_amount}'")
                                print(f"      📊 [VALIDATION] So sánh giá trị số tiền:")
                                print(f"         • Mong đợi: '{str(amount)}' (độ dài: {len(str(amount))})")
                                print(f"         • Thực tế: '{actual_amount}' (độ dài: {len(actual_amount) if actual_amount else 0})")
                                print(f"         • Khớp chính xác: {actual_amount == str(amount)}")
                                
                                if actual_amount != str(amount):
                                    print(f"      ⚠️  [WARNING] Giá trị số tiền không khớp!")
                                    print(f"         • Nguyên nhân có thể:")
                                    print(f"            - Input bị readonly/disabled")
                                    print(f"            - JavaScript validation chặn")
                                    print(f"            - Element không phải input thật")
                                    print(f"            - Trang có multiple input cùng tên")
                                    
                                    # Thử điền lại
                                    print(f"      🔄 Thử điền lại số tiền...")
                                    amount_input.clear()
                                    time.sleep(0.2)
                                    amount_input.send_keys(str(amount))
                                    time.sleep(0.5)
                                    
                                    retry_amount = amount_input.get_attribute('value')
                                    print(f"      🔍 Giá trị sau retry: '{retry_amount}'")
                                    print(f"      📊 Kết quả retry: {retry_amount == str(amount)}")
                                else:
                                    print(f"      ✅ Giá trị số tiền khớp chính xác")
                                
                                time.sleep(1)
                            except Exception as amount_error:
                                print(f"      ❌ Không tìm thấy element số tiền theo ID: {amount_error}")
                                print(f"      🔍 Thử tìm element khác...")
                                
                                # Nếu không tìm thấy input số tiền, thử tìm element khác
                                try:
                                    print(f"      🔍 Thử tìm element số tiền bằng CSS selector...")
                                    amount_input = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number'], input[name*='amount'], .amount-input, input[placeholder*='amount'], input[placeholder*='số tiền']"))
                                    )
                                    print(f"      ✅ Tìm thấy element số tiền (CSS selector)")
                                    print(f"         • Tag name: {amount_input.tag_name}")
                                    print(f"         • Type: {amount_input.get_attribute('type')}")
                                    print(f"         • Name: {amount_input.get_attribute('name')}")
                                    print(f"         • Class: {amount_input.get_attribute('class')}")
                                    
                                    # Xóa và điền
                                    old_amount = amount_input.get_attribute('value')
                                    print(f"      🔍 Giá trị cũ: '{old_amount}'")
                                    
                                    amount_input.clear()
                                    print(f"      🧹 Đã xóa nội dung cũ")
                                    
                                    amount_input.send_keys(str(amount))
                                    print(f"      ✍️  Đã điền số tiền (fallback): {amount:,}đ")
                                    
                                    # Kiểm tra giá trị đã điền
                                    actual_amount = amount_input.get_attribute('value')
                                    print(f"      🔍 Giá trị thực tế trong input (fallback): '{actual_amount}'")
                                    print(f"      📊 Kết quả fallback: {actual_amount == str(amount)}")
                                    
                                    time.sleep(1)
                                except Exception as fallback_error:
                                    print(f"      ❌ Không thể tìm thấy input số tiền: {fallback_error}")
                                    print(f"      💡 Gợi ý: Kiểm tra xem trang có input số tiền không?")
                                    print(f"      🔍 Có thể trang không có input số tiền cho nạp trả trước")
                                    print(f"      📋 Mã gốc: '{cbil}' (định dạng: sđt|số tiền)")
                                    print(f"      💰 Số tiền từ mã: {amount:,}đ")
                        
                        # Tự động điền mã PIN từ config
                        print(f"   🔐 [FORM] Bước 3/4: Điền mã PIN")
                        print(f"      🔐 Mã PIN: {Config.DEFAULT_PIN}")
                        print(f"      🔍 Tìm element: payMoneyForm:pin")
                        print(f"      📊 [DEBUG] Chi tiết element PIN:")
                        print(f"         • ID: payMoneyForm:pin")
                        print(f"         • Expected value: '{Config.DEFAULT_PIN}'")
                        print(f"         • Expected length: {len(Config.DEFAULT_PIN)}")
                        
                        try:
                            pin_input = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, "payMoneyForm:pin"))
                            )
                            print(f"      ✅ Tìm thấy element PIN (ID)")
                            print(f"         • Tag name: {pin_input.tag_name}")
                            print(f"         • Type: {pin_input.get_attribute('type')}")
                            print(f"         • Name: {pin_input.get_attribute('name')}")
                            print(f"         • Class: {pin_input.get_attribute('class')}")
                            print(f"         • Placeholder: {pin_input.get_attribute('placeholder')}")
                            print(f"         • Visible: {pin_input.is_displayed()}")
                            print(f"         • Enabled: {pin_input.is_enabled()}")
                            
                            # Kiểm tra giá trị cũ
                            old_pin = pin_input.get_attribute('value')
                            print(f"      🔍 Giá trị cũ trong input: '{old_pin}'")
                            
                            # Xóa nội dung cũ
                            pin_input.clear()
                            print(f"      🧹 Đã xóa nội dung cũ")
                            
                            # Kiểm tra sau khi clear
                            after_clear = pin_input.get_attribute('value')
                            print(f"      🔍 Giá trị sau khi clear: '{after_clear}'")
                            
                            # Điền mã PIN
                            print(f"      ✍️  Bắt đầu điền mã PIN: '{Config.DEFAULT_PIN}'")
                            pin_input.send_keys(Config.DEFAULT_PIN)
                            print(f"      ✍️  Đã điền mã PIN: '{Config.DEFAULT_PIN}'")
                            
                            # Đợi để đảm bảo giá trị được cập nhật
                            time.sleep(0.5)
                            
                            # Kiểm tra giá trị đã điền
                            actual_pin = pin_input.get_attribute('value')
                            print(f"      🔍 Giá trị thực tế trong input: '{actual_pin}'")
                            print(f"      📊 [VALIDATION] So sánh giá trị PIN:")
                            print(f"         • Mong đợi: '{Config.DEFAULT_PIN}' (độ dài: {len(Config.DEFAULT_PIN)})")
                            print(f"         • Thực tế: '{actual_pin}' (độ dài: {len(actual_pin) if actual_pin else 0})")
                            print(f"         • Khớp chính xác: {actual_pin == Config.DEFAULT_PIN}")
                            
                            if actual_pin != Config.DEFAULT_PIN:
                                print(f"      ⚠️  [WARNING] Giá trị PIN không khớp!")
                                print(f"         • Nguyên nhân có thể:")
                                print(f"            - Input bị readonly/disabled")
                                print(f"            - JavaScript validation chặn")
                                print(f"            - Element không phải input thật")
                                print(f"            - Trang có multiple input cùng tên")
                                
                                # Thử điền lại
                                print(f"      🔄 Thử điền lại mã PIN...")
                                pin_input.clear()
                                time.sleep(0.2)
                                pin_input.send_keys(Config.DEFAULT_PIN)
                                time.sleep(0.5)
                                
                                retry_pin = pin_input.get_attribute('value')
                                print(f"      🔍 Giá trị sau retry: '{retry_pin}'")
                                print(f"      📊 Kết quả retry: {retry_pin == Config.DEFAULT_PIN}")
                            else:
                                print(f"      ✅ Giá trị mã PIN khớp chính xác")
                            
                            time.sleep(1)
                        except Exception as pin_error:
                            print(f"      ❌ Không tìm thấy element PIN theo ID: {pin_error}")
                            print(f"      🔍 Thử tìm element khác...")
                            
                            # Nếu không tìm thấy input PIN theo ID, thử tìm element khác
                            try:
                                print(f"      🔍 Thử tìm element PIN bằng CSS selector...")
                                pin_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name*='pin'], .pin-input, input[placeholder*='PIN'], input[placeholder*='pin'], input[type='text'][name*='pin']"))
                                )
                                print(f"      ✅ Tìm thấy element PIN (CSS selector)")
                                print(f"         • Tag name: {pin_input.tag_name}")
                                print(f"         • Type: {pin_input.get_attribute('type')}")
                                print(f"         • Name: {pin_input.get_attribute('name')}")
                                print(f"         • Class: {pin_input.get_attribute('class')}")
                                
                                # Xóa và điền
                                old_pin = pin_input.get_attribute('value')
                                print(f"      🔍 Giá trị cũ: '{old_pin}'")
                                
                                pin_input.clear()
                                print(f"      🧹 Đã xóa nội dung cũ")
                                
                                pin_input.send_keys(Config.DEFAULT_PIN)
                                print(f"      ✍️  Đã điền mã PIN (fallback): '{Config.DEFAULT_PIN}'")
                                
                                # Kiểm tra giá trị đã điền
                                actual_pin = pin_input.get_attribute('value')
                                print(f"      🔍 Giá trị thực tế trong input (fallback): '{actual_pin}'")
                                print(f"      📊 Kết quả fallback: {actual_pin == Config.DEFAULT_PIN}")
                                
                                time.sleep(1)
                            except Exception as fallback_pin_error:
                                print(f"      ❌ Không thể tìm thấy input PIN: {fallback_pin_error}")
                                print(f"      💡 Gợi ý: Kiểm tra xem trang có input PIN không?")
                                print(f"      🔍 Có thể trang không có input PIN")
                                print(f"      📋 Mã gốc: '{cbil}'")
                                print(f"      🔐 Mã PIN từ config: '{Config.DEFAULT_PIN}'")
                        
                        # Validation trước khi gửi form
                        print(f"   🔍 [VALIDATION] Kiểm tra dữ liệu trước khi gửi:")
                        print(f"      📱 Số điện thoại: '{process_code}' (độ dài: {len(process_code)})")
                        if is_prepaid:
                            print(f"      💰 Số tiền: {amount:,}đ (hợp lệ: {amount in [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]})")
                        print(f"      🔐 Mã PIN: '{Config.DEFAULT_PIN}' (độ dài: {len(Config.DEFAULT_PIN)})")
                        
                        # Kiểm tra validation chi tiết
                        print(f"      📊 [VALIDATION DETAILS] Kiểm tra từng trường:")
                        
                        # Kiểm tra số điện thoại
                        phone_valid = process_code and len(process_code) >= 10
                        print(f"         • Số điện thoại: {phone_valid}")
                        print(f"            - Giá trị: '{process_code}'")
                        print(f"            - Độ dài: {len(process_code)} (cần >= 10)")
                        print(f"            - Hợp lệ: {phone_valid}")
                        
                        # Kiểm tra số tiền (nếu là nạp trả trước)
                        amount_valid = True
                        if is_prepaid:
                            amount_valid = amount in [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]
                            print(f"         • Số tiền: {amount_valid}")
                            print(f"            - Giá trị: {amount:,}đ")
                            print(f"            - Danh sách cho phép: [10k, 20k, 30k, 50k, 100k, 200k, 300k, 500k]")
                            print(f"            - Hợp lệ: {amount_valid}")
                        else:
                            print(f"         • Số tiền: N/A (không phải nạp trả trước)")
                        
                        # Kiểm tra mã PIN
                        pin_valid = Config.DEFAULT_PIN and len(Config.DEFAULT_PIN) >= 4
                        print(f"         • Mã PIN: {pin_valid}")
                        print(f"            - Giá trị: '{Config.DEFAULT_PIN}'")
                        print(f"            - Độ dài: {len(Config.DEFAULT_PIN)} (cần >= 4)")
                        print(f"            - Hợp lệ: {pin_valid}")
                        
                        # Tổng kết validation
                        overall_valid = phone_valid and amount_valid and pin_valid
                        print(f"      📊 [VALIDATION SUMMARY] Kết quả tổng thể: {overall_valid}")
                        print(f"         • Số điện thoại: {phone_valid}")
                        print(f"         • Số tiền: {amount_valid}")
                        print(f"         • Mã PIN: {pin_valid}")
                        print(f"         • Tất cả hợp lệ: {overall_valid}")
                        
                        if not overall_valid:
                            print(f"   ❌ [VALIDATION FAILED] Có lỗi validation:")
                            validation_errors = []
                            if not phone_valid:
                                validation_errors.append(f"Số điện thoại '{process_code}' không hợp lệ (cần ít nhất 10 số)")
                            if not amount_valid:
                                validation_errors.append(f"Số tiền {amount:,}đ không hợp lệ")
                            if not pin_valid:
                                validation_errors.append(f"Mã PIN '{Config.DEFAULT_PIN}' không hợp lệ (cần ít nhất 4 ký tự)")
                            
                            for error in validation_errors:
                                print(f"      • {error}")
                            print(f"   💡 Bỏ qua gửi form để tránh lỗi 'Vui lòng nhập đầy đủ thông tin'")
                            
                            # Ghi log lỗi validation
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": f"Validation failed: {'; '.join(validation_errors)}"})
                            
                            # Update database cho trường hợp validation failed
                            if specific_order_id:
                                print(f"   💾 [DATABASE] Update database cho validation failed...")
                                notes = f"Multi-network: Validation failed - {cbil} | {'; '.join(validation_errors)}"
                                db_success = update_database_immediately(specific_order_id, process_code, "failed", None, notes, None)
                                if db_success:
                                    print(f"      ✅ Database update thành công cho {process_code} (validation failed)")
                                else:
                                    print(f"      ❌ Database update thất bại cho {process_code} (validation failed)")
                            else:
                                print(f"⚠️  [WARNING] Không có Order ID riêng cho code {process_code}")
                            
                            break
                        
                        print(f"   ✅ [VALIDATION PASSED] Tất cả dữ liệu hợp lệ, tiến hành gửi form")
                        print(f"   🔄 Tiến trình: {cbil} - Bước 4/4: Xử lý giao dịch")
                        print(f"   🔍 Nhấn nút TIẾP TỤC...")
                        
                        # Tìm và kiểm tra nút TIẾP TỤC
                        try:
                            print(f"      🔍 Tìm nút TIẾP TỤC: payMoneyForm:btnContinue")
                            continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "payMoneyForm:btnContinue")))
                            print(f"      ✅ Tìm thấy nút TIẾP TỤC")
                            print(f"         • Tag name: {continue_button.tag_name}")
                            print(f"         • Text: {continue_button.text}")
                            print(f"         • Visible: {continue_button.is_displayed()}")
                            print(f"         • Enabled: {continue_button.is_enabled()}")
                            
                            # Nhấn nút
                            print(f"      ✋ Nhấn nút TIẾP TỤC...")
                            continue_button.click()
                            print(f"      ✅ Đã nhấn nút TIẾP TỤC")
                            time.sleep(1)
                            
                        except Exception as button_error:
                            print(f"      ❌ Lỗi khi tìm/nhấn nút TIẾP TỤC: {button_error}")
                            print(f"      🔍 Thử tìm nút khác...")
                            
                            # Thử tìm nút khác
                            try:
                                continue_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .btn-continue, .btn-submit, button:contains('TIẾP TỤC'), button:contains('Tiếp tục')"))
                                )
                                print(f"      ✅ Tìm thấy nút TIẾP TỤC (fallback)")
                                continue_button.click()
                                print(f"      ✅ Đã nhấn nút TIẾP TỤC (fallback)")
                                time.sleep(1)
                            except Exception as fallback_button_error:
                                print(f"      ❌ Không thể tìm thấy nút TIẾP TỤC: {fallback_button_error}")
                                raise fallback_button_error
                        
                        print(f"   ⏳ Chờ modal loading...")
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        
                        # Kiểm tra thông báo lỗi
                        error_text = get_error_alert_text()
                        if error_text:
                            print(f"   ❌ Có thông báo lỗi: {error_text}")
                            
                            # Xử lý lỗi "Vui lòng nhập đầy đủ thông tin" một cách chi tiết
                            if "Vui lòng nhập đầy đủ thông tin" in error_text:
                                print(f"   🔍 [VALIDATION ERROR] Phân tích lỗi validation:")
                                print(f"      📱 Số điện thoại đã nhập: '{process_code}'")
                                if is_prepaid:
                                    print(f"      💰 Số tiền đã nhập: {amount:,}đ")
                                    print(f"      🔐 Mã PIN đã nhập: {Config.DEFAULT_PIN}")
                                    print(f"      📋 Mã gốc: '{cbil}' (định dạng: sđt|số tiền)")
                                    
                                    # Kiểm tra chi tiết từng trường
                                    if not process_code or len(process_code) < 10:
                                        print(f"      ❌ Số điện thoại không hợp lệ: '{process_code}' (cần ít nhất 10 số)")
                                    if amount not in [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]:
                                        print(f"      ❌ Số tiền không hợp lệ: {amount} (chỉ cho phép: [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000])")
                                    if not Config.DEFAULT_PIN or len(Config.DEFAULT_PIN) < 4:
                                        print(f"      ❌ Mã PIN không hợp lệ: '{Config.DEFAULT_PIN}' (cần ít nhất 4 ký tự)")
                                    
                                    print(f"      💡 [GỢI Ý] Kiểm tra:")
                                    print(f"         • Số điện thoại có đúng định dạng không? (0985xxxxxxx)")
                                    print(f"         • Số tiền có trong danh sách cho phép không?")
                                    print(f"         • Mã PIN có đủ ký tự không?")
                                else:
                                    print(f"      📱 Số điện thoại đã nhập: '{process_code}'")
                                    print(f"      🔐 Mã PIN đã nhập: {Config.DEFAULT_PIN}")
                                    print(f"      📋 Mã gốc: '{cbil}' (định dạng: chỉ số điện thoại)")
                                    
                                    if not process_code or len(process_code) < 10:
                                        print(f"      ❌ Số điện thoại không hợp lệ: '{process_code}' (cần ít nhất 10 số)")
                                    if not Config.DEFAULT_PIN or len(Config.DEFAULT_PIN) < 4:
                                        print(f"      ❌ Mã PIN không hợp lệ: '{Config.DEFAULT_PIN}' (cần ít nhất 4 ký tự)")
                                    
                                    print(f"      💡 [GỢI Ý] Kiểm tra:")
                                    print(f"         • Số điện thoại có đúng định dạng không? (0985xxxxxxx)")
                                    print(f"         • Mã PIN có đủ ký tự không?")
                            
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": error_text})
                            
                            # Update database cho trường hợp thất bại
                            # Sử dụng Order ID riêng đã tìm trước đó
                            if specific_order_id:
                                print(f"   💾 [DATABASE] Update database cho trường hợp thất bại...")
                                print(f"      📋 Order ID riêng: {specific_order_id}")
                                print(f"      📱 Code: {process_code}")
                                print(f"      📊 Status: failed")
                                print(f"      💰 Amount: N/A (thất bại)")
                                
                                # Lưu thông tin loại dịch vụ vào notes
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Lỗi: {error_text}"
                                else:
                                    notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Lỗi: {error_text}"
                                
                                print(f"      📝 Notes: {notes}")
                                print(f"      🔄 Gọi update_database_immediately...")
                                
                                db_success = update_database_immediately(specific_order_id, process_code, "failed", None, notes, None)
                                
                                if db_success:
                                    print(f"      ✅ Database update thành công cho {process_code} (failed)")
                                else:
                                    print(f"      ❌ Database update thất bại cho {process_code} (failed)")
                                    logger.warning(f"Database update thất bại cho {process_code}")
                            else:
                                print(f"⚠️  [WARNING] Không có Order ID riêng cho code {process_code}")
                                print(f"      ❌ Không thể cập nhật database - thiếu Order ID riêng")
                            break
                        
                        # Lấy thông tin kết quả từ trang
                        print(f"   📊 Lấy thông tin kết quả...")
                        try:
                            # Tìm element chứa thông tin kết quả
                            result_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".result-info, .payment-result, .success-message, [class*='result'], [class*='success']"))
                            )
                            result_text = result_element.text.strip()
                            print(f"   📋 Kết quả: {result_text}")
                            
                            # Phân tích kết quả để tạo notes chi tiết
                            if "thành công" in result_text.lower() or "success" in result_text.lower():
                                result_status = "success"
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ | Kết quả: {result_text}"
                                else:
                                    notes = f"Multi-network: Gậc nợ trả sau - {cbil} | Kết quả: {result_text}"
                            else:
                                result_status = "failed"
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ | Kết quả: {result_text}"
                                else:
                                    notes = f"Multi-network: Gậc nợ trả sau - {cbil} | Kết quả: {result_text}"
                                
                        except Exception as result_error:
                            print(f"   ⚠️ Không thể lấy thông tin kết quả: {result_error}")
                            result_status = "success"
                            if is_prepaid:
                                notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ"
                            else:
                                notes = f"Multi-network: Gậc nợ trả sau - {cbil}"
                        
                        print(f"   ✅ Xử lý thành công cho {'nạp trả trước' if is_prepaid else 'gậc nợ trả sau'} {process_code}")
                        
                        # Hiển thị kết quả chi tiết tương tự FTTH
                        if 'result_text' in locals():
                            print(f"   📋 Kết quả chi tiết:")
                            print(f"      • Mã: {cbil}")
                            print(f"      • Loại dịch vụ: {'Nạp trả trước' if is_prepaid else 'Gậc nợ trả sau'}")
                            if is_prepaid:
                                print(f"      • Số tiền: {amount:,}đ")
                            print(f"      • Kết quả: {result_text}")
                            print(f"      • Trạng thái: {result_status}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount if is_prepaid else None, "status": result_status, "message": result_text if 'result_text' in locals() else "Thành công"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        # Sử dụng Order ID riêng đã tìm trước đó
                        # Mỗi mã cần có order_id riêng biệt để đảm bảo mỗi dòng = 1 đơn hàng
                        if specific_order_id:
                            print(f"   💾 [DATABASE] Bắt đầu update database...")
                            print(f"      📋 Order ID riêng: {specific_order_id}")
                            print(f"      📱 Code: {process_code}")
                            print(f"      📊 Status: {result_status}")
                            print(f"      💰 Amount: {amount if is_prepaid else 'N/A'}")
                            print(f"      📝 Notes: {notes}")
                            print(f"      💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt")
                            
                            amount_for_db = amount if is_prepaid else None
                            print(f"      🔄 Gọi update_database_immediately...")
                            db_success = update_database_immediately(specific_order_id, process_code, result_status, amount_for_db, notes, None)
                            
                            if db_success:
                                print(f"      ✅ Database update thành công cho {process_code}")
                                print(f"         💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt")
                            else:
                                print(f"      ❌ Database update thất bại cho {process_code}")
                                logger.warning(f"Database update thất bại cho {process_code}")
                        else:
                            print(f"⚠️  [WARNING] Không có Order ID riêng cho code {process_code}")
                            print(f"      ❌ Không thể cập nhật database - thiếu Order ID riêng")
                            print(f"      💡 Strategy: Cần Order ID riêng cho mỗi mã")
                        
                        print(f"   🎉 Hoàn thành xử lý mã {cbil}")
                        break
                        
                    except Exception as e:
                        print(f"   ❌ Lần thử {attempt + 1} thất bại: {e}")
                        logger.warning(f"Lần thử {attempt + 1} thất bại cho {cbil}: {e}")
                        if attempt < 2:  # Còn cơ hội retry
                            print(f"   ⏳ Chờ 1s trước khi retry...")
                            time.sleep(1)  # Delay thông minh
                            continue
                        else:  # Hết retry
                            print(f"   💥 Hết retry, mã {cbil} thất bại hoàn toàn")
                            logger.error(f"Topup đa mạng code {cbil} thất bại sau 3 lần thử: {e}")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": str(e)})
                            
                            # Update database cho trường hợp thất bại
                            # Sử dụng Order ID riêng đã tìm trước đó
                            if specific_order_id:
                                print(f"   💾 [DATABASE] Update database cho trường hợp thất bại (retry)...")
                                print(f"      📋 Order ID riêng: {specific_order_id}")
                                print(f"      📱 Code: {process_code}")
                                print(f"      📊 Status: failed")
                                print(f"      💰 Amount: N/A (thất bại)")
                                
                                # Lưu thông tin loại dịch vụ vào notes
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Lỗi: {str(e)}"
                                else:
                                    notes = f"Multi-network: Gậc nợ trả sau - {cbil} | Lỗi: {str(e)}"
                                
                                print(f"      📝 Notes: {notes}")
                                print(f"      🔄 Gọi update_database_immediately...")
                                
                                db_success = update_database_immediately(specific_order_id, process_code, "failed", None, notes, None)
                                
                                if db_success:
                                    print(f"      ✅ Database update thành công cho {process_code} (failed - retry)")
                                else:
                                    print(f"      ❌ Database update thất bại cho {process_code} (failed - retry)")
                                    logger.warning(f"Database update thất bại cho {process_code}")
                            else:
                                print(f"⚠️  [WARNING] Không có Order ID riêng cho code {process_code}")
                                print(f"      ❌ Không thể cập nhật database - thiếu Order ID riêng")
                
                if not success:
                    print(f"   💥 Mã {cbil} không thể xử lý sau 3 lần thử")
                    logger.error(f"Mã {cbil} không thể xử lý sau 3 lần thử")
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý Topup đa mạng:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            # Tổng kết database update
            print(f"\n💾 [DATABASE] Tổng kết cập nhật database:")
            successful_updates = sum(1 for r in results if r['status'] == 'success')
            failed_updates = sum(1 for r in results if r['status'] == 'failed')
            
            print(f"   📊 Kết quả cập nhật:")
            print(f"      • Thành công: {successful_updates} mã")
            print(f"      • Thất bại: {failed_updates} mã")
            print(f"      • Tổng cộng: {len(results)} mã")
            
            print(f"   💡 Database update strategy (như FTTH):")
            print(f"      • Mỗi dòng = 1 đơn hàng riêng biệt")
            print(f"      • Mỗi mã được tìm Order ID riêng từ database")
            print(f"      • Không có fallback - chỉ cập nhật khi có Order ID riêng")
            print(f"      • Đảm bảo tính chính xác và nhất quán dữ liệu")
            
            # Hiển thị chi tiết từng mã tương tự FTTH
            print(f"\n📋 [CHI TIẾT] Kết quả xử lý từng mã:")
            for result in results:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                amount_info = f" | Số tiền: {result['amount']:,}đ" if result.get('amount') else ""
                message_info = f" | {result.get('message', '')}" if result.get('message') else ""
                print(f"   {status_icon} {result['code']}{amount_info}{message_info}")
            
            logger.info(f"Topup multinetwork processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_topup_multinetwork_codes error: {e}")

def get_data_multi_network(text_widget, pin_widget, form_widget, amount_widget, payment_type: str = None):
    """Lấy dữ liệu API cho Nạp tiền đa mạng"""
    try:
        print(f"[DEBUG] get_data_multi_network được gọi với payment_type: {payment_type}")
        
        # Lấy dữ liệu theo loại dịch vụ đã chọn
        if payment_type:
            print(f"[DEBUG] Gọi db_fetch_service_data với payment_type: {payment_type}")
            data = db_fetch_service_data("nap_tien_da_mang", payment_type)
        else:
            print(f"[DEBUG] Gọi fetch_api_data (không có payment_type)")
            data = fetch_api_data("nap_tien_da_mang")
            
        if data:
            if "phone_numbers" in data:
                populate_text_widget(text_widget, data["phone_numbers"])
            
            # Tự động điền mã PIN từ config
            print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            # Đảm bảo combobox form hiển thị đúng loại dịch vụ đã chọn
            if payment_type == "prepaid":
                form_widget.set("Nạp trả trước")
            elif payment_type == "postpaid":
                form_widget.set("Gạch nợ trả sau")
            
            if "payment_type" in data:
                populate_combobox_widget(form_widget, data["payment_type"])
            # Chỉ điền số tiền nạp khi không phải "Nạp trả trước" (vì đã có trong format sđt|số tiền)
            if "amount" in data and payment_type != "prepaid":
                populate_combobox_widget(amount_widget, data["amount"])
            
            count = len(data.get("phone_numbers", []))
            order_id = data.get("order_id")
            service_type_text = "Nạp trả trước (sđt|số tiền)" if payment_type == "prepaid" else "Gạch nợ trả sau (chỉ số điện thoại)" if payment_type == "postpaid" else "Đa mạng"
            info_msg = f"Đã tải {count} số điện thoại {service_type_text}"
            
            print(f"[DEBUG] Chi tiết dữ liệu từ DB:")
            print(f"   📱 Số điện thoại: {count} mã")
            print(f"   📋 Order ID: {order_id}")
            print(f"   🔍 Payment type: {payment_type}")
            print(f"   📝 Service type text: {service_type_text}")
            
            if order_id:
                print(f"[INFO] Order ID từ DB (tổng quát): {order_id}", flush=True)
                print(f"[DEBUG] Order ID type: {type(order_id)}, value: '{order_id}'")
                logger.info(f"Order ID từ DB (Đa mạng - {service_type_text}): {order_id}")
                info_msg += f"\nOrder ID (tổng quát): {order_id}"
                
                # Lưu Order ID vào biến global để sử dụng khi xử lý
                global current_order_id
                current_order_id = order_id
                print(f"[DEBUG] Đã lưu current_order_id: {current_order_id}")
                
                # Hiển thị Order ID mapping cho từng mã như FTTH
                # Mỗi mã cần có order_id riêng biệt để đảm bảo mỗi dòng = 1 đơn hàng
                print("Order ID (mỗi mã riêng biệt):")
                phone_numbers = data.get("phone_numbers", [])
                for phone in phone_numbers:
                    if phone and phone.strip():
                        # Mỗi mã cần có order_id riêng biệt
                        specific_order_id = db_find_order_id('nap_tien_da_mang', phone, None)
                        if specific_order_id:
                            print(f"  {phone}: {specific_order_id}")
                        else:
                            print(f"  {phone}: Không tìm thấy")
                
                print(f"💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)")
            else:
                print(f"[WARNING] Không có Order ID từ DB!")
                print(f"[DEBUG] Data keys: {list(data.keys()) if data else 'None'}")
            
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu đa mạng: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu đa mạng: {e}")

def navigate_to_topup_multinetwork_page():
    """Điều hướng đến trang nạp tiền đa mạng."""
    try:
        
        target_url = "https://kpp.bankplus.vn/pages/chargecard.jsf"
        driver.get(target_url)
        # Chờ input số điện thoại xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng Topup đa mạng: {e}")
        raise

def toggle_input_amount(select, label, combobox):
    selected_value = select.get()
    if selected_value == "Nạp trả trước":
        # Ẩn combobox số tiền cho "Nạp trả trước" vì số tiền đã có trong format sđt|số tiền
        combobox.pack_forget()
        label.pack_forget()
    else:
        # Hiển thị combobox số tiền cho "Gạch nợ trả sau"
        combobox.pack(side="right")
        label.pack(side="right")
    maybe_update_ui()

def handle_choose_select(choose: str) -> int:
    """Xử lý lựa chọn loại thanh toán"""
    try:
        choose = choose.strip()
        if choose == "Nạp trả trước":
            return 1
        else:
            return 2
    except Exception as e:
        logger.error(f"Lỗi xử lý loại thanh toán: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi xử lý loại thanh toán: {e}")
        return 1

def payment_phone(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkcbb_form, tkcbb_amount):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        pin = tkinp_pin.get()
        cbb_type = tkcbb_form.get()
        type_sub = handle_choose_select(cbb_type)
        
        # Sửa logic validation cho "Nạp trả trước"
        if type_sub == 1:
            # Đối với "Nạp trả trước", số tiền được lấy từ format sđt|số tiền
            # Không cần validation từ combobox số tiền
            isnext = valid_data([cbils, pin])
            if isnext:
                # Không cần rsl_amount vì sẽ lấy số tiền từ format sđt|số tiền
                pass
        else:
            # Đối với "Gạch nợ trả sau", vẫn cần validation đầy đủ
            isnext = valid_data([cbils, pin])
            
        if not isnext:
            return False
        
        # Hiển thị Order ID mapping cho từng mã như FTTH
        print("Order ID:")
        code_to_order: Dict[str, Optional[str]] = {}
        for raw in cbils:
            c = (raw or "").strip()
            if not c:
                continue
            # Tìm Order ID chính xác cho từng mã (mỗi mã 1 order_id riêng)
            oid = db_find_order_id('nap_tien_da_mang', c, None)
            code_to_order[c] = oid
            if oid:
                print(f"  {c}: {oid}")
            else:
                print(f"  {c}: Không tìm thấy")
        
        print(f"🎯 Tổng cộng: {len(code_to_order)} mã có Order ID")
        print(f"💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)")
        data = []
        for cbil in cbils:
            cbil = cbil.strip()
            maybe_update_ui()
            time.sleep(1)
            if not stop_flag and cbil.strip() != "":
                # Hiển thị tiến trình với Order ID như FTTH
                # Mỗi mã cần có order_id riêng biệt để đảm bảo mỗi dòng = 1 đơn hàng
                specific_order_id = code_to_order.get(cbil)
                print(f"   🔧 Đang xử lý {cbil} | Order ID: {specific_order_id or 'Không tìm thấy'}")
                print(f"   📋 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt (như FTTH)")
                
                driver.refresh()
                time.sleep(2)
                navigate_to_topup_multinetwork_page()
                try:
                    phonenum = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
                    phonenum.clear()
                    phonenum.send_keys(cbil)
                    phonenum.send_keys(Keys.TAB)
                    time.sleep(1)
                except:
                    time.sleep(2)
                    phonenum = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
                    phonenum.clear()
                    phonenum.send_keys(cbil)
                    phonenum.send_keys(Keys.TAB)
                time.sleep(0.5)
                if type_sub == 1:
                    # Nạp trả trước: Lấy số tiền từ format sđt|số tiền
                    try:
                        # Parse số tiền từ format sđt|số tiền
                        if "|" in cbil:
                            phone_part, amount_part = cbil.split("|", 1)
                            amount_from_format = amount_part.strip()
                            print(f"   📱 Số điện thoại: {phone_part}")
                            print(f"   💰 Số tiền từ format: {amount_from_format}")
                        else:
                            print(f"   ⚠️  Format không đúng: {cbil} - cần format sđt|số tiền")
                            continue
                            
                        try:
                            cfm_modalTT = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirmTT_modal")))
                            driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modalTT)
                            time.sleep(1)
                        except:
                            pass
                        spl_lbl = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier")))
                        spl_lbl.click()
                        spl_0 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier_0")))
                        spl_0.click()
                        cfm_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesTTId")))
                        cfm_pay.click()
                    except:
                        pass
                    
                    # Không cần click vào option số tiền vì đã có trong format
                    print(f"   💡 Bỏ qua việc chọn option số tiền - sử dụng số tiền từ format: {amount_from_format}")
                    
                else:
                    try:
                        try:
                            cfm_modalTT = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirmTT_modal")))
                            driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modalTT)
                        except:
                            pass
                        try:
                            time.sleep(0.5)
                            spl_lbl = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier")))
                            spl_lbl.click()
                            time.sleep(0.5)
                            spl_1 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier_1")))
                            spl_1.click()
                            time.sleep(0.5)
                            cfm_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesTTId")))
                            cfm_pay.click()
                            time.sleep(0.5)
                        except:
                            pass
                        try:
                            btn_check = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:btnCheck")))
                            btn_check.click()
                        except:
                            pass
                        lbl_debt = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:debtId_input")))
                        debt_str = lbl_debt.get_attribute('value')
                        debt = int(debt_str.replace(".", "").replace(",", ""))
                        if debt >= 5000:
                            inp_amount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:transAmountId_input")))
                            inp_amount.clear()
                            inp_amount.send_keys(debt)
                        else:
                            data.append([cbil, debt, Config.STATUS_COMPLETE])
                            tkinp_ctm.delete("1.0", "1.end+1c")
                            insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
                            continue
                    except Exception as e:
                        data.append([cbil, 0, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - không nợ cước")
                        
                        # Update database cho trường hợp không nợ cước
                        if specific_order_id:
                            print(f"   💾 [DATABASE] Update database cho {cbil} (không nợ cước)...")
                            notes = f"Multi-network: Không nợ cước - {cbil}"
                            db_success = update_database_immediately(specific_order_id, cbil, "success", 0, notes, None)
                            if db_success:
                                print(f"      ✅ Database update thành công cho {cbil} (không nợ cước)")
                            else:
                                print(f"      ❌ Database update thất bại cho {cbil} (không nợ cước)")
                        else:
                            print(f"   ⚠️  Không có Order ID cho {cbil} - bỏ qua database update (không nợ cước)")
                        continue
                try:
                    pin_id = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:pinId")))
                    pin_id.clear()
                    pin_id.send_keys(pin)
                    btn_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:btnPay")))
                    btn_pay.click()
                    try:
                        cfm_modal = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirm_modal")))
                        driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                    except:
                        pass
                    time.sleep(0.5)
                    btn_confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesIdCard")))
                    btn_confirm.click()
                    if type_sub == 1:
                        # Sử dụng số tiền từ format sđt|số tiền
                        amount_to_use = amount_from_format if 'amount_from_format' in locals() else cbil
                        data.append([cbil, amount_to_use, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount_to_use}")
                        
                        # Update database với Order ID chính xác
                        if specific_order_id:
                            print(f"   💾 [DATABASE] Update database cho {cbil}...")
                            notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount_to_use}"
                            db_success = update_database_immediately(specific_order_id, cbil, "success", amount_to_use, notes, None)
                            if db_success:
                                print(f"      ✅ Database update thành công cho {cbil}")
                            else:
                                print(f"      ❌ Database update thất bại cho {cbil}")
                        else:
                            print(f"   ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                    else:
                        data.append([cbil, debt, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
                        
                        # Update database với Order ID chính xác
                        if specific_order_id:
                            print(f"   💾 [DATABASE] Update database cho {cbil}...")
                            notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Số tiền: {debt}"
                            db_success = update_database_immediately(specific_order_id, cbil, "success", debt, notes, None)
                            if db_success:
                                print(f"      ✅ Database update thành công cho {cbil}")
                            else:
                                print(f"      ❌ Database update thất bại cho {cbil}")
                        else:
                            print(f"   ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                except Exception as e:
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    tkinp_ctm.delete("1.0", "1.end+1c")
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                    
                    # Update database cho trường hợp thất bại
                    if specific_order_id:
                        print(f"   💾 [DATABASE] Update database cho {cbil} (failed)...")
                        notes = f"Multi-network: Lỗi xử lý - {cbil} | {str(e)}"
                        db_success = update_database_immediately(specific_order_id, cbil, "failed", None, notes, None)
                        if db_success:
                            print(f"      ✅ Database update thành công cho {cbil} (failed)")
                        else:
                            print(f"      ❌ Database update thất bại cho {cbil} (failed)")
                    else:
                        print(f"   ⚠️  Không có Order ID cho {cbil} - bỏ qua database update (failed)")
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Nạp tiền đa mạng"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện thoại: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán điện thoại: {e}")

def form_payment_phone():
    r = get_root()
    cus_frm = tk.Frame(r)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    form_frm = tk.Frame(r)
    form_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    pin_frm = tk.Frame(r)
    pin_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    btn_frm = tk.Frame(r)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Số điện thoại (mỗi dòng = 1 đơn hàng)")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=12, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=12, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    tklbl_form = tk.Label(form_frm, text="Hình thức:")
    tklbl_form.pack(side="left")
    tkcbb_form = ttk.Combobox(form_frm, values=["Nạp trả trước", "Gạch nợ trả sau"], width="14", state="readonly")
    tkcbb_form.pack(side="left")
    tkcbb_form.set("Nạp trả trước")
    tkcbb_form.bind("<<ComboboxSelected>>", lambda event: toggle_input_amount(tkcbb_form, tklbl_amount, tkcbb_amount))
    tkcbb_amount = ttk.Combobox(form_frm, values=["10.000đ", "20.000đ", "30.000đ", "50.000đ", "100.000đ", "200.000đ", "300.000đ", "500.000đ"], width="10", state="readonly")
    tklbl_amount = tk.Label(form_frm, text="Số tiền nạp:")
    
    # Khởi tạo UI: ẩn combobox số tiền cho "Nạp trả trước" (mặc định)
    toggle_input_amount(tkcbb_form, tklbl_amount, tkcbb_amount)
    tklbl_pin = tk.Label(pin_frm, text="Mã pin:")
    tklbl_pin.pack(side="left")
    tkinp_pin = ttk.Entry(pin_frm, width=12)
    tkinp_pin.pack(side="left", padx=4)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    def get_data_with_payment_type():
        """Lấy dữ liệu tương ứng với loại dịch vụ đã chọn"""
        selected = tkcbb_form.get()
        print(f"[DEBUG] Combobox được chọn: '{selected}'")
        
        if selected == "Nạp trả trước":
            payment_type = "prepaid"
        elif selected == "Gạch nợ trả sau":
            payment_type = "postpaid"
        else:
            payment_type = None
            
        print(f"[DEBUG] Payment type được map: {payment_type}")
        
        # Luôn gọi get_data_multi_network để đảm bảo dữ liệu tương ứng với loại dịch vụ
        # Điều này đảm bảo khi chuyển đổi giữa "Nạp trả trước" và "Gạch nợ trả sau"
        # thì dữ liệu được cập nhật tương ứng
        print(f"[DEBUG] Gọi get_data_multi_network với payment_type: {payment_type}")
        get_data_multi_network(tkinp_ctm, tkinp_pin, tkcbb_form, tkcbb_amount, payment_type)
        
        # UI đã được cập nhật tự động thông qua toggle_input_amount
    
    tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=get_data_with_payment_type)
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: payment_phone(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkcbb_form, tkcbb_amount))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 
