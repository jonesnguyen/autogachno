import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time
import threading

import sys
# Ensure parent directory is on sys.path so we can import the package `app` when running directly
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
	sys.path.insert(0, PARENT_DIR)

from app.config import Config, LOGIN_USERNAME
from app.utils.browser import driver, initialize_browser, cleanup, login_process, ensure_driver_and_login
from app.utils.ui_helpers import show_services_form, set_root, get_root, maybe_update_ui

# Cấu hình logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler('app.log', encoding='utf-8'),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

# Global variables
root = None
auto_mode_enabled = False
auto_mode_thread = None
auto_mode_stop_flag = False
auto_mode_loop_enabled = False  # Thêm biến cho chế độ lặp
auto_mode_loop_interval = 10  # Khoảng thời gian lặp lại (giây)
ui_initialized = False

def initialize_main_ui():
	"""Khởi tạo UI chính một lần duy nhất"""
	global root, ui_initialized
	
	if ui_initialized and root:
		return root
		
	if root is None:
		root = tk.Tk()
		root.title("HPK Tool - Viettel Pay Automation")
		root.geometry("500x550") 
		root.option_add("*Font", "Arial 10")
		try:
			root.iconbitmap(Config.ICON_FILE)
		except Exception as e:
			logger.warning(f"Không thể tải icon: {e}")
			pass
		set_root(root)
	
	# Chỉ hiển thị form dịch vụ một lần
	if not ui_initialized:
		show_services_form()
		create_auto_mode_controls()
		ui_initialized = True
	
	return root

def find_widget_by_text(parent, widget_type, text_pattern, max_depth=5, current_depth=0):
	"""Tìm widget theo text pattern với exact match để tránh nhầm với auto buttons"""
	if current_depth > max_depth:
		return None
	try:
		for widget in parent.winfo_children():
			if isinstance(widget, widget_type):
				if hasattr(widget, 'cget') and widget.cget('text') == text_pattern:
					return widget
			# Recursively search in child widgets
			result = find_widget_by_text(widget, widget_type, text_pattern, max_depth, current_depth + 1)
			if result:
				return result
	except Exception:
		pass
	return None

def find_combobox_by_values(parent, value_pattern, max_depth=5, current_depth=0):
	"""Tìm combobox chứa value pattern với giới hạn độ sâu"""
	if current_depth > max_depth:
		return None
	try:
		for widget in parent.winfo_children():
			if isinstance(widget, tk.ttk.Combobox):
				if hasattr(widget, 'cget') and value_pattern in str(widget.cget('values')):
					return widget
			# Recursively search in child widgets
			result = find_combobox_by_values(widget, value_pattern, max_depth, current_depth + 1)
			if result:
				return result
	except Exception:
		pass
	return None

def wait_for_widget(parent, finder_func, finder_args, timeout=20, poll_interval=0.5):
	"""Chờ widget xuất hiện với timeout"""
	start_time = time.time()
	while time.time() - start_time < timeout:
		widget = finder_func(parent, *finder_args)
		if widget:
			return widget
		maybe_update_ui()
		time.sleep(poll_interval)
	return None

def reset_service_form():
	"""Reset form dịch vụ về trạng thái ban đầu"""
	try:
		r = get_root()
		
		# Tìm và reset combobox dịch vụ
		service_combobox = find_combobox_by_values(r, "Tra cứu FTTH")
		if service_combobox:
			service_combobox.set("")  # Clear selection
			maybe_update_ui()
			
		# Tìm và clear các text widgets
		for widget in r.winfo_children():
			if isinstance(widget, tk.Frame):
				for child in widget.winfo_children():
					if isinstance(child, tk.Frame):
						for subchild in child.winfo_children():
							if isinstance(subchild, tk.Text):
								try:
									subchild.delete("1.0", "end")
								except:
									pass
		
		logger.info("🔄 Đã reset form dịch vụ")
		maybe_update_ui()
		
	except Exception as e:
		logger.error(f"Lỗi reset service form: {e}")

def auto_process_service(service_name, service_type=None):
    """Tự động xử lý một dịch vụ cụ thể với retry và timeout - Phiên bản tối ưu"""
    global auto_mode_stop_flag
    
    # Hiển thị tên dịch vụ với loại cụ thể
    service_display_name = service_name
    if service_type:
        type_suffix = " - Nạp trả trước" if service_type == "prepaid" else " - Gạch nợ trả sau"
        service_display_name = f"{service_name}{type_suffix}"
    
    logger.info(f"🤖 Bắt đầu xử lý tự động: {service_display_name}")
    update_auto_mode_status(f"Đang xử lý: {service_display_name}")
    
    try:
        # *** KIỂM TRA DATABASE TRƯỚC TIÊN ***
        if not _check_database_has_data(service_name, service_type, service_display_name):
            return True  # Skip và chuyển sang dịch vụ tiếp theo
        
        if auto_mode_stop_flag:
            return False
        
        # Reset form và chọn dịch vụ
        if not _setup_service_form(service_name, service_display_name):
            return False
            
        if auto_mode_stop_flag:
            return False
        
        # Cấu hình đặc biệt cho "Nạp tiền đa mạng"
        if service_name == "Nạp tiền đa mạng" and service_type:
            if not _configure_payment_type(service_type):
                logger.warning(f"⚠️ Không thể cấu hình loại thanh toán cho {service_display_name}")
        
        # Lấy dữ liệu
        if not _fetch_service_data(service_display_name):
            return True  # Skip nếu không lấy được dữ liệu
            
        if auto_mode_stop_flag:
            return False
        
        # Kiểm tra dữ liệu đã load
        if not _validate_loaded_data(service_display_name):
            return True  # Skip nếu dữ liệu không hợp lệ
            
        if auto_mode_stop_flag:
            return False
        
        # Bắt đầu xử lý
        if not _start_processing(service_display_name):
            return False
            
        # Theo dõi tiến độ
        success = _monitor_processing_progress(service_display_name)
        
        if success:
            logger.info(f"🎉 Hoàn thành dịch vụ: {service_display_name}")
            update_auto_mode_status(f"Hoàn thành: {service_display_name}")
        else:
            logger.warning(f"⚠️ Timeout xử lý cho {service_display_name}")
            
        time.sleep(3)  # Đợi một chút trước khi sang dịch vụ tiếp theo
        return success
        
    except Exception as e:
        logger.error(f"❌ Lỗi dịch vụ {service_display_name}: {e}")
        update_auto_mode_status(f"❌ Lỗi: {service_display_name}")
        return False

def _check_database_has_data(service_name, service_type, service_display_name):
    """Kiểm tra database có dữ liệu không trước khi xử lý"""
    try:
        from db import db_fetch_service_data
        
        service_map = {
            "Tra cứu FTTH": "tra_cuu_ftth",
            "Gạch điện EVN": "gach_dien_evn", 
            "Nạp tiền đa mạng": "nap_tien_da_mang",
            "Nạp tiền mạng Viettel": "nap_tien_mang_viettel",
            "Thanh toán TV - Internet": "thanh_toan_tv_internet",
            "Tra cứu nợ thuê bao trả sau": "tra_cuu_no_thue_bao_tra_sau"
        }
        
        db_service_key = service_map.get(service_name)
        if not db_service_key:
            logger.warning(f"⚠️ Không tìm thấy service key cho {service_name}")
            return False
        
        # Gọi database với hoặc không có service_type
        if service_name == "Nạp tiền đa mạng" and service_type:
            db_data = db_fetch_service_data(db_service_key, service_type)
        else:
            db_data = db_fetch_service_data(db_service_key)
            
        if not db_data:
            logger.warning(f"⚠️ Database trả về None cho {service_display_name}")
            update_auto_mode_status(f"⚠️ Bỏ qua: {service_display_name} (DB None)")
            return False
        
        subscriber_codes = db_data.get("subscriber_codes", [])
        code_order_map = db_data.get("code_order_map", [])
        
        # Kiểm tra dữ liệu có rỗng không
        if not subscriber_codes and not code_order_map:
            logger.warning(f"⚠️ Database rỗng cho {service_display_name}")
            update_auto_mode_status(f"⚠️ Bỏ qua: {service_display_name} (DB rỗng)")
            return False
        
        logger.info(f"✅ Database có dữ liệu: {len(subscriber_codes)} codes, {len(code_order_map)} orders")
        return True
        
    except Exception as e:
        logger.warning(f"Không thể kiểm tra database: {e}")
        # Nếu không kiểm tra được DB, tiếp tục với flow bình thường
        return True

def _setup_service_form(service_name, service_display_name):
    """Reset form và chọn dịch vụ"""
    try:
        reset_service_form()
        time.sleep(2)
        
        r = get_root()
        service_combobox = wait_for_widget(r, find_combobox_by_values, (service_name,))
        
        if not service_combobox:
            logger.error(f"Không tìm thấy combobox dịch vụ cho: {service_display_name}")
            return False
            
        logger.info(f"🎯 Đang chọn dịch vụ: {service_display_name}")
        service_combobox.set(service_name)
        service_combobox.event_generate('<<ComboboxSelected>>')
        maybe_update_ui()
        time.sleep(3)
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi setup service form: {e}")
        return False

def _configure_payment_type(service_type):
    """Cấu hình loại thanh toán cho Nạp tiền đa mạng"""
    try:
        r = get_root()
        
        # Tìm combobox "Hình thức" với tìm kiếm sâu
        def find_form_combobox_deep(parent, depth=0):
            if depth > 15:
                return None
            try:
                for widget in parent.winfo_children():
                    if isinstance(widget, tk.ttk.Combobox):
                        values = widget.cget('values')
                        if values and "Nạp trả trước" in values and "Gạch nợ trả sau" in values:
                            return widget
                    result = find_form_combobox_deep(widget, depth + 1)
                    if result:
                        return result
            except Exception:
                pass
            return None
        
        form_combobox = find_form_combobox_deep(r)
        if not form_combobox:
            logger.warning("⚠️ Không tìm thấy combobox hình thức")
            return False
        
        current_value = form_combobox.get()
        target_value = "Nạp trả trước" if service_type == "prepaid" else "Gạch nợ trả sau"
        
        if current_value != target_value:
            logger.info(f"🔄 Thay đổi từ '{current_value}' sang '{target_value}'")
            form_combobox.set(target_value)
            form_combobox.event_generate('<<ComboboxSelected>>')
            maybe_update_ui()
            time.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi cấu hình payment type: {e}")
        return False

def _fetch_service_data(service_display_name):
    """Lấy dữ liệu từ server"""
    try:
        r = get_root()
        get_data_button = wait_for_widget(r, find_widget_by_text, (tk.ttk.Button, "Get dữ liệu"))
        
        if not get_data_button:
            logger.error("Không tìm thấy nút 'Get dữ liệu'")
            return False
            
        logger.info("📄 Đang lấy dữ liệu...")
        update_auto_mode_status(f"Lấy dữ liệu: {service_display_name}")
        get_data_button.invoke()
        maybe_update_ui()
        time.sleep(5)
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi fetch data: {e}")
        return False

def _validate_loaded_data(service_display_name):
    """Kiểm tra dữ liệu đã được load có hợp lệ không"""
    try:
        r = get_root()
        
        # Tìm text widget chứa dữ liệu
        text_widget = None
        for frame in r.winfo_children():
            if isinstance(frame, tk.Frame):
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Text) and subchild.cget('bg') != "#ccc":
                                text_widget = subchild
                                break
                        if text_widget:
                            break
                if text_widget:
                    break
        
        if not text_widget:
            logger.error("Không tìm thấy text widget để kiểm tra dữ liệu")
            return False
        
        # Kiểm tra dữ liệu với retry
        max_retries = 3
        for retry in range(max_retries):
            try:
                data_content = text_widget.get("1.0", "end-1c").strip()
                if data_content:
                    lines = data_content.splitlines()
                    valid_lines = [line.strip() for line in lines 
                                 if line.strip() and not any(keyword.lower() in line.lower() 
                                 for keyword in ["Không có", "Error", "Lỗi", "không tìm thấy", "empty", "null"])]
                    
                    if valid_lines:
                        logger.info(f"✅ Dữ liệu hợp lệ: {len(valid_lines)} dòng")
                        return True
                
                if retry < max_retries - 1:
                    logger.info(f"⏳ Đợi dữ liệu load... (lần {retry + 1}/{max_retries})")
                    time.sleep(1)
                    maybe_update_ui()
                    
            except Exception as e:
                logger.warning(f"Lỗi kiểm tra dữ liệu lần {retry + 1}: {e}")
                time.sleep(1)
        
        logger.warning(f"⚠️ Không có dữ liệu hợp lệ cho {service_display_name}")
        update_auto_mode_status(f"⚠️ Bỏ qua: {service_display_name} (Không có dữ liệu)")
        return False
        
    except Exception as e:
        logger.error(f"Lỗi validate data: {e}")
        return False

def _start_processing(service_display_name):
    """Bắt đầu xử lý dữ liệu"""
    try:
        r = get_root()
        
        # Tìm tất cả nút "Bắt đầu"
        all_start_buttons = []
        def find_all_start_buttons(parent, depth=0):
            if depth > 10:
                return
            try:
                for widget in parent.winfo_children():
                    if isinstance(widget, tk.ttk.Button):
                        if hasattr(widget, 'cget') and widget.cget('text') == "Bắt đầu":
                            style = widget.cget('style') or ""
                            all_start_buttons.append((widget, style))
                    find_all_start_buttons(widget, depth + 1)
            except Exception:
                pass
        
        find_all_start_buttons(r)
        
        if not all_start_buttons:
            logger.error("❌ Không tìm thấy nút 'Bắt đầu'")
            return False
        
        # Tìm nút có style "Blue.TButton" hoặc lấy nút đầu tiên
        start_button = None
        for btn, style in all_start_buttons:
            if style == "Blue.TButton":
                start_button = btn
                break
        
        if not start_button:
            start_button = all_start_buttons[0][0]
            logger.warning("⚠️ Không tìm thấy Blue.TButton, sử dụng nút đầu tiên")
        
        logger.info("▶️ Đang bắt đầu xử lý...")
        update_auto_mode_status(f"Đang xử lý dữ liệu: {service_display_name}")
        start_button.invoke()
        maybe_update_ui()
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi start processing: {e}")
        return False

def _monitor_processing_progress(service_display_name):
    """Theo dõi tiến độ xử lý"""
    try:
        r = get_root()
        
        # Tìm processed widget
        processed_widget = None
        for frame in r.winfo_children():
            if isinstance(frame, tk.Frame):
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Text) and subchild.cget('bg') == "#ccc":
                                processed_widget = subchild
                                break
                        if processed_widget:
                            break
                if processed_widget:
                    break
        
        # Chờ xử lý xong với timeout
        processing_timeout = 300  # 5 phút
        start_time = time.time()
        last_line_count = 0
        stuck_counter = 0
        max_stuck = 10
        
        while time.time() - start_time < processing_timeout:
            if auto_mode_stop_flag:
                return False
                
            if processed_widget:
                try:
                    processed_content = processed_widget.get("1.0", "end-1c").strip()
                    line_count = len(processed_content.splitlines()) if processed_content else 0
                    
                    if line_count > last_line_count:
                        logger.info(f"📈 Tiến độ: {line_count} mục đã xử lý")
                        last_line_count = line_count
                        stuck_counter = 0
                    else:
                        stuck_counter += 1
                        if stuck_counter >= max_stuck:
                            logger.info("✅ Xử lý có thể đã hoàn thành")
                            break
                            
                except Exception as e:
                    logger.warning(f"Lỗi theo dõi tiến độ: {e}")
            else:
                # Không có processed widget, đợi thời gian cố định
                time.sleep(10)
                break
            
            maybe_update_ui()
            time.sleep(2)
        
        return time.time() - start_time < processing_timeout
        
    except Exception as e:
        logger.error(f"Lỗi monitor progress: {e}")
        return False
		
def auto_cron_worker():
	"""Worker thread cho auto mode - xử lý tuần tự 6 dịch vụ với 2 loại cho Nạp tiền đa mạng"""
	global auto_mode_stop_flag, auto_mode_loop_enabled, auto_mode_loop_interval
	try:
		while auto_mode_loop_enabled and not auto_mode_stop_flag:
			logger.info(f"🔄 Bắt đầu chu kỳ auto mode mới (lặp lại mỗi {auto_mode_loop_interval} giây)")
			
			# Danh sách dịch vụ với loại cụ thể
			services_with_types = [
				("Tra cứu FTTH", None),
				("Gạch điện EVN", None),
				("Nạp tiền đa mạng", "prepaid"),  # Nạp trả trước
				("Nạp tiền đa mạng", "postpaid"), # Gạch nợ trả sau
				("Nạp tiền mạng Viettel", None),
				("Thanh toán TV - Internet", None),
				("Tra cứu nợ thuê bao trả sau", None)
			]
			
			completed_services = 0
			skipped_services = 0
			failed_services = 0
			
			for i, (service, service_type) in enumerate(services_with_types, 1):
				if auto_mode_stop_flag:
					logger.info("🛑 Auto mode bị dừng bởi người dùng")
					break
					
				# Hiển thị tên dịch vụ với loại cụ thể
				service_display_name = service
				if service_type:
					if service_type == "prepaid":
						service_display_name = f"{service} - Nạp trả trước"
					elif service_type == "postpaid":
						service_display_name = f"{service} - Gạch nợ trả sau"
				
				logger.info(f"🔄 Bắt đầu xử lý dịch vụ {i}/{len(services_with_types)}: {service_display_name}")
				success = auto_process_service(service, service_type)
				
				if success:
					completed_services += 1
					logger.info(f"✅ Hoàn thành dịch vụ: {service_display_name}")
				else:
					# Kiểm tra xem có phải bỏ qua hay thật sự lỗi
					current_status = ""
					try:
						r = get_root()
						auto_frame = None
						for widget in r.winfo_children():
							if hasattr(widget, 'winfo_name') and 'auto_frame' in str(widget.winfo_name()):
								auto_frame = widget
								break
						if auto_frame and hasattr(auto_frame, 'status_label'):
							current_status = auto_frame.status_label.cget('text')
					except:
						pass
						
					if "Bỏ qua" in current_status:
						skipped_services += 1
						logger.info(f"⚠️ Bỏ qua dịch vụ: {service_display_name} (Không có dữ liệu)")
					else:
						failed_services += 1
						logger.error(f"❌ Lỗi xử lý dịch vụ: {service_display_name}")
						# Có thể chọn tiếp tục hoặc dừng ở đây
						# break  # Uncomment nếu muốn dừng khi gặp lỗi thật sự
			
			# Thống kê cuối cùng
			total_processed = completed_services + skipped_services + failed_services
			logger.info(f"📊 Thống kê Auto Mode:")
			logger.info(f"   - Tổng dịch vụ: {len(services_with_types)}")
			logger.info(f"   - Hoàn thành: {completed_services}")
			logger.info(f"   - Bỏ qua: {skipped_services}")
			logger.info(f"   - Lỗi: {failed_services}")
			
			if not auto_mode_stop_flag:
				if failed_services == 0:
					logger.info("🏁 Hoàn thành tất cả dịch vụ trong auto mode")
					update_auto_mode_status(f"🏁 Hoàn thành: {completed_services}, Bỏ qua: {skipped_services}")
				else:
					logger.info(f"⚠️ Auto mode hoàn thành với {failed_services} lỗi")
					update_auto_mode_status(f"⚠️ Hoàn thành: {completed_services}, Lỗi: {failed_services}")
			else:
				logger.info("🛑 Auto mode đã bị dừng giữa chừng")
				update_auto_mode_status(f"🛑 Dừng: {total_processed}/{len(services_with_types)}")
				break
			
			# Kiểm tra xem có cần lặp lại không
			if auto_mode_loop_enabled and not auto_mode_stop_flag:
				logger.info(f"⏰ Chờ {auto_mode_loop_interval} giây trước khi lặp lại...")
				update_auto_mode_status(f"⏰ Chờ {auto_mode_loop_interval}s để lặp lại...")
				
				# Chờ với kiểm tra stop flag mỗi giây
				for i in range(auto_mode_loop_interval):
					if auto_mode_stop_flag:
						break
					time.sleep(1)
					maybe_update_ui()
				
				if auto_mode_stop_flag:
					break
					
				logger.info("🔄 Bắt đầu chu kỳ auto mode tiếp theo...")
			else:
				break
	
	except Exception as e:
		logger.error(f"❌ Lỗi trong auto cron worker: {e}")
		update_auto_mode_status("❌ Lỗi hệ thống")
	finally:
		# Reset auto mode
		global auto_mode_enabled
		auto_mode_enabled = False
		update_auto_mode_ui()


def start_auto_mode():
	"""Bắt đầu chế độ tự động"""
	global auto_mode_enabled, auto_mode_thread, auto_mode_stop_flag, auto_mode_loop_enabled
	
	if auto_mode_enabled:
		logger.warning("Auto mode đã đang chạy!")
		return
		
	auto_mode_enabled = True
	auto_mode_stop_flag = False
	auto_mode_loop_enabled = True  # Bật chế độ lặp tự động
	
	# Khởi tạo thread cho auto mode
	auto_mode_thread = threading.Thread(target=auto_cron_worker, daemon=True)
	auto_mode_thread.start()
	
	logger.info("🚀 Đã bắt đầu Auto Mode (lặp lại mỗi 10 giây)")
	update_auto_mode_status("🚀 Đã bắt đầu Auto Mode (lặp lại mỗi 10s)")
	update_auto_mode_ui()

def stop_auto_mode():
	"""Dừng chế độ tự động"""
	global auto_mode_enabled, auto_mode_stop_flag, auto_mode_loop_enabled
	
	auto_mode_stop_flag = True
	auto_mode_enabled = False
	auto_mode_loop_enabled = False  # Tắt chế độ lặp tự động
	
	logger.info("🛑 Đã dừng Auto Mode")
	update_auto_mode_status("🛑 Đã dừng Auto Mode")
	update_auto_mode_ui()
	
	# Đợi thread kết thúc
	if auto_mode_thread and auto_mode_thread.is_alive():
		auto_mode_thread.join(timeout=5)  # Tăng timeout join

def update_auto_mode_status(status_text):
	"""Cập nhật status label của auto mode"""
	try:
		r = get_root()
		if not r:
			return
			
		# Tìm frame chứa auto mode controls
		auto_frame = None
		for widget in r.winfo_children():
			if hasattr(widget, 'winfo_name') and 'auto_frame' in str(widget.winfo_name()):
				auto_frame = widget
				break
				
		if auto_frame and hasattr(auto_frame, 'status_label'):
			auto_frame.status_label.config(text=status_text, fg="blue")
			maybe_update_ui()
	except Exception as e:
		logger.error(f"Lỗi cập nhật auto mode status: {e}")

def update_auto_mode_ui():
	"""Cập nhật UI theo trạng thái auto mode"""
	try:
		r = get_root()
		if not r:
			return
			
		# Tìm frame chứa các nút auto mode
		auto_frame = None
		for widget in r.winfo_children():
			if hasattr(widget, 'winfo_name') and 'auto_frame' in str(widget.winfo_name()):
				auto_frame = widget
				break
				
		if auto_frame:
			for widget in auto_frame.winfo_children():
				if isinstance(widget, tk.ttk.Button):
					if "Bắt đầu Auto" in widget.cget('text'):
						widget.config(state="disabled" if auto_mode_enabled else "normal")
					elif "Dừng Auto" in widget.cget('text'):
						widget.config(state="normal" if auto_mode_enabled else "disabled")
			
			# Cập nhật status label
			if hasattr(auto_frame, 'status_label'):
				if auto_mode_enabled:
					if auto_mode_loop_enabled:
						auto_frame.status_label.config(text="🔄 Đang chạy (lặp lại mỗi 10s)...", fg="orange")
					else:
						auto_frame.status_label.config(text="🔄 Đang chạy...", fg="orange")
				else:
					auto_frame.status_label.config(text="Sẵn sàng", fg="green")
					
	except Exception as e:
		logger.error(f"Lỗi cập nhật auto mode UI: {e}")

def create_auto_mode_controls():
	"""Tạo các điều khiển cho auto mode"""
	try:
		r = get_root()
		if not r:
			return
		
		# Kiểm tra xem đã tồn tại auto_frame chưa
		auto_frame_exists = False
		for widget in r.winfo_children():
			if hasattr(widget, 'winfo_name') and 'auto_frame' in str(widget.winfo_name()):
				auto_frame_exists = True
				break
		
		if auto_frame_exists:
			return  # Đã tạo rồi, không tạo lại
		
		# Tạo frame cho auto controls
		auto_frame = tk.Frame(r, name="auto_frame")
		auto_frame.pack(side="top", padx=6, pady=6, fill="x")
		
		# Label
		tk.Label(auto_frame, text="🤖 Chế độ tự động:", font=("Arial", 10, "bold")).pack(side="left")
		
		# Nút bắt đầu auto
		start_auto_btn = tk.ttk.Button(
			auto_frame, 
			text="🚀 Bắt đầu Auto Mode", 
			command=start_auto_mode
		)
		start_auto_btn.pack(side="left", padx=5)
		
		# Nút dừng auto
		stop_auto_btn = tk.ttk.Button(
			auto_frame, 
			text="🛑 Dừng Auto Mode", 
			command=stop_auto_mode,
			state="disabled"
		)
		stop_auto_btn.pack(side="left", padx=5)
		
		# Thông tin về chế độ lặp
		loop_info_label = tk.Label(
			auto_frame, 
			text="⏰ Tự động lặp lại mỗi 10 giây", 
			fg="purple", 
			font=("Arial", 8, "italic")
		)
		loop_info_label.pack(side="left", padx=10)
		
		# Status label với màu sắc
		status_label = tk.Label(auto_frame, text="Sẵn sàng", fg="green", font=("Arial", 9, "bold"))
		status_label.pack(side="right", padx=10)
		
		# Lưu reference đến status label để có thể cập nhật sau
		auto_frame.status_label = status_label
		
		# Separator
		separator = tk.ttk.Separator(r, orient="horizontal")
		separator.pack(fill="x", padx=6, pady=3)
		
	except Exception as e:
		logger.error(f"Lỗi tạo auto mode controls: {e}")

def main():
	"""Hàm main - chỉ khởi tạo một lần"""
	global driver, ui_initialized
	
	try:
		# Khởi tạo UI chính
		initialize_main_ui()
		
		# Khởi tạo trình duyệt và đăng nhập tự động bằng tài khoản mặc định
		ensure_driver_and_login()
		try:
			login_process()
		except Exception:
			pass
			
	except Exception as e:
		logger.error(f"Lỗi khởi tạo: {e}")

if __name__ == "__main__":
	try:
		main()
		
		def on_closing():
			global auto_mode_stop_flag, auto_mode_loop_enabled
			auto_mode_stop_flag = True
			auto_mode_loop_enabled = False
			cleanup()
			if root:
				root.destroy()
		
		if root:
			root.protocol("WM_DELETE_WINDOW", on_closing)
			root.mainloop()
	except Exception as e:
		logger.error(f"Lỗi chính: {e}")
		#messagebox.showerror("Lỗi", f"Lỗi khởi động ứng dụng: {e}")
	finally:
		cleanup()