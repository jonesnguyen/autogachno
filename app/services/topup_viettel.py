"""Topup multi-network service module"""

import logging
from typing import List, Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox
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
stt_complete = "Đã xử lý"
stt_incomplete = "Chưa xử lý"

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

def get_data_viettel(text_widget, pin_widget):
    """Lấy dữ liệu API cho Nạp tiền đa mạng"""
    try:
        data = fetch_api_data("nap_tien_viettel")
        print("Nạp tiền Viettel:")
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
            map_texts = []
            for m in code_order_map:
                code_clean = (m.get("code") or "").strip()
                oid = m.get("orderId")
                map_texts.append(f"{code_clean}: {oid if oid else 'Không có'}")
    
            info_msg = f"Đã tải {len(codes)} mã thuê bao Postpaid\n"
            info_msg += "\n".join(map_texts)
    
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            pass  # Không có dữ liệu từ DB

    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu Postpaid: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu Postpaid: {e}")

def navigate_to_topup_multinetwork_page():
    """Điều hướng đến trang nạp tiền đa mạng."""
    try:
        
        target_url = "https://kpp.bankplus.vn/pages/chargecard.jsf"
        driver.get(target_url)
        driver.refresh()
        
        time.sleep(2)
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

def payment_viettel(tkinp_ctm, tkinp_ctmed, tkinp_pin):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        pin = tkinp_pin.get()

        if not valid_data([cbils, pin]):
            return False

        data_rows = []
        for raw in cbils:
            maybe_update_ui()
            time.sleep(1)
            raw = (raw or "").strip()
            if not raw:
                continue

            cbil, amount, order_id_val = raw.split("|")
            cbil = cbil.strip()
            amount = amount.strip()
            order_id_val = order_id_val.strip()
            rsl_amount = handle_choose_amount(amount)
            print(f"sdt: {cbil}, amount: {amount}, order_id: {order_id_val}")


            if not stop_flag and cbil.strip() != "":
                print(f"   🔧 Đang xử lý {cbil} | Order ID: {order_id_val or 'Không có'}")
                update_database_immediately(order_id_val, cbil, "processing", None, f"Đang xử lý {cbil}", None)
                navigate_to_topup_multinetwork_page()
                time.sleep(3)
                phonenum = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
                phonenum.clear()
                phonenum.send_keys(cbil)
                phonenum.send_keys(Keys.TAB)
                time.sleep(1)

                try:
                    cfm_modalTT = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirmTT_modal")))
                    driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modalTT)
                    time.sleep(1)
                    spl_lbl = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier")))
                    spl_lbl.click()
                    time.sleep(0.5)
                    spl_0 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier_0")))
                    spl_0.click()
                    time.sleep(0.5)
                    cfm_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesTTId")))
                    cfm_pay.click()
                except:
                    pass

                try:
                    inp_amount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:transAmountId_input")))
                    inp_amount.clear()
                    inp_amount.send_keys(amount)
                    time.sleep(0.5)
                    pin_id = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:pinId")))
                    pin_id.clear()
                    pin_id.send_keys(pin)
                    btn_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:btnPay")))
                    btn_pay.click()
                    time.sleep(0.5)
                    try:
                        cfm_modal = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirm_modal")))
                        driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                    except:
                        pass
                    time.sleep(0.5)
                    btn_confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesIdCard")))
                    btn_confirm.click()

                    time.sleep(2.5)
                    # Chờ alert xuất hiện
                    error_text = get_error_alert_text()
                    if error_text:
                        print(f"   ❌ Thanh toán thất bại (alert): {error_text}")
                        note_text = f"Nạp tiền đa mạng payment failed - {cbil} | {error_text}"
                        data_rows.append([cbil, 0, note_text])
                        data_rows.append([cbil, amount, stt_complete])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount} - Lỗi: {error_text}")       
                        if order_id_val:
                            update_database_immediately(order_id_val, cbil, "failed", None, note_text, None)
                        continue  # sang mã tiếp theo
                    
                    # Kiểm tra thông báo info
                    info_text = get_info_alert_text()
                    if info_text or ("không còn nợ cước" in info_text.lower()):
                        print(f"   ℹ️  Có thông báo info: {info_text}")
                        print(f"   ✅ Không còn nợ cước: Amount = 0")
                        
                        note_text = info_text.strip()
                        data_rows.append([cbil, amount, stt_complete])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount} | {note_text}")   
                        _ = update_database_immediately(order_id_val, cbil, "success", 0, note_text, None) 
                        continue
                    else:
                        data_rows.append([cbil, amount, stt_complete])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                        _ = update_database_immediately(order_id_val, cbil, "success", 0, None, None)    
                except:
                    data_rows.append([cbil, 0, stt_incomplete])
                    _ = update_database_immediately(order_id_val, cbil, "failed", None, None, None) 
                    tkinp_ctm.delete("1.0", "1.end+1c")
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")       

        time.sleep(2)
        if len(data_rows) > 0:
            name_dir = "Nạp tiền viettel"
            export_excel(data_rows, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện thoại: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán điện thoại: {e}")

def form_payment_viettel():
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
    button_frm = tk.Frame(r)
    button_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Số điện thoại")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=12, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=12, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    tklbl_pin = tk.Label(pin_frm, text="Mã pin:")
    tklbl_pin.pack(side="left")
    tkinp_pin = ttk.Entry(pin_frm, width=12)
    tkinp_pin.pack(side="left", padx=4)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    tkbtn_get_data = ttk.Button(button_frm, text="Get dữ liệu", command=lambda: get_data_viettel(tkinp_ctm, tkinp_pin))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(button_frm, text="Bắt đầu", command=lambda: payment_viettel(tkinp_ctm, tkinp_ctmed, tkinp_pin))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(button_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 
