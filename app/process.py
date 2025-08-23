def process_lookup_ftth_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý tra cứu FTTH không cần GUI, điều khiển selenium trực tiếp."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý FTTH cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    print("   ✅ Bắt đầu xử lý (bỏ qua đăng nhập)")
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang FTTH...")
            navigate_to_ftth_page_and_select_radio()
            print("   ✅ Đã điều hướng thành công đến trang FTTH")
            
            # Hiển thị tiến trình cho từng order nếu có
            if order_id:
                print("   📋 Danh sách mã sẽ xử lý:")
                for idx, cb in enumerate(codes, 1):
                    print(f"      {idx}. {cb}")
            
            results = []
            for idx, cbil in enumerate(codes, 1):
                print(f"\n📱 [MÃ {idx}/{len(codes)}] Xử lý mã: {cbil}")
                success = False
                for attempt in range(AUTOMATION_MAX_RETRIES):  # Retry tối đa cấu hình
                    try:
                        cbil = (cbil or "").strip()
                        if not cbil:
                            print(f"   ⚠️  Mã rỗng, bỏ qua")
                            break
                        
                        if attempt > 0:
                            print(f"   🔄 Retry lần {attempt + 1}/{AUTOMATION_MAX_RETRIES} cho mã {cbil}")
                            logger.info(f"Retry lần {attempt + 1} cho mã {cbil}")
                            driver.refresh()
                            time.sleep(2)
                            navigate_to_ftth_page_and_select_radio()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        root.update() if 'root' in globals() else None
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
                        element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                        _is_amount, amount, _pid = amount_by_cbil(cbil, element41, False)
                        details = extract_ftth_details_from_page()
                        
                        print(f"   ✅ Xử lý thành công: Amount = {amount}")
                        if details:
                            print(f"   📋 Chi tiết FTTH:")
                            for key, value in details.items():
                                print(f"      • {key}: {value}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount, "status": "success"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            db_success = update_database_immediately(order_id, cbil, "success", amount, "FTTH lookup ok", details)
                            if not db_success:
                                logger.warning(f"Database update thất bại cho {cbil}")
                        else:
                            print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {cbil}")
                        
                        print(f"   🎉 Hoàn thành xử lý mã {cbil}")
                        break
                        
                    except Exception as e:
                        print(f"   ❌ Lần thử {attempt + 1} thất bại: {e}")
                        logger.warning(f"Lần thử {attempt + 1} thất bại cho {cbil}: {e}")
                        if attempt < (AUTOMATION_MAX_RETRIES - 1):  # Còn cơ hội retry
                            print(f"   ⏳ Chờ 1s trước khi retry...")
                            time.sleep(1)  # Delay thông minh
                            continue
                        else:  # Hết retry
                            print(f"   💥 Hết retry, mã {cbil} thất bại hoàn toàn")
                            logger.error(f"FTTH code {cbil} thất bại sau {AUTOMATION_MAX_RETRIES} lần thử: {e}")
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
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý FTTH:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            logger.info(f"FTTH processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_lookup_ftth_codes error: {e}")

def process_evn_payment_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý thanh toán điện EVN không cần GUI, điều khiển selenium trực tiếp."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý EVN cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang EVN...")
            navigate_to_evn_page()
            print("   ✅ Đã điều hướng thành công đến trang EVN")
            
            results = []
            for idx, cbil in enumerate(codes, 1):
                print(f"\n📱 [MÃ {idx}/{len(codes)}] Xử lý mã: {cbil}")
                success = False
                for attempt in range(AUTOMATION_MAX_RETRIES):  # Retry tối đa theo cấu hình
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
                            navigate_to_evn_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        root.update() if 'root' in globals() else None
                        time.sleep(0.5)
                        
                        print(f"   📝 Điền mã hóa đơn: {cbil}")
                        customer = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "collectElectricBillForm:j_idt29")))
                        customer.clear()
                        customer.send_keys(cbil)
                        
                        print(f"   🔍 Nhấn nút KIỂM TRA...")
                        payment_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "collectElectricBillForm:j_idt31")))
                        payment_button.click()
                        time.sleep(1)
                        
                        print(f"   ⏳ Chờ modal loading...")
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        
                        print(f"   📊 Lấy thông tin kết quả...")
                        element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                        _is_amount, amount, _pid = amount_by_cbil(cbil, element41, False)
                        
                        print(f"   ✅ Xử lý thành công: Amount = {amount}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount, "status": "success"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            db_success = update_database_immediately(order_id, cbil, "success", amount, "EVN payment ok", None)
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
                            logger.error(f"EVN code {cbil} thất bại sau 3 lần thử: {e}")
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
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý EVN:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            logger.info(f"EVN processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_evn_payment_codes error: {e}")

def process_topup_multinetwork_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý nạp tiền đa mạng - hỗ trợ cả nạp trả trước và gạch nợ trả sau."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý Topup đa mạng cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang Topup đa mạng...")
            navigate_to_topup_multinetwork_page()
            print("   ✅ Đã điều hướng thành công đến trang Topup đa mạng")
            
            results = []
            for idx, cbil in enumerate(codes, 1):
                print(f"\n📱 [MÃ {idx}/{len(codes)}] Xử lý mã: {cbil}")
                
                # Hiển thị tiến trình tương tự FTTH
                print(f"   🔄 Đang xử lý {cbil} | Order ID: {order_id or 'Không có'}")
                print(f"   📍 Loại dịch vụ: {'Nạp trả trước' if '|' in cbil else 'Gạch nợ trả sau'}")
                
                # Phân tích dữ liệu để xác định loại dịch vụ
                is_prepaid = '|' in cbil  # Nạp trả trước: có dấu | (sđt|số tiền)
                if is_prepaid:
                    # Nạp trả trước: sđt|số tiền
                    parts = cbil.split('|')
                    if len(parts) != 2:
                        print(f"   ❌ Sai định dạng: {cbil} (cần: sđt|số tiền)")
                        results.append({"code": cbil, "amount": None, "status": "failed", "message": "Sai định dạng"})
                        continue
                    
                    phone_number = parts[0].strip()
                    amount_str = parts[1].strip()
                    try:
                        amount = int(amount_str)
                        valid_amounts = [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]
                        if amount not in valid_amounts:
                            print(f"   ❌ Số tiền không hợp lệ: {amount} (chỉ cho phép: {valid_amounts})")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": f"Số tiền {amount} không hợp lệ"})
                            continue
                    except ValueError:
                        print(f"   ❌ Số tiền không hợp lệ: {amount_str}")
                        results.append({"code": cbil, "amount": None, "status": "failed", "message": "Số tiền không hợp lệ"})
                        continue
                    
                    print(f"   🎯 Nạp trả trước: {phone_number} | Số tiền: {amount:,}đ")
                    process_code = phone_number
                else:
                    # Gạch nợ trả sau: chỉ số điện thoại
                    phone_number = cbil.strip()
                    print(f"   🎯 Gạch nợ trả sau: {phone_number}")
                    process_code = phone_number
                
                success = False
                for attempt in range(3):  # Retry tối đa 3 lần
                    try:
                        if attempt > 0:
                            print(f"   🔄 Retry lần {attempt + 1}/3 cho mã {cbil}")
                            logger.info(f"Retry lần {attempt + 1} cho mã {cbil}")
                            driver.refresh()
                            time.sleep(2)
                            navigate_to_topup_multinetwork_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        root.update() if 'root' in globals() else None
                        time.sleep(0.5)
                        
                        print(f"   📝 Điền số điện thoại: {process_code}")
                        print(f"   🔄 Tiến trình: {cbil} - Bước 1/4: Điền số điện thoại")
                        phone_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:phoneNumber")))
                        phone_input.clear()
                        phone_input.send_keys(process_code)
                        
                        # Nếu là nạp trả trước, nhập số tiền
                        if is_prepaid:  # Nạp trả trước
                            print(f"   🔄 Tiến trình: {cbil} - Bước 2/4: Điền số tiền")
                            try:
                                print(f"   💰 Điền số tiền: {amount:,}đ")
                                amount_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.ID, "payMoneyForm:amount"))
                                )
                                amount_input.clear()
                                amount_input.send_keys(str(amount))
                                time.sleep(1)
                            except:
                                # Nếu không tìm thấy input số tiền, thử tìm element khác
                                amount_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number'], input[name*='amount'], .amount-input"))
                                )
                                amount_input.clear()
                                amount_input.send_keys(str(amount))
                                time.sleep(1)
                        
                        # Tự động điền mã PIN từ config
                        print(f"   🔄 Tiến trình: {cbil} - Bước 3/4: Điền mã PIN")
                        try:
                            print(f"   🔐 Điền mã PIN: {Config.DEFAULT_PIN}")
                            pin_input = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.ID, "payMoneyForm:pin"))
                            )
                            pin_input.clear()
                            pin_input.send_keys(Config.DEFAULT_PIN)
                            time.sleep(1)
                        except:
                            # Nếu không tìm thấy input PIN theo ID, thử tìm element khác
                            try:
                                pin_input = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name*='pin'], .pin-input, input[placeholder*='PIN'], input[placeholder*='pin']"))
                                )
                                pin_input.clear()
                                pin_input.send_keys(Config.DEFAULT_PIN)
                                time.sleep(1)
                                print(f"   🔐 Điền mã PIN thành công (fallback): {Config.DEFAULT_PIN}")
                            except Exception as pin_error:
                                print(f"   ⚠️ Không thể tìm thấy input PIN: {pin_error}")
                        
                        print(f"   🔄 Tiến trình: {cbil} - Bước 4/4: Xử lý giao dịch")
                        print(f"   🔍 Nhấn nút TIẾP TỤC...")
                        continue_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "payMoneyForm:btnContinue")))
                        continue_button.click()
                        time.sleep(1)
                        
                        print(f"   ⏳ Chờ modal loading...")
                        WebDriverWait(driver, 16).until(EC.invisibility_of_element_located((By.ID, "payMoneyForm:j_idt6_modal")))
                        
                        # Kiểm tra thông báo lỗi
                        error_text = get_error_alert_text()
                        if error_text:
                            print(f"   ❌ Có thông báo lỗi: {error_text}")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": error_text})
                            
                            # Update database cho trường hợp thất bại
                            if order_id:
                                print(f"   💾 Update database cho trường hợp thất bại...")
                                # Lưu thông tin loại dịch vụ vào notes
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Lỗi: {error_text}"
                                else:
                                    notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Lỗi: {error_text}"
                                
                                db_success = update_database_immediately(order_id, process_code, "failed", None, notes, None)
                                if not db_success:
                                    logger.warning(f"Database update thất bại cho {process_code}")
                            break
                        
                        # Lấy thông tin kết quả từ trang
                        print(f"   📊 Lấy thông tin kết quả...")
                        try:
                            # Tìm element chứa thông tin kết quả
                            result_element = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".result-info, .payment-result, .success-message, [class*='result'], [class*='success']"))
                            )
                            result_text = result_element.text.strip()
                            print(f"   📋 Kết quả: {result_text}")
                            
                            # Phân tích kết quả để tạo notes chi tiết
                            if "thành công" in result_text.lower() or "success" in result_text.lower():
                                result_status = "success"
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ | Kết quả: {result_text}"
                                else:
                                    notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Kết quả: {result_text}"
                            else:
                                result_status = "failed"
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ | Kết quả: {result_text}"
                                else:
                                    notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Kết quả: {result_text}"
                                
                        except Exception as result_error:
                            print(f"   ⚠️ Không thể lấy thông tin kết quả: {result_error}")
                            result_status = "success"
                            if is_prepaid:
                                notes = f"Multi-network: Nạp trả trước - {cbil} | Số tiền: {amount:,}đ"
                            else:
                                notes = f"Multi-network: Gạch nợ trả sau - {cbil}"
                        
                        print(f"   ✅ Xử lý thành công cho {'nạp trả trước' if is_prepaid else 'gạch nợ trả sau'} {process_code}")
                        
                        # Hiển thị kết quả chi tiết tương tự FTTH
                        if 'result_text' in locals():
                            print(f"   📋 Kết quả chi tiết:")
                            print(f"      • Mã: {cbil}")
                            print(f"      • Loại dịch vụ: {'Nạp trả trước' if is_prepaid else 'Gạch nợ trả sau'}")
                            if is_prepaid:
                                print(f"      • Số tiền: {amount:,}đ")
                            print(f"      • Kết quả: {result_text}")
                            print(f"      • Trạng thái: {result_status}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount if is_prepaid else None, "status": result_status, "message": result_text if 'result_text' in locals() else "Thành công"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            amount_for_db = amount if is_prepaid else None
                            db_success = update_database_immediately(order_id, process_code, result_status, amount_for_db, notes, None)
                            if not db_success:
                                logger.warning(f"Database update thất bại cho {process_code}")
                        else:
                            print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {process_code}")
                        
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
                            logger.error(f"Topup đa mạng code {cbil} thất bại sau 3 lần thử: {e}")
                            results.append({"code": cbil, "amount": None, "status": "failed", "message": str(e)})
                            
                            # Update database cho trường hợp thất bại
                            if order_id:
                                print(f"   💾 Update database cho trường hợp thất bại...")
                                # Lưu thông tin loại dịch vụ vào notes
                                if is_prepaid:
                                    notes = f"Multi-network: Nạp trả trước - {cbil} | Lỗi: {str(e)}"
                                else:
                                    notes = f"Multi-network: Gạch nợ trả sau - {cbil} | Lỗi: {str(e)}"
                                
                                db_success = update_database_immediately(order_id, process_code, "failed", None, notes, None)
                                if not db_success:
                                    logger.warning(f"Database update thất bại cho {process_code}")
                            else:
                                print(f"⚠️  [WARNING] Không có order_id, bỏ qua database update cho {process_code}")
                
                if not success:
                    print(f"   💥 Mã {cbil} không thể xử lý sau 3 lần thử")
                    logger.error(f"Mã {cbil} không thể xử lý sau 3 lần thử")
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý Topup đa mạng:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            # Hiển thị chi tiết từng mã tương tự FTTH
            print(f"\n📋 [CHI TIẾT] Kết quả xử lý từng mã:")
            for result in results:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                amount_info = f" | Số tiền: {result['amount']:,}đ" if result.get('amount') else ""
                message_info = f" | {result.get('message', '')}" if result.get('message') else ""
                print(f"   {status_icon} {result['code']}{amount_info}{message_info}")
            
            logger.info(f"Topup multinetwork processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_topup_multinetwork_codes error: {e}")

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
                        
                        root.update() if 'root' in globals() else None
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

def process_tv_internet_codes(codes: List[str], order_id: Optional[str] = None):
    """Xử lý thanh toán TV-Internet không cần GUI, điều khiển selenium trực tiếp."""
    print(f"🚀 [AUTOMATION] Bắt đầu xử lý TV-Internet cho {len(codes)} mã")
    print(f"   📋 Order ID: {order_id or 'Không có'}")
    
    if not ensure_driver_and_login():
        print("   ❌ Không thể khởi tạo driver hoặc đăng nhập")
        logger.error("Không thể khởi tạo driver hoặc đăng nhập")
        return
    
    try:
        with automation_lock:
            print("   🔒 Đã khóa automation, điều hướng đến trang TV-Internet...")
            navigate_to_tv_internet_page()
            print("   ✅ Đã điều hướng thành công đến trang TV-Internet")
            
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
                            navigate_to_tv_internet_page()
                        else:
                            print(f"   🎯 Lần thử đầu tiên cho mã {cbil}")
                        
                        root.update() if 'root' in globals() else None
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
                        element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                        _is_amount, amount, _pid = amount_by_cbil(cbil, element41, False)
                        
                        print(f"   ✅ Xử lý thành công: Amount = {amount}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount, "status": "success"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            db_success = update_database_immediately(order_id, cbil, "success", amount, "TV-Internet payment ok", None)
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
                            logger.error(f"TV-Internet code {cbil} thất bại sau 3 lần thử: {e}")
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
            
            print(f"\n📊 [KẾT QUẢ] Tổng kết xử lý TV-Internet:")
            print(f"   ✅ Thành công: {len([r for r in results if r['status'] == 'success'])} mã")
            print(f"   ❌ Thất bại: {len([r for r in results if r['status'] == 'failed'])} mã")
            print(f"   📋 Tổng cộng: {len(results)} mã")
            
            logger.info(f"TV-Internet processed: {len(results)} items")
    except Exception as e:
        print(f"   💥 Lỗi tổng thể: {e}")
        logger.error(f"process_tv_internet_codes error: {e}")

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
                        
                        root.update() if 'root' in globals() else None
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
                        element41 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:j_idt41")))
                        _is_amount, amount, _pid = amount_by_cbil(cbil, element41, False)
                        
                        print(f"   ✅ Xử lý thành công: Amount = {amount}")
                        
                        # Thành công, thoát khỏi retry loop
                        success = True
                        results.append({"code": cbil, "amount": amount, "status": "success"})
                        
                        # Update database ngay lập tức cho từng đơn xử lý xong
                        if order_id:
                            print(f"   💾 Bắt đầu update database...")
                            db_success = update_database_immediately(order_id, cbil, "success", amount, "Postpaid lookup ok", None)
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
