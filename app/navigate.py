def navigate_to_ftth_page_and_select_radio():
    """Đi tới trang FTTH và chọn radio 'Số thuê bao'"""
    try:
        # Bỏ qua kiểm tra đăng nhập theo yêu cầu
        target_url = "https://kpp.bankplus.vn/pages/newInternetTelevisionViettel.jsf?serviceCode=000003&serviceType=INTERNET"
        driver.get(target_url)
        # Chờ input mã thuê bao xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
        # Chọn radio Số thuê bao (id payMoneyForm:console:3)
        try:
            radio_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "payMoneyForm:console:3")))
            radio_box = radio_input.find_element(By.XPATH, "../../div[contains(@class,'ui-radiobutton-box')]")
            radio_box.click()
        except Exception:
            # fallback click vào label
            try:
                label = driver.find_element(By.XPATH, "//label[@for='payMoneyForm:console:3']")
                label.click()
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Không thể điều hướng FTTH hoặc chọn radio: {e}")
        raise  # Re-raise để caller biết có lỗi

def navigate_to_evn_page():
    """Điều hướng đến trang thanh toán điện EVN."""
    try:
        
        target_url = "https://kpp.bankplus.vn/pages/collectElectricBill.jsf?serviceCode=EVN"
        driver.get(target_url)
        # Chờ input mã thuê bao xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "collectElectricBillForm:j_idt29")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng EVN: {e}")
        raise

def navigate_to_topup_multinetwork_page():
    """Điều hướng đến trang nạp tiền đa mạng."""
    try:
        
        target_url = "https://kpp.bankplus.vn/pages/chargecard.jsf"
        driver.get(target_url)
        # Chờ input số điện thoại xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "indexForm:phoneNumberId")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng Topup đa mạng: {e}")
        raise

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

def navigate_to_tv_internet_page():
    """Điều hướng đến trang thanh toán TV-Internet."""
    try:
        target_url = "https://kpp.bankplus.vn/pages/newInternetTelevisionViettel.jsf?serviceCode=000003&serviceType=INTERNET"
        driver.get(target_url)
        # Chờ input mã thuê bao xuất hiện
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "payMoneyForm:contractCode")))
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Không thể điều hướng TV-Internet: {e}")
        raise

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
