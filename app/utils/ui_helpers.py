import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Any

from ..config import Config

logger = logging.getLogger(__name__)

stop_flag = False
root: tk.Tk | None = None

def get_root() -> tk.Tk:
    global root
    if root is None:
        root = tk.Tk()
        root.title("HPK Tool - Viettel Pay Automation")
        root.geometry("500x550")
        root.option_add("*Font", "Arial 10")
        try:
            root.iconbitmap(Config.ICON_FILE)
        except Exception as e:
            logger.warning(f"Không thể tải icon: {e}")
    return root

def set_root(r: tk.Tk) -> None:
    global root
    root = r

def maybe_update_ui():
    try:
        r = get_root()
        r.update_idletasks()
        r.update()
    except Exception:
        pass

def populate_text_widget(text_widget, data_list):
    """Đổ dữ liệu vào Text widget"""
    try:
        text_widget.config(state="normal")
        text_widget.delete("1.0", "end")
        if data_list:
            text_widget.insert("1.0", "\n".join(data_list))
        text_widget.config(state="normal")
    except Exception as e:
        logger.error(f"Lỗi đổ dữ liệu vào text widget: {e}")

def populate_entry_widget(entry_widget, value):
    """Đổ dữ liệu vào Entry widget"""
    try:
        entry_widget.delete(0, "end")
        if value:
            entry_widget.insert(0, str(value))
    except Exception as e:
        logger.error(f"Lỗi đổ dữ liệu vào entry widget: {e}")

def populate_combobox_widget(combobox_widget, value):
    """Đổ dữ liệu vào Combobox widget"""
    try:
        if value and value in combobox_widget['values']:
            combobox_widget.set(value)
    except Exception as e:
        logger.error(f"Lỗi đổ dữ liệu vào combobox widget: {e}")

def delete_ctmed(cmted: tk.Text):
    """Xóa nội dung text widget"""
    cmted.config(state="normal")
    cmted.delete("1.0", "end")
    cmted.config(state="disabled")

def insert_ctmed(cmted: tk.Text, cbil: str):
    """Thêm text vào widget"""
    cmted.config(state="normal")
    cmted.insert("1.0", f"{cbil}\n")
    cmted.config(state="disabled")

def stop_tool():
    """Dừng chương trình"""
    global stop_flag
    stop_flag = True
    #messagebox.showinfo(Config.TITLE, "Đã dừng chương trình")

def update_stop_flag():
    """Reset stop flag"""
    global stop_flag
    stop_flag = False

def valid_data(data: List[Any]) -> bool:
    """Kiểm tra dữ liệu đầu vào"""
    try:
        for item in data:
            # Nếu là danh sách (ví dụ danh sách mã), yêu cầu có ít nhất 1 phần tử không rỗng
            if isinstance(item, (list, tuple)):
                has_nonempty = any((isinstance(x, str) and x.strip()) for x in item)
                if not has_nonempty:
                    #messagebox.showwarning(Config.TITLE, "Vui lòng nhập đầy đủ thông tin")
                    return False
            else:
                # Xử lý chuỗi/tham số đơn lẻ
                text = str(item) if item is not None else ""
                if not text.strip():
                    #messagebox.showwarning(Config.TITLE, "Vui lòng nhập đầy đủ thông tin")
                    return False
        return True
    except Exception as e:
        logger.error(f"Lỗi kiểm tra dữ liệu: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi kiểm tra dữ liệu: {e}")
        return False

def clear_widgets(main_frm):
    r = get_root()
    for widget in r.winfo_children():
        if widget is not main_frm:
            # Không xóa auto mode controls
            if hasattr(widget, 'winfo_name') and 'auto_frame' in str(widget.winfo_name()):
                continue
            # Không xóa separator của auto mode
            if isinstance(widget, tk.ttk.Separator):
                continue
            widget.destroy()

def show_services_form():
    try:
        r = get_root()
        main_frm = tk.Frame(r)
        main_frm.pack(expand=True, side="top", padx=6, pady=6, fill="both")
        tklbl_choose = tk.Label(main_frm, text="Loại thanh toán:")
        tklbl_choose.pack(side="left")
        tkcbb_choose = ttk.Combobox(main_frm, values=[
            "Tra cứu FTTH",
            "Gạch điện EVN", 
            "Nạp tiền đa mạng",
            "Nạp tiền mạng Viettel",
            "Thanh toán TV - Internet",
            "Tra cứu nợ thuê bao trả sau"
        ], width="32", state="readonly")
        tkcbb_choose.pack(side="left", padx=6, expand=True, fill="x")
        tkcbb_choose.set("Tra cứu FTTH")
        def handle_choose_services(event, choose, main_frm):
            service = choose.get()
            clear_widgets(main_frm)
            # Import lazily to avoid circular imports
            if service == "Tra cứu FTTH":
                from ..services.ftth import form_lookup_ftth
                form_lookup_ftth()
            elif service == "Gạch điện EVN":
                from ..services.evn import form_debt_electric
                form_debt_electric() 
            elif service == "Nạp tiền đa mạng":
                from ..services.topup_multi import form_payment_phone
                form_payment_phone()
            elif service == "Nạp tiền mạng Viettel":
                from ..services.topup_viettel import form_payment_viettel
                form_payment_viettel()
            elif service == "Thanh toán TV - Internet":
                from ..services.tv_internet import form_payment_internet
                form_payment_internet()
            elif service == "Tra cứu nợ thuê bao trả sau":
                from ..services.postpaid import form_lookup_card
                form_lookup_card()
        tkcbb_choose.bind("<<ComboboxSelected>>", lambda event: handle_choose_services(event, tkcbb_choose, main_frm))
        handle_choose_services(None, tkcbb_choose, main_frm)
    except Exception as e:
        logger.error(f"Lỗi hiển thị form dịch vụ: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi hiển thị form dịch vụ: {e}")
