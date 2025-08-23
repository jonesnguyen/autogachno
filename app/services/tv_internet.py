import logging
import re
import time
from typing import List, Optional, Dict, Any, Tuple

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import ttk, messagebox

from ..config import Config
from ..db import (
    update_database_immediately,
    db_find_order_id,
    db_fetch_service_data,
)
from ..utils.browser import driver, automation_lock, get_error_alert_text
from ..utils.ui_helpers import (
    populate_text_widget,
    populate_entry_widget,
    insert_ctmed,
    delete_ctmed,
    valid_data,
    maybe_update_ui,
    get_root,
    update_stop_flag,
)
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

# ==============================
# Helpers
# ==============================

def amount_by_cbil(cbil: str, element, lookup: bool = False) -> Tuple[bool, Any, Optional[str]]:
    """Phân tích HTML, tìm số tiền và id nút thanh toán (nếu lookup=True)."""
    try:
        amount = "Không tìm thấy mã thuê bao"
        payment_id = None
        html_content = element.get_attribute('outerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')
        pay_content_groups = soup.find_all("div", class_="row pay-content mb-3")
        for group in pay_content_groups:
            p_tags = group.find_all("p")
            is_found = any(cbil in p_tag.text for p_tag in p_tags)
            if lookup and is_found:
                button_tag = group.find("button", {"id": re.compile(r'payMoneyForm:btnView\d*')})
                if button_tag:
                    payment_id = button_tag['id']
            if is_found:
                for p_tag in p_tags:
                    if "VND" in p_tag.text:
                        str_price = p_tag.text.split("VND")[0].strip()
                        try:
                            amount = int(str_price.replace(",", "").replace(".", ""))
                        except Exception:
                            pass
                        if isinstance(amount, int) and amount >= 5000:
                            return True, amount, payment_id
                        else:
                            return False, amount, payment_id
        return False, amount, payment_id
    except Exception as e:
        logger.error(f"Lỗi lấy số tiền: {e}")
        return False, "Lỗi thanh toán", None


def navigate_to_tv_internet_page_and_select_radio():
	try:
		target_url = "https://kpp.bankplus.vn/pages/newInternetTelevisionViettel.jsf?serviceCode=000003&serviceType=INTERNET"
		driver.get(target_url)
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
		try:
			radio_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "payMoneyForm:console:3")))
			radio_box = radio_input.find_element(By.XPATH, "../../div[contains(@class,'ui-radiobutton-box')]")
			radio_box.click()
		except Exception:
			try:
				label = driver.find_element(By.XPATH, "//label[@for='payMoneyForm:console:3']")
				label.click()
			except Exception:
				pass
	except Exception as e:
		logger.warning(f"Không thể điều hướng FTTH hoặc chọn radio: {e}")
		raise


# ==============================
# Automation
# ==============================

def get_data_tv_internet(text_widget, pin_widget):
    """Lấy dữ liệu DB + điền PIN mặc định."""
    try:
        data = db_fetch_service_data("thanh_toan_tv_internet")
        print(data)
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

            # Dùng code_order_map thay vì chỉ lấy latest order_id
            code_order_map = data.get("code_order_map", [])
            map_texts = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId")
                map_texts.append(f"{code_clean}: {oid if oid else 'Không có'}")

            info_msg = f"Đã tải {len(codes)} mã thuê bao TV-Internet\n"
            info_msg += "\n".join(map_texts)

            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            pass  # Không có dữ liệu từ DB
    except Exception as e:
        logger.error(f"Lỗi get_data_tv_internet: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi get_data_tv_internet: {e}")

def payment_internet(tkinp_ctm, tkinp_ctmed, tkinp_pin: Optional[ttk.Entry] = None):
    """Thanh toán TV-Internet qua GUI."""
    try:
        delete_ctmed(tkinp_ctmed)
        from ..utils.ui_helpers import update_stop_flag
        update_stop_flag()

        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        pin = tkinp_pin.get() if tkinp_pin else None
        if not valid_data([cbils, pin]):
            return False

        data_rows = []
        for raw in cbils:
            maybe_update_ui()
            time.sleep(1)
            raw = (raw or "").strip()
            if not raw:
                continue

            # --- TÁCH CODE|ORDER_ID ---
            if "|" in raw:
                cbil, order_id_val = raw.split("|", 1)
                cbil = cbil.strip()
                order_id_val = order_id_val.strip()
            else:
                cbil = raw
                order_id_val = None

            try:
                print(f"   🔧 Đang xử lý {cbil} | Order ID: {order_id_val or 'Không có'}")
                
                navigate_to_tv_internet_page_and_select_radio()
                time.sleep(3)

                if order_id_val:
                    update_database_immediately(order_id_val, cbil, "processing", None, f"Đang xử lý {cbil}", None)

                # Điền mã thuê bao
                customer = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode"))
                )
                customer.clear()
                customer.send_keys(cbil)

                # Nhấn nút kiểm tra
                payment_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay0"))
                )
                payment_button.click()
                
                # Kiểm tra alert lỗi sau khi thanh toán
                time.sleep(2) 
                 # Chờ alert xuất hiện
                error_text = get_error_alert_text()
                if error_text:
                    print(f"   ❌ Thanh toán thất bại (alert): {error_text}")
                    note_text = f"TV-Internet payment failed - {cbil} | {error_text}"
                    data_rows.append([cbil, 0, note_text])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi: {error_text}")
                    if order_id_val:
                        update_database_immediately(order_id_val, cbil, "failed", None, note_text, None)
                    continue  # sang mã tiếp theo

                time.sleep(1)
                
                WebDriverWait(driver, 16).until(
                    EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal"))
                )

                # Lấy kết quả
                element41 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41"))
                )
                is_amount, amount, payment_id = amount_by_cbil(cbil, element41, True)

                if not is_amount:
                    note_text = f"TV-Internet payment failed - {cbil} | Amount: {amount}"
                    data_rows.append([cbil, amount, note_text])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                    if order_id_val:
                        update_database_immediately(order_id_val, cbil, "failed", None, note_text, None)
                    continue

                # Thực hiện thanh toán
                print(f"   💳 Nhấn nút thanh toán: {payment_id}")
                payment_btn1 = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, payment_id))
                )
                payment_btn1.click()

                print(f"   🔐 Điền mã PIN...")
                pin_id = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "payMoneyForm:pinId"))
                )
                pin_id.clear()
                pin_id.send_keys(pin)

                print(f"   ✅ Xác nhận thanh toán...")
                pay_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "payMoneyForm:btnPay"))
                )
                pay_btn.click()

                try:
                    print(f"   ⏳ Kiểm tra modal xác nhận...")
                    cfm_modal = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.ID, "payMoneyForm:dlgConfirm_modal"))
                    )
                    driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                except:
                    print(f"   ℹ️ Không tìm thấy modal xác nhận, tiếp tục...")

                print(f"   ✔️ Nhấn nút xác nhận cuối cùng...")
                confirm_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "payMoneyForm:yesId0"))
                )
                confirm_btn.click()

                # Kiểm tra alert lỗi sau khi thanh toán
                time.sleep(2)  # Chờ alert xuất hiện
                error_text = get_error_alert_text()
                if error_text:
                    print(f"   ❌ Thanh toán thất bại (alert): {error_text}")
                    note_text = f"TV-Internet payment failed - {cbil} | {error_text}"
                    data_rows.append([cbil, 0, note_text])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi: {error_text}")
                    if order_id_val:
                        update_database_immediately(order_id_val, cbil, "failed", None, note_text, None)
                    continue  # sang mã tiếp theo
                else:
                    # Không có alert => coi như thành công
                    note_text = f"TV-Internet payment ok - {cbil} | Amount: {amount}"
                    data_rows.append([cbil, amount, note_text])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                    if order_id_val:
                        update_database_immediately(order_id_val, cbil, "success", amount, note_text, None)

            except Exception as e:
                data_rows.append([cbil, 0, Config.STATUS_INCOMPLETE])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                if order_id_val:
                    update_database_immediately(order_id_val, cbil, "failed", None, str(e), None)

        time.sleep(1)
        if data_rows:
            export_excel(data_rows, "Thanh toán TV-Internet")

    except Exception as e:
        logger.error(f"Lỗi payment_internet: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi payment_internet: {e}")


def form_payment_internet():
    r = get_root()
    cus_frm = tk.Frame(r)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    phnum_frm = tk.Frame(r)
    phnum_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    btn_frm = tk.Frame(r)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")

    tk.Label(ctm_frm, text="Mã thuê bao").pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=16, width=24)
    tkinp_ctm.pack(side="left", pady=8)

    tk.Label(ctmed_frm, text="Đã xử lý").pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, height=16, width=32, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)

    tk.Label(phnum_frm, text="Mã pin:").pack(side="left")
    tkinp_pin = ttk.Entry(phnum_frm, width=22)
    tkinp_pin.pack(side="left", padx=4)

    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")

    ttk.Button(btn_frm, text="Get dữ liệu", command=lambda: get_data_tv_internet(tkinp_ctm, tkinp_pin)).pack(side="left", padx=5, pady=5)
    ttk.Button(btn_frm, text="Bắt đầu", style="Blue.TButton", command=lambda: payment_internet(tkinp_ctm, tkinp_ctmed, tkinp_pin)).pack(side="left", padx=5, pady=5)    
    ttk.Button(btn_frm, text="Dừng lại", command=lambda: update_stop_flag()).pack(side="right", padx=5, pady=5)


__all__ = [
    "process_payment_tv_internet_codes",
    "get_data_tv_internet",
    "payment_internet",
    "form_payment_internet",
]
