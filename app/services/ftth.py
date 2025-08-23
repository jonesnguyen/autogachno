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
	db_check_pending_orders_for_code,
	db_fetch_service_data,
)
# FIXED: Import ensure_driver_and_login instead of just driver
from ..utils.browser import ensure_driver_and_login, automation_lock, get_error_alert_text
from ..utils.ui_helpers import (
	populate_text_widget,
	populate_entry_widget,
	insert_ctmed,
	delete_ctmed,
	valid_data,
	maybe_update_ui,
	get_root,
)
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

def get_driver():
	"""Get the current driver instance, ensuring it's initialized"""
	try:
		from ..utils.browser import driver
		if driver is None:
			logger.info("Driver is None, ensuring initialization...")
			ensure_driver_and_login()
			from ..utils.browser import driver
		return driver
	except Exception as e:
		logger.error(f"Error getting driver: {e}")
		ensure_driver_and_login()
		from ..utils.browser import driver
		return driver

def amount_by_cbil(cbil: str, element, lookup: bool = False) -> Tuple[bool, Any, Optional[str]]:
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
						amount = int(str_price.replace(",", ""))
						if amount >= 5000:
							return True, amount, payment_id
						else:
							return False, amount, payment_id
		return False, amount, payment_id
	except Exception as e:
		logger.error(f"Lỗi lấy số tiền: {e}")
		return False, "Lỗi thanh toán", None

def navigate_to_ftth_page_and_select_radio():
	try:
		# FIXED: Get driver instance properly
		driver = get_driver()
		if driver is None:
			raise Exception("Cannot initialize driver")
			
		target_url = "https://kpp.bankplus.vn/pages/newInternetTelevisionViettel.jsf?serviceCode=000003&serviceType=INTERNET"
		logger.info(f"Navigating to: {target_url}")
		driver.get(target_url)
		time.sleep(2)
		WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
		time.sleep(2)
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


def extract_ftth_details_from_page() -> Dict[str, Any]:
	details: Dict[str, Any] = {}
	try:
		# FIXED: Get driver instance properly
		driver = get_driver()
		if driver is None:
			logger.error("Driver is None in extract_ftth_details_from_page")
			return details
			
		html_content = driver.page_source
		soup = BeautifulSoup(html_content, 'html.parser')
		label_to_key = {
			'Mã hợp đồng:': 'contract_code',
			'Chủ hợp đồng:': 'contract_owner',
			'Số thuê bao đại diện:': 'representative_subscriber',
			'Dịch vụ:': 'service',
			'Số điện thoại liên hệ:': 'contact_phone',
			'Nợ cước:': 'debt_amount',
		}
		for row in soup.find_all('div', class_='row'):
			cols = row.find_all('div', class_='col-6')
			if len(cols) != 2:
				continue
			label_tag = cols[0].find('label')
			value_p = cols[1].find('p')
			if not label_tag or not value_p:
				continue
			label_text = label_tag.get_text(strip=True)
			value_text = value_p.get_text(strip=True)
			key = label_to_key.get(label_text)
			if not key:
				continue
			if key == 'debt_amount':
				try:
					import re as _re
					num_str = _re.findall(r"[\d\.,]+", value_text)
					if num_str:
						details[key] = int(num_str[0].replace('.', '').replace(',', ''))
					else:
						details[key] = None
				except Exception:
					details[key] = None
			else:
				details[key] = value_text
	except Exception as e:
		logger.warning(f"Lỗi trích chi tiết FTTH: {e}")
	return details

def get_data_ftth(text_widget, order_entry: Optional[ttk.Entry] = None):
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
    
            # Dùng code_order_map thay vì chỉ lấy latest order_id
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
        logger.error(f"Lỗi lấy dữ liệu FTTH: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu FTTH: {e}")

def lookup_ftth(tkinp_ctm, tkinp_ctmed, tkinp_order: Optional[ttk.Entry] = None):
    try:
        # FIXED: Ensure driver is available before starting
        driver = get_driver()
        if driver is None:
            logger.error("Cannot get driver instance")
            return False
            
        delete_ctmed(tkinp_ctmed)
        from ..utils.ui_helpers import update_stop_flag
        update_stop_flag()

        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
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
                navigate_to_ftth_page_and_select_radio()
                time.sleep(3)
                update_database_immediately(order_id_val, cbil, "processing", None, f"Đang xử lý {cbil}", None)

                # FIXED: Use the driver we got earlier
                customer = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode"))
                )
                customer.clear()
                customer.send_keys(cbil)

                payment_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay0"))
                )
                payment_button.click()
                time.sleep(1)

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

                WebDriverWait(driver, 16).until(
                    EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal"))
                )
                element41 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41"))
                )
                is_amount, amount, payment_id = amount_by_cbil(cbil, element41, False)
                details = extract_ftth_details_from_page()
                note_text = (
                    f"HD:{details.get('contract_code','')} | "
                    f"Chu:{details.get('contract_owner','')} | "
                    f"SDT:{details.get('contact_phone','')} | "
                    f"No:{details.get('debt_amount','')}"
                )
                data_rows.append([cbil, amount, note_text])
                insert_ctmed(tkinp_ctmed, f"{cbil} - {amount} | {note_text}")
                _ = update_database_immediately(order_id_val, cbil, "success", amount, note_text, details)

            except Exception as e:
                logger.error(f"Error processing {cbil}: {e}")
                data_rows.append([cbil, 0, Config.STATUS_INCOMPLETE])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")

        time.sleep(1)
        if data_rows:
            export_excel(data_rows, "Tra cứu FTTH")

    except Exception as e:
        logger.error(f"Lỗi tra cứu FTTH: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi tra cứu FTTH: {e}")


def form_lookup_ftth():
	r = get_root()
	cus_frm = tk.Frame(r)
	cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
	ctm_frm = tk.Frame(cus_frm)
	ctm_frm.pack(expand=True, side="left")
	ctmed_frm = tk.Frame(cus_frm)
	ctmed_frm.pack(expand=True, side="right")
	btn_frm = tk.Frame(r)
	btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
	tklbl_ctm = tk.Label(ctm_frm, text="Số thuê bao (mỗi dòng tạo 1 order)")
	tklbl_ctm.pack(side="top")
	tkinp_ctm = tk.Text(ctm_frm, height=16, width=24)
	tkinp_ctm.pack(side="left", pady=8)
	tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
	tklbl_ctm.pack(side="top")
	tkinp_ctmed = tk.Text(ctmed_frm, height=16, width=32, bg="#ccc", state="disabled")
	tkinp_ctmed.pack(side="left", pady=8)
	style = ttk.Style()
	style.configure("Red.TButton", foreground="red")
	style.configure("Blue.TButton", foreground="blue")
	style.configure("Green.TButton", foreground="green")
	tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=lambda: get_data_ftth(tkinp_ctm, None))
	tkbtn_get_data.pack(side='left', padx=5, pady=5)
	tkbtn_get_data.configure(style="Green.TButton")
	tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: lookup_ftth(tkinp_ctm, tkinp_ctmed, None))
	tkbtn_payment.pack(side='left', padx=5, pady=5)
	tkbtn_payment.configure(style="Blue.TButton") 
	from ..utils.ui_helpers import stop_tool
	tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
	tkbtn_destroy.pack(side='right', padx=5, pady=5)
	tkbtn_destroy.configure(style="Red.TButton") 

__all__ = [
	"process_lookup_ftth_codes",
	"get_data_ftth",
	"lookup_ftth",
	"navigate_to_ftth_page_and_select_radio",
	"extract_ftth_details_from_page",
	"amount_by_cbil",
	"form_lookup_ftth",
]