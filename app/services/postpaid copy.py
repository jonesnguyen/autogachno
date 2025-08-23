"""Postpaid lookup service module"""

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
from ..db import update_database_immediately, db_find_order_id
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

def process_postpaid_lookup_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý tra cứu trả sau không cần GUI, điều khiển selenium trực tiếp."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý Postpaid cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang Postpaid...")
            navigate_to_postpaid_lookup_page()
            print("   ✅ Đã điều hướng thành công đến trang Postpaid")
            
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
                            navigate_to_postpaid_lookup_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        get_root().update() if 'get_root' in globals() else None
                        time.sleep(0.5)
                        
                        print(f"   📝 Điền mã thuê bao: {cbil}")
                        customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
                        customer.clear()
                        customer.send_keys(cbil)
                        
                        print(f"   🔍 Nhấn nút KIỂM TRA...")
                        payment_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay0")))
                        payment_button.click()
                        time.sleep(1)
                        
                        print(f"   ⏳ Chờ modal loading...")
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        
                        print(f"   📊 Lấy thông tin kết quả...")
                        
                        # Kiểm tra thông báo lỗi trước
                        error_text = get_error_alert_text()
                        if error_text:
                            print(f"   ❌ Có thông báo lỗi: {error_text}")
                            if "Vui lòng nhập đầy đủ thông tin" in error_text:
                                print(f"   🔍 Lỗi validation: Thiếu thông tin bắt buộc")
                                print(f"   💡 Kiểm tra: Mã thuê bao '{cbil}' có hợp lệ không?")
                            
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": error_text})
                            
                            # Update database cho trường hợp thất bại
                            if order_id:
                                print(f"   💾 Update database cho trường hợp thất bại...")
                                db_success = update_database_immediately(order_id, cbil, "failed", None, f"Lỗi: {error_text}", None)
                                if not db_success:
                                    logger.warning(f"Database update thất bại cho {cbil}")
                            else:
                                print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                            
                            break
                        
                        # Kiểm tra thông báo info
                        info_text = get_info_alert_text()
                        if info_text:
                            print(f"   ℹ️  Có thông báo info: {info_text}")
                            if "không còn nợ cước" in info_text.lower():
                                print(f"   ✅ Không còn nợ cước: Amount = 0")
                                amount = 0
                                success = True
                                results.append({"code": cbil, "amount": amount, "status": "success", "message": info_text})
                                
                                # Update database cho trường hợp không nợ cước
                                if order_id:
                                    print(f"   💾 Update database cho trường hợp không nợ cước...")
                                    notes = f"Postpaid: Không nợ cước - {cbil} | {info_text}"
                                    db_success = update_database_immediately(order_id, cbil, "success", amount, notes, None)
                                    if not db_success:
                                        logger.warning(f"Database update thất bại cho {cbil}")
                                else:
                                    print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                                
                                print(f"   🎉 Hoàn thành xử lý mã {cbil}")
                                break
                        
                        # Thử lấy thông tin từ element
                        try:
                            element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                            _is_amount, amount, _pid = amount_by_cbil(cbil, element41, False)
                            
                            if _is_amount and amount > 0:
                                print(f"   ✅ Xử lý thành công: Amount = {amount:,}đ")
                                
                                # Thành công, thoát khỏi retry loop
                                success = True
                                results.append({"code": cbil, "amount": amount, "status": "success"})
                                
                                # Update database ngay lập tức cho từng đơn xử lý xong
                                if order_id:
                                    print(f"   💾 Bắt đầu update database...")
                                    notes = f"Postpaid: Có nợ cước - {cbil} | Số tiền: {amount:,}đ"
                                    db_success = update_database_immediately(order_id, cbil, "success", amount, notes, None)
                                    if not db_success:
                                        logger.warning(f"Database update thất bại cho {cbil}")
                                else:
                                    print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                                
                                print(f"   🎉 Hoàn thành xử lý mã {cbil}")
                                break
                            else:
                                print(f"   ⚠️  Không thể lấy thông tin số tiền từ element")
                                results.append({"code": cbil, "amount": None, "status": "failed", "message": "Không thể lấy thông tin số tiền"})
                        except Exception as element_error:
                            print(f"   ⚠️  Không thể tìm thấy element: {element_error}")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": f"Không thể tìm thấy element: {element_error}"})
                        
                        # Nếu đến đây mà chưa thành công, coi như thất bại
                        print(f"   ❌ Không thể xử lý mã {cbil} - không có kết quả rõ ràng")
                        results.append({"code": cbil, "amount": None, "status": "failed", "message": "Không có kết quả rõ ràng"})
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
                            logger.error(f"Postpaid code {cbil} thất bại sau 3 lần thử: {e}")
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
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý Postpaid:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            logger.info(f"Postpaid processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_postpaid_lookup_codes error: {e}")


def get_data_postpaid(text_widget):
    """Lấy dữ liệu API cho Tra cứu nợ thuê bao trả sau"""
    try:
        data = fetch_api_data("tra_cuu_no_tra_sau")
        if data and "phone_numbers" in data:
            populate_text_widget(text_widget, data["phone_numbers"])
            order_id = data.get("order_id")
            info_msg = f"Đã tải {len(data['phone_numbers'])} số điện thoại trả sau"
            if order_id:
                print(f"[INFO] Order ID từ DB: {order_id}", flush=True)
                logger.info(f"Order ID từ DB (Trả sau): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ API")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu trả sau: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu trả sau: {e}")


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
            #messagebox.showwarning(Config.TITLE, "Vui lòng nhập đầy đủ thông tin")
            return False
        
        # Kiểm tra dữ liệu đầu vào
        print(f"🔍 [VALIDATION] Kiểm tra dữ liệu đầu vào:")
        print(f"   📱 Số lượng mã: {len(cbils)}")
        for i, cbil in enumerate(cbils):
            if cbil.strip():
                print(f"   📋 Mã {i+1}: '{cbil.strip()}'")
            else:
                print(f"   ⚠️  Mã {i+1}: Rỗng (sẽ bỏ qua)")
        
        print(f"   💡 Strategy: Mỗi dòng = 1 đơn hàng riêng biệt")
        data = []
        for idx, cbil in enumerate(cbils, 1):
            cbil = cbil.strip()
            if not cbil:  # Bỏ qua dòng rỗng
                print(f"   ⏭️  Bỏ qua dòng {idx}: Rỗng")
                continue
                
            print(f"\n📱 [MÃ {idx}/{len(cbils)}] Xử lý mã: {cbil}")
            
            # Tìm Order ID riêng cho từng mã (như FTTH)
            order_id_val = db_find_order_id('tra_cuu_no_tra_sau', cbil, None)
            if order_id_val:
                print(f"   📋 Order ID riêng: {order_id_val}")
            else:
                print(f"   ⚠️  Không tìm thấy Order ID cho {cbil}")
            
            get_root().update()
            time.sleep(1)
            if not stop_flag:
                # Điều hướng đến trang tra cứu trả sau trước khi xử lý
                navigate_to_postpaid_lookup_page()
                time.sleep(2)
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
                    error_text = get_error_alert_text()
                    if error_text:
                        print(f"   ❌ Có thông báo lỗi: {error_text}")
                        if "Vui lòng nhập đầy đủ thông tin" in error_text:
                            print(f"   🔍 Lỗi validation: Thiếu thông tin bắt buộc")
                            print(f"   💡 Kiểm tra: Mã thuê bao '{cbil}' có hợp lệ không?")
                        
                        note_text = error_text.strip()
                        data.append([cbil, "Lỗi", Config.STATUS_INCOMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi | {note_text}")
                        
                        # Cập nhật DB failed với notes
                        if order_id_val:
                            try:
                                notes_db = f"Postpaid: Lỗi - {cbil} | {note_text}"
                                _ = update_database_immediately(order_id_val, cbil, "failed", None, notes_db, None)
                                print(f"      ✅ Database update thành công cho {cbil} (failed)")
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (Postpaid failed) cho {cbil}: {_e}")
                        else:
                            print(f"      ⚠️  Không có Order ID cho {cbil} - bỏ qua database update")
                        
                        continue
                    
                    # Kiểm tra thông báo info
                    info_text = get_info_alert_text()
                    if info_text and ("không còn nợ cước" in info_text.lower()):
                        print(f"   ℹ️  Có thông báo info: {info_text}")
                        print(f"   ✅ Không còn nợ cước: Amount = 0")
                        
                        note_text = info_text.strip()
                        data.append([cbil, 0, Config.STATUS_COMPLETE])
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
                        data.append([cbil, debt, Config.STATUS_COMPLETE])
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
                        data.append([cbil, "Lỗi", Config.STATUS_INCOMPLETE])
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
                    
                    data.append([cbil, "Lỗi xử lý", Config.STATUS_INCOMPLETE])
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
        if len(data) > 0:
            name_dir = "Tra cứu nợ trả sau"
            export_excel(data, name_dir)
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

