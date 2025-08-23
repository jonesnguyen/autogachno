import requests
from requests.auth import HTTPBasicAuth
import sys
import os

# Thêm thư mục gốc vào sys.path để import được
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.db import db_get_account_credentials, db_get_code_by_order_id

API_URL = "https://thuhohpk.com/api/tool-bill-completed"

def mark_bill_completed(order_id: str, auth: tuple = None, timeout: int = 10):
    """
    Gọi API tool-bill-completed bằng Basic Auth và in ra toàn bộ phản hồi từ server.
    
    Args:
        order_id: ID của đơn hàng để lấy credentials và code
        auth: Tuple (username, password) - nếu None sẽ lấy từ database
        timeout: Timeout cho request
    """
    # Lấy code từ database dựa vào order_id
    code = db_get_code_by_order_id(order_id)
    if not code:
        print(f"   ❌ Không tìm thấy code cho order_id: {order_id}")
        return {"success": False, "msg": "Không tìm thấy code"}
    
    print(f"   📋 Lấy được code: {code} cho order_id: {order_id}")
    
    credentials = db_get_account_credentials(order_id)
    email, password = credentials
    auth = (email, password)
    print(f"📧 Sử dụng credentials từ database: {email}")
    
    headers = {"Content-Type": "application/json"}
    payload = {"account": code}  # Sử dụng code từ database

    try:
        print(f"🔐 Gọi API với auth: {auth[0]} và code: {code}")
        resp = requests.post(
            API_URL,
            auth=HTTPBasicAuth(*auth),
            json=payload,
            headers=headers,
            timeout=timeout
        )
        # Nếu là JSON hợp lệ
        try:
            data = resp.json()
            msg = data.get("msg", "").strip()
            return {
                "success": (msg == "Cập nhật thành công"),
                "msg": msg
            }
        except ValueError:
            # Không phải JSON
            return {"success": False, "msg": f"Không phải JSON: {resp.text}"}

    except requests.RequestException as e:
        return {"success": False, "msg": f"Lỗi gọi API: {e}"}


if __name__ == "__main__":
    # Test với credentials từ database
    order_id = "ec18432a-a1da-4e61-b90d-d6acc4fe8720"
    result = mark_bill_completed(order_id)
    print("Kết quả xử lý:", result)
    
    
