# Viettel topup service module

import logging
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, #messagebox
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ..config import Config
from ..db import update_database_immediately
from ..utils.browser import driver, ensure_driver_and_login, automation_lock
from ..utils.ui_helpers import (
    populate_text_widget,
    populate_entry_widget,
    insert_ctmed,
    delete_ctmed,
    valid_data,
    stop_flag,
    get_root,
    maybe_update_ui,
    stop_tool,
    update_stop_flag,
)
from ..utils.api_client import fetch_api_data
from ..utils.excel_export import export_excel

logger = logging.getLogger(__name__)

def process_topup_viettel_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý nạp tiền Viettel không cần GUI, điều khiển selenium trực tiếp."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý Topup Viettel cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang Topup Viettel...")
            navigate_to_topup_viettel_page()
            print("   ✅ Đã điều hướng thành công đến trang Topup Viettel")
            
            results = []
            for idx, cbil in enumerate(codes, 1):
                print(f"\n📱 [MÃ {idx}/{len(codes)}] Xử lý mã: {cbil}")
                success = False
                for attempt in range(3):  # Retry tối đa 3 lần
                    try:
                        cbil = (cbil or "").strip()
                        if not cbil:
                            print(f"   ⚠️  Mã rỗng, bỏ qua")
                            break
                        
                        if attempt > 0:
                            print(f"   🔄 Retry lần {attempt + 1}/3 cho mã {cbil}")
                            logger.info(f"Retry lần {attempt + 1} cho mã {cbil}")
                            driver.refresh()
                            time.sleep(2)
                            navigate_to_topup_viettel_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        maybe_update_ui()
                        time.sleep(0.5)
                        
                        print(f"   📝 Điền số điện thoại: {cbil}")
                        phone_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:phoneNumber")))
                        phone_input.clear()
                        phone_input.send_keys(cbil)
                        
                        print(f"   🔍 Nhấn nút TIẾP TỤC...")
                        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "payMoneyForm:btnContinue")))
                        continue_button.click()
                        time.sleep(1)
                        
                        print(f"   ⏳ Chờ modal loading...")
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        
                        print(f"   ✅ Xử lý thành công cho số điện thoại {cbil}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": None, "status": "success"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            db_success = update_database_immediately(order_id, cbil, "success", None, "Topup Viettel ok", None)
                            if not db_success:
                                logger.warning(f"Database update thất bại cho {cbil}")
                        else:
                            print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                        
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
                            logger.error(f"Topup Viettel code {cbil} thất bại sau 3 lần thử: {e}")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": str(e)})
                            
                            # Update database cho trường hợp thất bại
                            if order_id:
                                print(f"   💾 Update database cho trường hợp thất bại...")
                                db_success = update_database_immediately(order_id, cbil, "failed", None, str(e), None)
                                if not db_success:
                                    logger.warning(f"Database update thất bại cho {cbil}")
                            else:
                                print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                
                if not success:
                    print(f"   💥 Mã {cbil} không thể xử lý sau 3 lần thử")
                    logger.error(f"Mã {cbil} không thể xử lý sau 3 lần thử")
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý Topup Viettel:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            logger.info(f"Topup Viettel processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_topup_viettel_codes error: {e}")

def get_data_viettel(text_widget, pin_widget, amount_widget):
    """Lấy dữ liệu API cho Nạp tiền mạng Viettel"""
    try:
        data = fetch_api_data("nap_tien_viettel")
        if data:
            if "phone_numbers" in data:
                populate_text_widget(text_widget, data["phone_numbers"])
            # Tự động điền mã PIN từ config
            print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            if "amount" in data:
                populate_entry_widget(amount_widget, data["amount"])
            
            count = len(data.get("phone_numbers", []))
            order_id = data.get("order_id")
            info_msg = f"Đã tải {count} số điện thoại Viettel"
            if order_id:
                print(f"[INFO] Order ID từ DB: {order_id}", flush=True)
                logger.info(f"Order ID từ DB (Viettel): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu Viettel: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu Viettel: {e}")

def navigate_to_topup_viettel_page():
    """Điều hướng đến trang nạp tiền Viettel."""
    try:
        
        target_url = "https://kpp.bankplus.vn/pages/chargecard.jsf"
        driver.get(target_url)
        # Chờ input số điện thoại xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:phoneNumber")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng Topup Viettel: {e}")
        raise


def payment_viettel(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkinp_amount):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        pin = tkinp_pin.get()
        amount = tkinp_amount.get()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils, pin, amount]):
            return False
        data = []
        for cbil in cbils:
            get_root().update()
            time.sleep(0.5)
            cbil = cbil.strip()
            if not stop_flag and cbil.strip() != "":
                time.sleep(0.5)
                try:
                    phonenum = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
                    phonenum.clear()
                    phonenum.send_keys(cbil)
                    phonenum.send_keys(Keys.TAB)
                    time.sleep(0.5)
                except:
                    time.sleep(2)
                    phonenum = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
                    phonenum.clear()
                    phonenum.send_keys(cbil)
                    phonenum.send_keys(Keys.TAB)
                try:
                    cfm_modalTT = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirmTT_modal")))
                    driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modalTT)
                    time.sleep(0.5)
                    spl_lbl = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, "indexForm:supplier")))
                    spl_lbl.click()
                    time.sleep(0.5)
                    spl_0 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier_0")))
                    spl_0.click()
                    time.sleep(0.5)
                    cfm_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesTTId")))
                    cfm_pay.click()
                    time.sleep(0.5)
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
                    time.sleep(0.5)
                    btn_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:btnPay")))
                    btn_pay.click()
                    time.sleep(0.5)
                    try:
                        cfm_modal = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirm_modal")))
                        driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                    except:
                        pass
                    btn_confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesIdCard")))
                    btn_confirm.click()
                    data.append([cbil, amount, Config.STATUS_COMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                    tkinp_ctm.delete("1.0", "1.end+1c")
                except:
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - null")
                    tkinp_ctm.delete("1.0", "1.end+1c")
                    continue
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Nạp tiền mạng Viettel"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán Viettel: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán Viettel: {e}")

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
    tkinp_amount = tk.Entry(pin_frm, width=12)
    tkinp_amount.pack(side="right", padx=4)
    tklbl_amount = tk.Label(pin_frm, text="Số tiền nạp:")
    tklbl_amount.pack(side="right")
    tklbl_pin = tk.Label(pin_frm, text="Mã pin:")
    tklbl_pin.pack(side="left")
    tkinp_pin = ttk.Entry(pin_frm, width=12)
    tkinp_pin.pack(side="left", padx=4)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    tkbtn_get_data = ttk.Button(button_frm, text="Get dữ liệu", command=lambda: get_data_viettel(tkinp_ctm, tkinp_pin, tkinp_amount))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(button_frm, text="Bắt đầu", command=lambda: payment_viettel(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkinp_amount))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(button_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 
