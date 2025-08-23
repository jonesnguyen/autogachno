"""API client utilities"""

import logging
import requests
from typing import Any, Dict, List, Optional
import time

from ..config import Config
from ..db import db_fetch_service_data

logger = logging.getLogger(__name__)

def send_callback_with_retry(order_id: str, code: str, status: str, amount: Any, notes: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """Gửi callback với retry logic tối đa 3 lần."""
    print(f"🔄 [CALLBACK] Bắt đầu gửi callback cho mã {code} - Order: {order_id}")
    print(f"   📊 Status: {status}, Amount: {amount}, Notes: {notes}")
    
    for attempt in range(3):
        try:
            payload = {
                "orderId": order_id,
                "code": code,
                "status": status,
                "amount": str(amount) if isinstance(amount, (int, float)) else None,
                "notes": notes,
            }
            
            if details:
                payload["data"] = {
                    "type": "ftth_details",
                    "details": details,
                }
                print(f"   📋 Data: {details}")
            
            print(f"   📤 Lần thử {attempt + 1}/3: Gửi đến {Config.NODE_SERVER_URL}/api/automation/callback")
            response = requests.post(
                f"{Config.NODE_SERVER_URL}/api/automation/callback",
                json=payload,
                timeout=10,  # Tăng timeout
            )
            
            if response.status_code == 200:
                print(f"   ✅ Callback thành công cho {code} (lần {attempt + 1})")
                logger.info(f"Callback thành công cho {code} (lần {attempt + 1})")
                return True
            else:
                print(f"   ❌ Callback thất bại cho {code} (lần {attempt + 1}): HTTP {response.status_code}")
                logger.warning(f"Callback thất bại cho {code} (lần {attempt + 1}): {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Callback lỗi cho {code} (lần {attempt + 1}): {e}")
            logger.warning(f"Callback lỗi cho {code} (lần {attempt + 1}): {e}")
        
        if attempt < 2:  # Còn cơ hội retry
            print(f"   ⏳ Chờ 2s trước khi retry...")
            time.sleep(2)  # Delay giữa các lần retry
    
    print(f"   💥 Callback thất bại sau 3 lần thử cho {code}")
    logger.error(f"Callback thất bại sau 3 lần thử cho {code}")
    return False

def start_api_server():
    """Bỏ qua mock API server: danh sách đơn lấy từ Database qua Node API."""
    logger.info("Bỏ qua mock_api_server: dùng trực tiếp Node API/DB")
    return False

def check_api_health():
    """Kiểm tra Node API (nguồn dữ liệu thật) có hoạt động không"""
    try:
        response = requests.get(f"{Config.NODE_SERVER_URL}/api/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def fetch_api_data(service_type: str) -> Optional[Dict]:
    """Đã chuyển sang đọc trực tiếp DB (bỏ API)."""
    return db_fetch_service_data(service_type)
