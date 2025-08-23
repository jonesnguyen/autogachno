def get_data_ftth(text_widget, order_entry: Optional[ttk.Entry] = None):
    """Lấy dữ liệu API cho Tra cứu FTTH và set Order ID nếu có"""
    try:
        data = fetch_api_data("tra_cuu_ftth")
        if data and "subscriber_codes" in data:
            codes = data["subscriber_codes"]
            populate_text_widget(text_widget, codes)
            
            # Tự động điền mã PIN từ config (nếu có pin_widget)
            if 'pin_widget' in locals() and pin_widget:
                print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
                populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            order_id = data.get("order_id")
            code_map = data.get("code_order_map") or []
            info_msg = f"Đã tải {len(codes)} mã thuê bao FTTH"
            if order_id:
                print(f"[INFO] Order ID từ DB (gần nhất): {order_id}", flush=True)
                logger.info(f"Order ID từ DB (FTTH, gần nhất): {order_id}")
                info_msg += f"\nOrder ID (gần nhất): {order_id}"
            # In mapping chi tiết mã -> orderId nếu có
            if code_map:
                print("[INFO] Mapping mã -> Order ID:", flush=True)
                for item in code_map:
                    try:
                        print(f"  {item.get('code')}: {item.get('orderId')}", flush=True)
                    except Exception:
                        pass
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu FTTH: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu FTTH: {e}")

def get_data_evn(text_widget, phone_widget, pin_widget):
    """Lấy dữ liệu API cho Gạch điện EVN"""
    try:
        data = fetch_api_data("gach_dien_evn")
        if data:
            if "bill_codes" in data:
                populate_text_widget(text_widget, data["bill_codes"])
            if "receiver_phone" in data:
                populate_entry_widget(phone_widget, data["receiver_phone"])
            
            # Tự động điền mã PIN từ config
            print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(data.get("bill_codes", []))
            order_id = data.get("order_id")
            info_msg = f"Đã tải {count} mã hóa đơn điện EVN"
            if order_id:
                print(f"[INFO] Order ID từ DB: {order_id}", flush=True)
                logger.info(f"Order ID từ DB (EVN): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu EVN: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu EVN: {e}")

def get_data_multi_network(text_widget, pin_widget, form_widget, amount_widget, payment_type: str = None):
    """Lấy dữ liệu API cho Nạp tiền đa mạng"""
    try:
        print(f"[DEBUG] get_data_multi_network được gọi với payment_type: {payment_type}")
        
        # Lấy dữ liệu theo loại dịch vụ đã chọn
        if payment_type:
            print(f"[DEBUG] Gọi db_fetch_service_data với payment_type: {payment_type}")
            data = db_fetch_service_data("nap_tien_da_mang", payment_type)
        else:
            print(f"[DEBUG] Gọi fetch_api_data (không có payment_type)")
            data = fetch_api_data("nap_tien_da_mang")
            
        if data:
            if "phone_numbers" in data:
                populate_text_widget(text_widget, data["phone_numbers"])
            
            # Tự động điền mã PIN từ config
            print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            if "payment_type" in data:
                populate_combobox_widget(form_widget, data["payment_type"])
            if "amount" in data:
                populate_combobox_widget(amount_widget, data["amount"])
            
            count = len(data.get("phone_numbers", []))
            order_id = data.get("order_id")
            service_type_text = "Nạp trả trước (sđt|số tiền)" if payment_type == "prepaid" else "Gạch nợ trả sau (chỉ số điện thoại)" if payment_type == "postpaid" else "Đa mạng"
            info_msg = f"Đã tải {count} số điện thoại {service_type_text}"
            if order_id:
                print(f"[INFO] Order ID từ DB: {order_id}", flush=True)
                logger.info(f"Order ID từ DB (Đa mạng - {service_type_text}): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu đa mạng: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu đa mạng: {e}")

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

def get_data_tv_internet(text_widget, pin_widget):
    """Lấy dữ liệu API cho Thanh toán TV - Internet"""
    try:
        data = fetch_api_data("thanh_toan_tv_internet")
        if data:
            if "subscriber_codes" in data:
                populate_text_widget(text_widget, data["subscriber_codes"])
            
            # Tự động điền mã PIN từ config
            print(f"[DEBUG] Tự động điền mã PIN: {Config.DEFAULT_PIN}")
            populate_entry_widget(pin_widget, Config.DEFAULT_PIN)
            
            count = len(data.get("subscriber_codes", []))
            order_id = data.get("order_id")
            info_msg = f"Đã tải {count} mã thuê bao TV-Internet"
            if order_id:
                print(f"[INFO] Order ID từ DB: {order_id}", flush=True)
                logger.info(f"Order ID từ DB (TV-Internet): {order_id}")
                info_msg += f"\nOrder ID: {order_id}"
            #messagebox.showinfo(Config.TITLE, info_msg)
        else:
            #messagebox.showwarning(Config.TITLE, "Không có dữ liệu từ DB")
    except Exception as e:
        logger.error(f"Lỗi lấy dữ liệu TV-Internet: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi lấy dữ liệu TV-Internet: {e}")

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
