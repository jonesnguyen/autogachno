import os
import logging
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import sys
# Ensure parent directory is on sys.path so we can import the package `app` when running directly
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
	sys.path.insert(0, PARENT_DIR)

from app.config import Config, LOGIN_USERNAME
from app.utils.browser import driver, initialize_browser, cleanup, login_process, ensure_driver_and_login
from app.utils.ui_helpers import show_services_form, set_root

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

def main():
	global driver
	# Khởi tạo trình duyệt và đăng nhập tự động bằng tài khoản mặc định
	try:
		ensure_driver_and_login()
		try:
			login_process()
		except Exception:
			pass
	except Exception as e:
		logger.error(f"Lỗi khởi tạo trình duyệt: {e}")
	# Hiển thị form dịch vụ luôn, không cần đọc cấu hình
	show_services_form()

if __name__ == "__main__":
	try:
		main()
		root.protocol("WM_DELETE_WINDOW", lambda: [cleanup(), root.destroy()])
		root.mainloop()
	except Exception as e:
		logger.error(f"Lỗi chính: {e}")
		#messagebox.showerror("Lỗi", f"Lỗi khởi động ứng dụng: {e}")
	finally:
		cleanup()
