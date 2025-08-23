import logging
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..config import Config
from ..db import update_database_immediately, db_find_order_id
from ..utils.browser import driver, ensure_driver_and_login, automation_lock, get_error_alert_text
from ..utils.ui_helpers import (
    populate_text_widget,
    populate_entry_widget,
    delete_ctmed,
    insert_ctmed,
    valid_data,
    get_root,
    update_stop_flag,
    stop_tool,
)
from ..utils.api_client import fetch_api_data
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

def navigate_to_evn_page():
    try:
        target_url = "https://kpp.bankplus.vn/pages/collectElectricBill.jsf?serviceCode=EVN"
        driver.get(target_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "collectElectricBillForm:j_idt29")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng EVN: {e}")
        raise

def get_data_evn(text_widget, phone_widget, pin_widget):
    try:
        data = fetch_api_data("gach_dien_evn")
        if data:
            if "bill_codes" in data:
                populate_text_widget(text_widget, data["bill_codes"])
            if "receiver_phone" in data:
                populate_entry_widget(phone_widget, data["receiver_phone"])
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            count = len(data.get("bill_codes", []))
            order_id = data.get("order_id")
            info_msg = f"Đã tải {count} mã hóa đơn điện EVN"
            if order_id:
                logger.info(f"Order ID từ DB (EVN): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            pass  # Không có dữ liệu từ DB
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu EVN: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu EVN: {e}")

def debt_electric(tkinp_ctm, tkinp_ctmed, tkinp_phone, tkinp_pin):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        data = []
        for cbil in cbils:
            cbil = cbil.strip()
            if not cbil:
                continue
            try:
                customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:billCodeId")))
                customer.clear()
                customer.send_keys(cbil)
                time.sleep(0.5)
                payment = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay")))
                payment.click()
                time.sleep(1)
                WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                alert_text = get_error_alert_text()
                if alert_text and ("không" in alert_text.lower() or "đã xảy ra lỗi" in alert_text.lower()):
                    note_err = alert_text.strip()
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi | {note_err}")
                    order_id_val = db_find_order_id('gach_dien_evn', cbil.strip(), None)
                    if order_id_val:
                        _ = update_database_immediately(order_id_val, cbil, "failed", None, note_err, None)
                    continue
                lblamount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt49")))
                try:
                    text_of_amount = lblamount.text
                    amount_str = text_of_amount.replace('VND', '').replace('.', '')
                    amount = int(amount_str)
                except:
                    amount = lblamount.text
                time.sleep(0.5)
                confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:yesIdEVN")))
                confirm.click()
                data.append([cbil, amount, Config.STATUS_COMPLETE])
                insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                order_id_val = db_find_order_id('gach_dien_evn', cbil.strip(), None)
                if order_id_val:
                    _ = update_database_immediately(order_id_val, cbil, "success", amount, "EVN payment ok", None)
                continue
            except Exception:
                data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                continue
        time.sleep(1)
        if data:
            export_excel(data, "Thanh toán điện EVN")
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện EVN: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán điện EVN: {e}")

def form_debt_electric():
    r = get_root()
    cus_frm = tk.Frame(r)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    btn_frm = tk.Frame(r)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Mã thuê bao")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=18, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=18, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    tkinp_phone = ttk.Entry(r)
    tkinp_pin = ttk.Entry(r)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=lambda: get_data_evn(tkinp_ctm, tkinp_phone, tkinp_pin))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: debt_electric(tkinp_ctm, tkinp_ctmed, tkinp_phone, tkinp_pin))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 

__all__ = [
    "process_evn_payment_codes",
    "get_data_evn",
    "debt_electric",
    "navigate_to_evn_page",
    "form_debt_electric",
]


