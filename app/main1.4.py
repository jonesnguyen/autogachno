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

def auto_process_service(service_name):
	"""Tự động xử lý một dịch vụ cụ thể với retry và timeout"""
	global auto_mode_stop_flag
	try:
		logger.info(f"🤖 Bắt đầu xử lý tự động: {service_name}")
		
		# Cập nhật status label
		update_auto_mode_status(f"Đang xử lý: {service_name}")
		
		# Reset form trước khi chọn dịch vụ mới
		reset_service_form()
		time.sleep(2)
		
		# Tìm và chọn dịch vụ trong combobox với chờ
		r = get_root()
		service_combobox = wait_for_widget(
			r, 
			find_combobox_by_values, 
			(service_name,)
		)
		
		if not service_combobox:
			logger.error(f"Không tìm thấy combobox dịch vụ cho: {service_name}")
			return False
			
		# Chọn dịch vụ
		logger.info(f"🎯 Đang chọn dịch vụ: {service_name}")
		service_combobox.set(service_name)
		service_combobox.event_generate('<<ComboboxSelected>>')
		maybe_update_ui()
		time.sleep(3)  # Đợi UI cập nhật và form dịch vụ được load
		
		if auto_mode_stop_flag:
			return False
			
		# Chờ nút "Get dữ liệu" xuất hiện
		get_data_button = wait_for_widget(
			r,
			find_widget_by_text,
			(tk.ttk.Button, "Get dữ liệu")
		)
		if not get_data_button:
			logger.error("Không tìm thấy nút 'Get dữ liệu' sau khi load form")
			return False
			
		# Bấm nút Get dữ liệu
		logger.info("🔄 Đang lấy dữ liệu...")
		update_auto_mode_status(f"Đang lấy dữ liệu: {service_name}")
		get_data_button.invoke()
		maybe_update_ui()
		time.sleep(5)  # Đợi dữ liệu load lâu hơn
		
		if auto_mode_stop_flag:
			return False
		
		# *** KIỂM TRA DATABASE TRƯỚC KHI KIỂM TRA TEXT WIDGET ***
		# Kiểm tra xem dữ liệu từ database có rỗng không
		try:
			from ..db import db_fetch_service_data
			service_map = {
				"Tra cứu FTTH": "tra_cuu_ftth",
				"Gạch điện EVN": "gach_dien_evn", 
				"Nạp tiền đa mạng": "nap_tien_da_mang",
				"Nạp tiền mạng Viettel": "nap_tien_mang_viettel",
				"Thanh toán TV - Internet": "thanh_toan_tv_internet",
				"Tra cứu nợ thuê bao trả sau": "tra_cuu_no_thue_bao_tra_sau"
			}
			
			db_service_key = service_map.get(service_name)
			if db_service_key:
				db_data = db_fetch_service_data(db_service_key)
				if db_data:
					subscriber_codes = db_data.get("subscriber_codes", [])
					code_order_map = db_data.get("code_order_map", [])
					
					# Kiểm tra nếu cả subscriber_codes và code_order_map đều rỗng
					if not subscriber_codes and not code_order_map:
						logger.warning(f"⚠️ Database trả về dữ liệu rỗng cho {service_name}")
						logger.info(f"   - subscriber_codes: {subscriber_codes}")
						logger.info(f"   - code_order_map: {code_order_map}")
						update_auto_mode_status(f"⚠️ Bỏ qua: {service_name} (DB rỗng)")
						return True  # Bỏ qua và chuyển sang dịch vụ tiếp theo
		except Exception as e:
			logger.warning(f"Không thể kiểm tra dữ liệu database: {e}")
			# Tiếp tục kiểm tra text widget như bình thường
			
		# Tìm text widget chứa dữ liệu để kiểm tra
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
		
		# Kiểm tra dữ liệu đã được load chưa với retry
		data_loaded = False
		data_content = ""
		max_retries = 3  # Tăng retry
		for retry in range(max_retries):
			try:
				data_content = text_widget.get("1.0", "end-1c").strip()
				if data_content and len(data_content.splitlines()) > 0:
					# Kiểm tra xem có phải dữ liệu thật không (không phải thông báo lỗi)
					lines = data_content.splitlines()
					valid_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("Không có") and not line.strip().startswith("Error")]
					
					if valid_lines:
						data_loaded = True
						logger.info(f"✅ Dữ liệu đã được load: {len(valid_lines)} dòng hợp lệ")
						break
					else:
						logger.warning(f"⚠️ Dữ liệu load nhưng không hợp lệ hoặc rỗng: {data_content[:100]}...")
						if retry >= max_retries - 3:  # Trong 3 lần cuối, kiểm tra kỹ hơn
							break
				else:
					logger.info(f"⏳ Đợi dữ liệu load... (lần {retry + 1}/{max_retries})")
				time.sleep(1)
				maybe_update_ui()
			except Exception as e:
				logger.warning(f"Lỗi kiểm tra dữ liệu lần {retry + 1}: {e}")
				time.sleep(1)
		
		# Kiểm tra cuối cùng xem có dữ liệu không
		if not data_loaded:
			logger.warning(f"⚠️ Không có dữ liệu cho dịch vụ {service_name} - Bỏ qua và chuyển sang dịch vụ tiếp theo")
			update_auto_mode_status(f"⚠️ Bỏ qua: {service_name} (Không có dữ liệu)")
			return True  # Return True để tiếp tục với dịch vụ tiếp theo, không dừng toàn bộ auto mode
		
		# Kiểm tra lại nội dung dữ liệu một lần nữa để đảm bảo
		final_data_content = text_widget.get("1.0", "end-1c").strip()
		if not final_data_content:
			logger.warning(f"⚠️ Dữ liệu rỗng cho dịch vụ {service_name} - Bỏ qua")
			update_auto_mode_status(f"⚠️ Bỏ qua: {service_name} (Dữ liệu rỗng)")
			return True
			
		# Kiểm tra xem có phải thông báo lỗi không
		error_keywords = ["Không có", "Error", "Lỗi", "không tìm thấy", "empty", "null"]
		if any(keyword.lower() in final_data_content.lower() for keyword in error_keywords):
			logger.warning(f"⚠️ Dữ liệu chứa thông báo lỗi cho dịch vụ {service_name}: {final_data_content[:100]}...")
			update_auto_mode_status(f"⚠️ Bỏ qua: {service_name} (Dữ liệu lỗi)")
			return True
			
		# Cập nhật data_content để sử dụng ở phần sau
		data_content = final_data_content
		
		# Hiển thị thông tin dữ liệu đã load
		try:
			if data_content:
				lines = data_content.split('\n')
				valid_lines = [line.strip() for line in lines if line.strip()]
				logger.info(f"📊 Số lượng mã cần xử lý: {len(valid_lines)}")
				for i, line in enumerate(valid_lines[:3], 1):  # Hiển thị 3 mã đầu tiên
					if '|' in line:
						code, order_id = line.split('|', 1)
						logger.info(f"   - Mã {i}: {code.strip()} (Order: {order_id.strip()})")
					else:
						logger.info(f"   - Mã {i}: {line.strip()}")
		except Exception as e:
			logger.warning(f"Lỗi hiển thị dữ liệu sample: {e}")
		
		if auto_mode_stop_flag:
			return False
		
		# *** IMPROVED: Tìm tất cả nút "Bắt đầu" và debug chúng ***
		logger.info("🔍 Tìm kiếm các nút 'Bắt đầu'...")
		all_start_buttons = []
		
		def find_all_start_buttons(parent, depth=0):
			if depth > 10:  # Giới hạn độ sâu
				return
			try:
				for widget in parent.winfo_children():
					if isinstance(widget, tk.ttk.Button):
						if hasattr(widget, 'cget') and widget.cget('text') == "Bắt đầu":
							style = widget.cget('style') or ""
							logger.info(f"   - Tìm thấy nút 'Bắt đầu': style='{style}', state='{widget.cget('state')}'")
							all_start_buttons.append((widget, style))
					# Tìm đệ quy trong widget con
					find_all_start_buttons(widget, depth + 1)
			except Exception as e:
				pass
		
		find_all_start_buttons(r)
		
		if not all_start_buttons:
			logger.error("❌ Không tìm thấy nút 'Bắt đầu' nào sau khi load dữ liệu")
			return False
		
		# Tìm nút có style "Blue.TButton" hoặc lấy nút đầu tiên
		start_button = None
		for btn, style in all_start_buttons:
			if style == "Blue.TButton":
				start_button = btn
				logger.info(f"✅ Tìm thấy nút 'Bắt đầu' có style 'Blue.TButton'")
				break
		
		if not start_button and all_start_buttons:
			# Nếu không tìm thấy Blue.TButton, lấy nút đầu tiên và log warning
			start_button = all_start_buttons[0][0]
			logger.warning(f"⚠️ Không tìm thấy nút 'Blue.TButton', sử dụng nút đầu tiên: style='{all_start_buttons[0][1]}'")
		
		if not start_button:
			logger.error("❌ Không có nút 'Bắt đầu' khả dụng")
			return False
		
		# Bấm nút Bắt đầu
		logger.info("▶️ Đang bắt đầu xử lý...")
		update_auto_mode_status(f"Đang xử lý dữ liệu: {service_name}")
		start_button.invoke()
		maybe_update_ui()
		
		# Theo dõi tiến độ xử lý bằng cách kiểm tra text widget "Đã xử lý"
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
		
		if not processed_widget:
			logger.warning("Không tìm thấy processed text widget để theo dõi tiến độ")
		
		# Chờ xử lý xong với timeout 300 giây (5 phút mỗi dịch vụ)
		processing_timeout = 300
		start_time = time.time()
		last_line_count = 0
		stuck_counter = 0
		max_stuck = 10  # Nếu không thay đổi trong 10 lần check, coi như xong hoặc lỗi
		
		while time.time() - start_time < processing_timeout:
			if auto_mode_stop_flag:
				return False
				
			try:
				if processed_widget:
					processed_content = processed_widget.get("1.0", "end-1c").strip()
					line_count = len(processed_content.splitlines()) if processed_content else 0
					total_lines = len(data_content.splitlines())
					
					if line_count > last_line_count:
						logger.info(f"📈 Tiến độ: {line_count} / {total_lines} (~{int(line_count / total_lines * 100) if total_lines > 0 else 0}%)")
						last_line_count = line_count
						stuck_counter = 0
					else:
						stuck_counter += 1
						if stuck_counter >= max_stuck:
							logger.info(f"✅ Xử lý có thể đã hoàn thành (không thay đổi trong {max_stuck * 2} giây)")
							break
					
					if line_count >= total_lines:
						logger.info(f"✅ Đã xử lý xong tất cả: {line_count} mục")
						break
				else:
					# Không có processed widget, chỉ đợi một thời gian cố định
					time.sleep(10)
					break
			except Exception as e:
				logger.warning(f"Lỗi theo dõi tiến độ: {e}")
			
			maybe_update_ui()
			time.sleep(2)  # Check mỗi 2 giây
		
		if time.time() - start_time >= processing_timeout:
			logger.warning(f"⚠️ Timeout xử lý cho {service_name}")
			return False
		
		logger.info(f"🎉 Hoàn thành dịch vụ: {service_name}")
		update_auto_mode_status(f"Hoàn thành: {service_name}")
		time.sleep(3)  # Đợi một chút trước khi sang dịch vụ tiếp theo
		return True
		
	except Exception as e:
		logger.error(f"❌ Lỗi xử lý dịch vụ {service_name}: {e}")
		update_auto_mode_status(f"❌ Lỗi: {service_name}")
		return False
	
def auto_cron_worker():
	"""Worker thread cho auto mode - xử lý tuần tự 6 dịch vụ"""
	global auto_mode_stop_flag, auto_mode_loop_enabled, auto_mode_loop_interval
	try:
		while auto_mode_loop_enabled and not auto_mode_stop_flag:
			logger.info(f"🔄 Bắt đầu chu kỳ auto mode mới (lặp lại mỗi {auto_mode_loop_interval} giây)")
			
			services = [
				"Tra cứu FTTH",
				"Gạch điện EVN",
				"Nạp tiền đa mạng",
				"Nạp tiền mạng Viettel",
				"Thanh toán TV - Internet",
				"Tra cứu nợ thuê bao trả sau"
			]
			
			completed_services = 0
			skipped_services = 0
			failed_services = 0
			
			for service in services:
				if auto_mode_stop_flag:
					logger.info("🛑 Auto mode bị dừng bởi người dùng")
					break
					
				logger.info(f"🔄 Bắt đầu xử lý dịch vụ {completed_services + skipped_services + failed_services + 1}/{len(services)}: {service}")
				success = auto_process_service(service)
				
				if success:
					completed_services += 1
					logger.info(f"✅ Hoàn thành dịch vụ: {service}")
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
						logger.info(f"⚠️ Bỏ qua dịch vụ: {service} (Không có dữ liệu)")
					else:
						failed_services += 1
						logger.error(f"❌ Lỗi xử lý dịch vụ: {service}")
						# Có thể chọn tiếp tục hoặc dừng ở đây
						# break  # Uncomment nếu muốn dừng khi gặp lỗi thật sự
			
			# Thống kê cuối cùng
			total_processed = completed_services + skipped_services + failed_services
			logger.info(f"📊 Thống kê Auto Mode:")
			logger.info(f"   - Tổng dịch vụ: {len(services)}")
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
				update_auto_mode_status(f"🛑 Dừng: {total_processed}/{len(services)}")
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