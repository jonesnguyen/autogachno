def payment_internet(tkinp_ctm, tkinp_ctmed, tkinp_pin):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        pin = tkinp_pin.get()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils, pin]):
            return False
        data = []
        for cbil in cbils:
            root.update()
            time.sleep(0.5)
            cbil = cbil.strip()
            if not stop_flag and cbil.strip() != "":
                try:
                    customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
                    customer.clear()
                    customer.send_keys(cbil)
                    time.sleep(0.5)
                    payment_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay0")))
                    payment_button.click()
                    time.sleep(1)
                    WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                    element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                    is_amount, amount, payment_id = amount_by_cbil(cbil, element41, True)
                    if not is_amount:
                        data.append([cbil, amount, Config.STATUS_COMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        continue
                    else:
                        payment_btn1 = WebDriverWait(driver, 16).until(EC.presence_of_element_located((By.ID, payment_id)))
                        payment_btn1.click()
                        pin_id = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:pinId")))
                        pin_id.clear()
                        pin_id.send_keys(pin)
                        pay_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay")))
                        pay_btn.click()
                        try:
                            cfm_modal = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, "payMoneyForm:dlgConfirm_modal")))
                            driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                        except:
                            pass
                        confirm_btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:yesId0")))
                        confirm_btn.click()
                        data.append([cbil, amount, Config.STATUS_COMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                        tkinp_ctm.delete("1.0", "1.end+1c")
                except Exception as e:
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                    tkinp_ctm.delete("1.0", "1.end+1c")
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Thanh toán TV - Internet"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán internet: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán internet: {e}")

def form_payment_internet():
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    phnum_frm = tk.Frame(root)
    phnum_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    btn_frm = tk.Frame(root)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Mã thuê bao")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=12, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=12, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    tklbl_pin = tk.Label(phnum_frm, text="Mã pin:")
    tklbl_pin.pack(side="left")
    tkinp_pin = ttk.Entry(phnum_frm, width=22)
    tkinp_pin.pack(side="left", padx=4)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=lambda: get_data_tv_internet(tkinp_ctm, tkinp_pin))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: payment_internet(tkinp_ctm, tkinp_ctmed, tkinp_pin))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 

def lookup_ftth(tkinp_ctm, tkinp_ctmed, tkinp_order: Optional[ttk.Entry] = None):
    
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        navigate_to_ftth_page_and_select_radio()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        # Hiển thị mapping mã -> orderId trước khi xử lý
        print("Order ID:")
        code_to_order: Dict[str, Optional[str]] = {}
        for raw in cbils:
            c = (raw or "").strip()
            if not c:
                continue
            oid = db_find_order_id('tra_cuu_ftth', c, None)
            code_to_order[c] = oid
            print(f"  {c}: {oid if oid else 'Không tìm thấy'}")

        data = []
        for cbil in cbils:
            root.update()
            time.sleep(1)
            cbil = cbil.strip()
            if not stop_flag and cbil.strip() != "":
                success = False
                for attempt in range(3):  # Retry tối đa 3 lần
                    try:
                        # Log tiến trình theo orderId
                        print(f"   🔧 Đang xử lý {cbil} | Order ID: {code_to_order.get(cbil) if code_to_order.get(cbil) else 'Không tìm thấy'}")
                        if attempt > 0:
                            logger.info(f"Retry lần {attempt + 1} cho mã {cbil}")
                            driver.refresh()
                            time.sleep(2)
                            navigate_to_ftth_page_and_select_radio()
                        
                        # Điền vào form
                        customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
                        customer.clear()
                        customer.send_keys(cbil)
                        # Nhấn nút thanh toán
                        payment_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay0")))
                        payment_button.click()
                        time.sleep(1)
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        # Kiểm tra thông báo lỗi (nếu có) và dừng retry khi chứa từ "không"
                        alert_text = get_error_alert_text()
                        if alert_text and ("không" in alert_text.lower()):
                            note_err = alert_text.strip()
                            data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                            insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi | {note_err}")
                            order_id_val = code_to_order.get(cbil) or db_find_order_id('tra_cuu_ftth', cbil.strip(), None)
                            if order_id_val:
                                try:
                                    _ = update_database_immediately(order_id_val, cbil, "failed", None, note_err, None)
                                except Exception as _e:
                                    logger.warning(f"DB update lỗi (failed) cho {cbil}: {_e}")
                            break
                        element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                        is_amount, amount, payment_id = amount_by_cbil(cbil, element41, False)
                        details = extract_ftth_details_from_page()
                        note_text = f"HD:{details.get('contract_code','')} | Chu:{details.get('contract_owner','')} | SDT:{details.get('contact_phone','')} | No:{details.get('debt_amount','')}"
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        data.append([cbil, amount, note_text])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount} | {note_text}")
                        
                        # Update trực tiếp DB: dùng mapping đã tra ở trên
                        order_id_val = code_to_order.get(cbil) or db_find_order_id('tra_cuu_ftth', cbil.strip(), None)
                        if not order_id_val:
                            print(f"   ⚠️ Không tìm thấy orderId cho code='{cbil}'. Bỏ qua update.")
                            # Hiển thị danh sách order_id pending/processing (nếu có) để dễ kiểm tra
                            pendings = db_check_pending_orders_for_code('tra_cuu_ftth', cbil.strip(), None)
                            if pendings:
                                print(f"   🔎 Pending/processing orderIds for {cbil}: {', '.join(pendings)}")
                        else:
                            try:
                                db_success = update_database_immediately(order_id_val, cbil, "success", amount, note_text, details)
                                if not db_success:
                                    logger.warning(f"Database update thất bại cho {cbil}")
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (success) cho {cbil}: {_e}")
                        
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        break
                        
                    except Exception as e:
                        logger.warning(f"Lần thử {attempt + 1} thất bại cho {cbil}: {e}")
                        if attempt < (AUTOMATION_MAX_RETRIES - 1):  # Còn cơ hội retry
                            time.sleep(1)  # Delay thông minh
                            continue
                        else:  # Hết retry
                            logger.error(f"Mã {cbil} thất bại sau {AUTOMATION_MAX_RETRIES} lần thử: {e}")
                            data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                            insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                            tkinp_ctm.delete("1.0", "1.end+1c")
                            break
                
                if not success:
                    logger.error(f"Mã {cbil} không thể xử lý sau 3 lần thử")
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Tra cứu FTTH"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi tra cứu FTTH: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi tra cứu FTTH: {e}")

def form_lookup_ftth():
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    btn_frm = tk.Frame(root)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Số thuê bao (mỗi dòng tạo 1 order)")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=16, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, height=16, width=32, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    # Loại bỏ ô Order ID: orderId sẽ mặc định dùng chính cbil; nút tạo orders từ DB
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=lambda: get_data_ftth(tkinp_ctm, None))
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    # Bỏ nút tạo orders: chỉ get dữ liệu và xử lý cập nhật cho DB sẵn có
    tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: lookup_ftth(tkinp_ctm, tkinp_ctmed, None))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 

def payment_phone(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkcbb_form, tkcbb_amount):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        pin = tkinp_pin.get()
        cbb_type = tkcbb_form.get()
        type_sub = handle_choose_select(cbb_type)
        if type_sub == 1:
            amount = tkcbb_amount.get()
            isnext = valid_data([cbils, pin, amount])
            if isnext:
                rsl_amount = handle_choose_amount(amount)
        else:
            isnext = valid_data([cbils, pin])
        if not isnext:
            return False
        data = []
        for cbil in cbils:
            cbil = cbil.strip()
            root.update()
            time.sleep(1)
            if not stop_flag and cbil.strip() != "":
                driver.refresh()
                time.sleep(2)
                navigate_to_topup_multinetwork_page()
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
                time.sleep(0.5)
                if type_sub == 1:
                    try:
                        try:
                            cfm_modalTT = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirmTT_modal")))
                            driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modalTT)
                            time.sleep(1)
                        except:
                            pass
                        spl_lbl = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier")))
                        spl_lbl.click()
                        spl_0 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:supplier_0")))
                        spl_0.click()
                        cfm_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesTTId")))
                        cfm_pay.click()
                    except:
                        pass
                    script = f"""
                    var element = document.querySelector('input[id="indexForm:subAmountId:{rsl_amount}"]').closest('div');
                    if (!element.classList.contains('ui-state-active')) {{
                        element.click();
                    }}
                    """
                    driver.execute_script(script)
                else:
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
                        lbl_debt = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:debtId_input")))
                        debt_str = lbl_debt.get_attribute('value')
                        debt = int(debt_str.replace(".", "").replace(",", ""))
                        if debt >= 5000:
                            inp_amount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:transAmountId_input")))
                            inp_amount.clear()
                            inp_amount.send_keys(debt)
                        else:
                            data.append([cbil, debt, Config.STATUS_COMPLETE])
                            tkinp_ctm.delete("1.0", "1.end+1c")
                            insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
                            continue
                    except:
                        data.append([cbil, 0, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - không nợ cước")
                        continue
                try:
                    pin_id = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:pinId")))
                    pin_id.clear()
                    pin_id.send_keys(pin)
                    btn_pay = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:btnPay")))
                    btn_pay.click()
                    try:
                        cfm_modal = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:dlgConfirm_modal")))
                        driver.execute_script("arguments[0].style.zIndex = '-99';", cfm_modal)
                    except:
                        pass
                    time.sleep(0.5)
                    btn_confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:yesIdCard")))
                    btn_confirm.click()
                    if type_sub == 1:
                        data.append([cbil, amount, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                    else:
                        data.append([cbil, debt, Config.STATUS_COMPLETE])
                        tkinp_ctm.delete("1.0", "1.end+1c")
                        insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
                except:
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    tkinp_ctm.delete("1.0", "1.end+1c")
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Nạp tiền đa mạng"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện thoại: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán điện thoại: {e}")

def form_payment_phone():
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    form_frm = tk.Frame(root)
    form_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    pin_frm = tk.Frame(root)
    pin_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    btn_frm = tk.Frame(root)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Số điện thoại")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=12, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=12, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    tklbl_form = tk.Label(form_frm, text="Hình thức:")
    tklbl_form.pack(side="left")
    tkcbb_form = ttk.Combobox(form_frm, values=["Nạp trả trước", "Gạch nợ trả sau"], width="14", state="readonly")
    tkcbb_form.pack(side="left")
    tkcbb_form.set("Nạp trả trước")
    tkcbb_form.bind("<<ComboboxSelected>>", lambda event: toggle_input_amount(tkcbb_form, tklbl_amount, tkcbb_amount))
    tkcbb_amount = ttk.Combobox(form_frm, values=["10.000đ", "20.000đ", "30.000đ", "50.000đ", "100.000đ", "200.000đ", "300.000đ", "500.000đ"], width="10", state="readonly")
    tkcbb_amount.pack(side="right")
    tklbl_amount = tk.Label(form_frm, text="Số tiền nạp:")
    tklbl_amount.pack(side="right")
    tklbl_pin = tk.Label(pin_frm, text="Mã pin:")
    tklbl_pin.pack(side="left")
    tkinp_pin = ttk.Entry(pin_frm, width=12)
    tkinp_pin.pack(side="left", padx=4)
    style = ttk.Style()
    style.configure("Red.TButton", foreground="red")
    style.configure("Blue.TButton", foreground="blue")
    style.configure("Green.TButton", foreground="green")
    def get_data_with_payment_type():
        selected = tkcbb_form.get()
        print(f"[DEBUG] Combobox được chọn: '{selected}'")
        
        if selected == "Nạp trả trước":
            payment_type = "prepaid"
        elif selected == "Gạch nợ trả sau":
            payment_type = "postpaid"
        else:
            payment_type = None
            
        print(f"[DEBUG] Payment type được map: {payment_type}")
        get_data_multi_network(tkinp_ctm, tkinp_pin, tkcbb_form, tkcbb_amount, payment_type)
    
    tkbtn_get_data = ttk.Button(btn_frm, text="Get dữ liệu", command=get_data_with_payment_type)
    tkbtn_get_data.pack(side='left', padx=5, pady=5)
    tkbtn_get_data.configure(style="Green.TButton")
    tkbtn_payment = ttk.Button(btn_frm, text="Bắt đầu", command=lambda: payment_phone(tkinp_ctm, tkinp_ctmed, tkinp_pin, tkcbb_form, tkcbb_amount))
    tkbtn_payment.pack(side='left', padx=5, pady=5)
    tkbtn_payment.configure(style="Blue.TButton") 
    tkbtn_destroy = ttk.Button(btn_frm, text="Dừng lại", command=stop_tool)
    tkbtn_destroy.pack(side='right', padx=5, pady=5)
    tkbtn_destroy.configure(style="Red.TButton") 

def lookup_card(tkinp_ctm, tkinp_ctmed):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        if not valid_data([cbils]):
            return False
        data = []
        for cbil in cbils:
            cbil = cbil.strip()
            root.update()
            time.sleep(1)
            if not stop_flag and cbil.strip() != "":
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

                    # Chờ modal/tiến trình, rồi kiểm tra thông báo info "không còn nợ cước"
                    time.sleep(1)
                    info_text = get_info_alert_text()
                    if info_text and ("không còn nợ cước" in info_text.lower()):
                        note_text = info_text.strip()
                        data.append([cbil, 0, Config.STATUS_COMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - 0 | {note_text}")
                        # Cập nhật DB success với amount=0 và notes = "code - 0 | alert"
                        order_id_val = db_find_order_id('tra_cuu_no_tra_sau', cbil.strip(), None)
                        if order_id_val:
                            try:
                                notes_db = f"{cbil} - 0 | {note_text}"
                                _ = update_database_immediately(order_id_val, cbil, "success", 0, notes_db, None)
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (Postpaid no debt) cho {cbil}: {_e}")
                        continue

                    # Lấy giá trị nợ cước nếu có
                    lbl_debt = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "indexForm:debtId_input")))
                    debt_str = lbl_debt.get_attribute('value')
                    debt = int(debt_str.replace(".", "").replace(",", ""))
                    data.append([cbil, debt, Config.STATUS_COMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {debt}")
                    # Cập nhật DB success với amount=debt
                    order_id_val = db_find_order_id('tra_cuu_no_tra_sau', cbil.strip(), None)
                    if order_id_val:
                        try:
                            _ = update_database_immediately(order_id_val, cbil, "success", debt, "Postpaid lookup ok", None)
                        except Exception as _e:
                            logger.warning(f"DB update lỗi (Postpaid debt) cho {cbil}: {_e}")
                    continue
                except:
                    # Nếu có thông báo info/alert khác thì lưu notes giống hiển thị
                    note_text = get_info_alert_text() or get_error_alert_text() or ""
                    data.append([cbil, "Không tìm thấy nợ cước", Config.STATUS_INCOMPLETE])
                    display_line = f"{cbil} - null{(' | ' + note_text) if note_text else ''}"
                    insert_ctmed(tkinp_ctmed, display_line)
                    # Cập nhật DB failed với notes giống hiển thị
                    order_id_val = db_find_order_id('tra_cuu_no_tra_sau', cbil.strip(), None)
                    if order_id_val:
                        try:
                            _ = update_database_immediately(order_id_val, cbil, "failed", None, display_line, None)
                        except Exception as _e:
                            logger.warning(f"DB update lỗi (Postpaid failed) cho {cbil}: {_e}")
                    continue
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Tra cứu nợ trả sau"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi tra cứu nợ trả sau: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi tra cứu nợ trả sau: {e}")

def form_lookup_card():
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    button_frm = tk.Frame(root)
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
            root.update()
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
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    form_frm = tk.Frame(root)
    form_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    pin_frm = tk.Frame(root)
    pin_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    button_frm = tk.Frame(root)
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

def debt_electric(tkinp_ctm, tkinp_ctmed, tkinp_phone, tkinp_pin):
    try:
        delete_ctmed(tkinp_ctmed)
        update_stop_flag()
        pin = tkinp_pin.get()
        phone = tkinp_phone.get()
        cbils = tkinp_ctm.get("1.0", "end-1c").splitlines()
        # EVN: chỉ 1 form nhập mã hóa đơn. Không cần số điện thoại và mã pin.
        if not valid_data([cbils]):
            return False
        data = []
        for cbil in cbils:
            cbil = cbil.strip()
            root.update()
            time.sleep(1)
            if not stop_flag and cbil.strip() != "":
                try:
                    # Điền mã hóa đơn
                    customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:billCodeId")))
                    customer.clear()
                    customer.send_keys(cbil)
                    time.sleep(0.5)

                    # Nhấn Pay/Check
                    payment = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:btnPay")))
                    payment.click()
                    time.sleep(1)

                    # Chờ modal ẩn
                    WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))

                    # Bắt lỗi EVN nếu có
                    alert_text = get_error_alert_text()
                    if alert_text and ("không" in alert_text.lower() or "đã xảy ra lỗi" in alert_text.lower()):
                        note_err = alert_text.strip()
                        data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                        insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi | {note_err}")
                        # Cập nhật DB failed cho EVN nếu có orderId
                        order_id_val = db_find_order_id('gach_dien_evn', cbil.strip(), None)
                        if order_id_val:
                            try:
                                _ = update_database_immediately(order_id_val, cbil, "failed", None, note_err, None)
                            except Exception as _e:
                                logger.warning(f"DB update lỗi (EVN failed) cho {cbil}: {_e}")
                        continue

                    # Lấy amount
                    lblamount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt49")))
                    try:
                        text_of_amount = lblamount.text
                        amount_str = text_of_amount.replace('VND', '').replace('.', '')
                        amount = int(amount_str)
                    except:
                        amount = lblamount.text

                    # Xác nhận
                    time.sleep(0.5)
                    confirm = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:yesIdEVN")))
                    confirm.click()

                    # Thành công
                    data.append([cbil, amount, Config.STATUS_COMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - {amount}")
                    # Cập nhật DB success
                    order_id_val = db_find_order_id('gach_dien_evn', cbil.strip(), None)
                    if order_id_val:
                        try:
                            _ = update_database_immediately(order_id_val, cbil, "success", amount, "EVN payment ok", None)
                        except Exception as _e:
                            logger.warning(f"DB update lỗi (EVN success) cho {cbil}: {_e}")
                    continue
                except Exception as e:
                    data.append([cbil, 0, Config.STATUS_INCOMPLETE])
                    insert_ctmed(tkinp_ctmed, f"{cbil} - Lỗi")
                    continue
        time.sleep(2)
        if len(data) > 0:
            name_dir = "Thanh toán điện EVN"
            export_excel(data, name_dir)
    except Exception as e:
        logger.error(f"Lỗi thanh toán điện EVN: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi thanh toán điện EVN: {e}")

def form_debt_electric():
    cus_frm = tk.Frame(root)
    cus_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    ctm_frm = tk.Frame(cus_frm)
    ctm_frm.pack(expand=True, side="left")
    ctmed_frm = tk.Frame(cus_frm)
    ctmed_frm.pack(expand=True, side="right")
    # Loại bỏ ô nhập SĐT và PIN theo yêu cầu
    btn_frm = tk.Frame(root)
    btn_frm.pack(expand=True, side="top", padx=14, pady=8, fill="both")
    tklbl_ctm = tk.Label(ctm_frm, text="Mã thuê bao")
    tklbl_ctm.pack(side="top")
    tkinp_ctm = tk.Text(ctm_frm, height=18, width=24)
    tkinp_ctm.pack(side="left", pady=8)
    tklbl_ctm = tk.Label(ctmed_frm, text="Đã xử lý")
    tklbl_ctm.pack(side="top")
    tkinp_ctmed = tk.Text(ctmed_frm, width=32, height=18, bg="#ccc", state="disabled")
    tkinp_ctmed.pack(side="left", pady=8)
    # Placeholder rỗng để giữ hàm gọi hiện tại (không dùng)
    tkinp_phone = ttk.Entry(root)
    tkinp_pin = ttk.Entry(root)
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

root = tk.Tk()
root.title("HPK Tool - Viettel Pay Automation")
root.geometry("500x550") 
root.option_add("*Font", "Arial 10")
try:
    root.iconbitmap(Config.ICON_FILE)
except Exception as e:
    logger.warning(f"Không thể tải icon: {e}")
    pass

def show_services_form():
    try:
        main_frm = tk.Frame(root)
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
            if service == "Tra cứu FTTH":
                form_lookup_ftth()
            elif service == "Gạch điện EVN":
                form_debt_electric() 
            elif service == "Nạp tiền đa mạng":
                form_payment_phone()
            elif service == "Nạp tiền mạng Viettel":
                form_payment_viettel()
            elif service == "Thanh toán TV - Internet":
                form_payment_internet()
            elif service == "Tra cứu nợ thuê bao trả sau":
                form_lookup_card()
        tkcbb_choose.bind("<<ComboboxSelected>>", lambda event: handle_choose_services(event, tkcbb_choose, main_frm))
        handle_choose_services(None, tkcbb_choose, main_frm)
    except Exception as e:
        logger.error(f"Lỗi hiển thị form dịch vụ: {e}")
        #messagebox.showerror(Config.TITLE, f"Lỗi hiển thị form dịch vụ: {e}")
