"""Postpaid lookup service module"""

import logging
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, messagebox
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ..config import Config
from ..db import (
    update_database_immediately,
    db_find_order_id,
    db_fetch_service_data,
)
from ..utils.browser import driver, ensure_driver_and_login, automation_lock, get_info_alert_text, get_error_alert_text
from ..utils.ui_helpers import (
    populate_text_widget,
    insert_ctmed,
    delete_ctmed,
    valid_data,
    stop_flag,
    get_root,
    update_stop_flag,
    stop_tool,
)
from ..utils.excel_export import export_excel
from ..utils.api_client import fetch_api_data

# Import amount_by_cbil function
try:
    from ..utils.ui_helpers import amount_by_cbil
except ImportError:
    # Fallback nếu không import được
    def amount_by_cbil(cbil, element, lookup=False):
        try:
            amount_text = element.text.strip()
            if amount_text and amount_text.replace(".", "").replace(",", "").isdigit():
                amount = int(amount_text.replace(".", "").replace(",", ""))
                return True, amount, None
            return False, 0, None
        except:
            return False, 0, None

logger = logging.getLogger(__name__)


def get_data_postpaid(text_widget):
    """Lấy dữ liệu API cho Tra cứu nợ thuê bao trả sau"""
    try:
        data = db_fetch_service_data("tra_cuu_no_tra_sau")
        print("Tra cứu nợ trả sau:")
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



def navigate_to_postpaid_lookup_page():
    """Điều hướng đến trang tra cứu trả sau."""
    try:
        target_url = "https://kpp.bankplus.vn/pages/chargecard.jsf"
        driver.get(target_url)
        # Chờ input mã thuê bao xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng Postpaid: {e}")
        raise


def lookup_card(tkinp_ctm, tkinp_ctmed):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False

        data_rows = []
        for raw in cbils:
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
            
            get_root().update()
            time.sleep(1)
            if not stop_flag:
                # Điều hướng đến trang tra cứu trả sau trước khi xử lý
                print(f"   🔧 Đang xử lý {cbil} | Order ID: {order_id_val or 'Không có'}")
                navigate_to_postpaid_lookup_page()
                time.sleep(2)
                update_database_immediately(order_id_val, cbil, "processing", None, f"Đang xử lý {cbil}", None)

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

                    # Chờ modal/tiến trình, rồi kiểm tra thông báo
                    time.sleep(1)
                    
                    # Kiểm tra thông báo lỗi trước
                    # Chờ alert xuất hiện
                    error_text = get_error_alert_text()
                    if error_text:
                        print(f"   ❌ Thanh toán thất bại (alert): {error_text}")
                        note_text = f"Postpaid payment failed - {cbil} | {error_text}"
                        data_rows.append([cbil, 0, note_text])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi: {error_text}")
                        if order_id_val:
                            update_database_immediately(order_id_val, cbil, "failed", None, note_text, None)
                        continue  # sang mã tiếp theo
                    
                    # Kiểm tra thông báo info
                    info_text = get_info_alert_text()
                    if info_text and ("không còn nợ cước" in info_text.lower()):
                        print(f"   ℹ️  Có thông báo info: {info_text}")
                        print(f"   ✅ Không còn nợ cước: Amount = 0")
                        
                        note_text = info_text.strip()
                        data_rows.append([cbil, 0, Config.STATUS_COMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - 0 | {note_text}")
                        
                        # Cập nhật DB success với amount=0 và notes
                        if order_id_val:
                            try:
                                notes_db = f"Postpaid: Không nợ cước - {cbil} | {note_text}"
                                _ = update_database_immediately(order_id_val, cbil, "success", 0, notes_db, None)
                                print(f"      ✅ Database update thành công cho {cbil} (không nợ cước)")
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (Postpaid no debt) cho {cbil}: {_e}")
                        else:
                            print(f"      ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                        
                        continue

                    # Lấy giá trị nợ cước nếu có
                    try:
                        lbl_debt = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:debtId_input")))
                        debt_str = lbl_debt.get_attribute('value')
                        debt = int(debt_str.replace(".", "").replace(",", ""))
                        
                        print(f"   💰 Có nợ cước: {debt:,}đ")
                        data_rows.append([cbil, debt, Config.STATUS_COMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {debt:,}đ")
                        
                        # Cập nhật DB success với amount=debt
                        if order_id_val:
                            try:
                                notes_db = f"Postpaid: Có nợ cước - {cbil} | Số tiền: {debt:,}đ"
                                _ = update_database_immediately(order_id_val, cbil, "success", debt, notes_db, None)
                                print(f"      ✅ Database update thành công cho {cbil} (có nợ cước)")
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (Postpaid debt) cho {cbil}: {_e}")
                        else:
                            print(f"      ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                        
                        continue
                    except Exception as debt_error:
                        print(f"   ⚠️  Không thể lấy thông tin nợ cước: {debt_error}")
                        data_rows.append([cbil, "Lỗi", Config.STATUS_INCOMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi | Không thể lấy nợ cước")
                        
                        # Cập nhật DB failed
                        if order_id_val:
                            try:
                                notes_db = f"Postpaid: Lỗi lấy nợ cước - {cbil} | {str(debt_error)}"
                                _ = update_database_immediately(order_id_val, cbil, "failed", None, notes_db, None)
                                print(f"      ✅ Database update thành công cho {cbil} (failed)")
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (Postpaid failed) cho {cbil}: {_e}")
                        else:
                            print(f"      ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                        
                        continue
                except Exception as general_error:
                    print(f"   ❌ Lỗi xử lý chung: {general_error}")
                    
                    # Nếu có thông báo info/alert khác thì lưu notes giống hiển thị
                    note_text = get_info_alert_text() or get_error_alert_text() or ""
                    if note_text:
                        print(f"   ℹ️  Thông báo hệ thống: {note_text}")
                    
                    data_rows.append([cbil, "Lỗi xử lý", Config.STATUS_INCOMPLETE])
                    display_line = f"{cbil} - Lỗi xử lý{(' | ' + note_text) if note_text else ''}"
                    insert_ctmed(tkinp_ctmed, display_line)
                    
                    # Cập nhật DB failed với notes giống hiển thị
                    if order_id_val:
                        try:
                            notes_db = f"Postpaid: Lỗi xử lý - {cbil} | {str(general_error)}{(' | ' + note_text) if note_text else ''}"
                            _ = update_database_immediately(order_id_val, cbil, "failed", None, notes_db, None)
                            print(f"      ✅ Database update thành công cho {cbil} (failed)")
                        except Exception as _e:
                            logger.warning(f"DB update lỗi (Postpaid failed) cho {cbil}: {_e}")
                    else:
                        print(f"      ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                    
                    continue
        time.sleep(2)
        if len(data_rows) > 0:
            name_dir = "Tra cứu nợ trả sau"
            export_excel(data_rows, name_dir)
    except Exception as e:
        logger.error(f"Lỗi tra cứu nợ trả sau: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi tra cứu nợ trả sau: {e}")

def form_lookup_card():
    cus_frm = tk.Frame(get_root())
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    button_frm = tk.Frame(get_root())
    button_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="SĐT tra cứu")
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
    tkbtn_get_data = ttk.Button(button_frm, text="Get dữ liệu", command=lambda: get_data_postpaid(tkinp_ctm))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(button_frm, text="Bắt đầu", command=lambda: lookup_card(tkinp_ctm, tkinp_ctmed))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(button_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 

