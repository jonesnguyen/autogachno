import threading
from threading import Thread
from typing import Any, Dict
from flask import Flask, jsonify, request
import requests
import os
NODE_SERVER_URL = os.getenv('NODE_SERVER_URL', 'http://127.0.0.1:5000')

# Lightweight internal API server to receive automation commands from the web app

app = Flask(__name__)

automation_lock = threading.Lock()


@app.get('/api/health')
def health():
    return jsonify({
        'status': 'success',
        'message': 'Python automation API is running',
    })


def _run_automation(service_type: str, payload: Dict[str, Any]):
    # Import here to avoid circular issues
    try:
        import main as app_main  # type: ignore
    except Exception:
        try:
            from . import main as app_main  # type: ignore
        except Exception:
            app_main = None

    # TODO: Map service_type to concrete automation routines in main.py
    # Placeholder: log intent; real selenium integration can call functions in main.py
    # Example: if app_main and service_type == 'tra_cuu_ftth': app_main.process_lookup_ftth(payload.get('codes', []))
    print('[automation] start', service_type, payload)
    # Basic mapping example
    try:
      if app_main and service_type == 'tra_cuu_ftth':
          # Kiểm tra đăng nhập trước khi xử lý
          if not app_main.is_logged_in(app_main.driver):
              print('[automation] Chưa đăng nhập, không thể xử lý FTTH')
              return
          
          codes = payload.get('codes') or []
          order_id = payload.get('orderId')
          # Giới hạn retry còn 1 khi chạy qua automation theo yêu cầu
          try:
            app_main.AUTOMATION_MAX_RETRIES = 1
          except Exception:
            pass
          app_main.process_lookup_ftth_codes(codes, order_id)
    except Exception as e:
      print('[automation] error', e)


@app.post('/api/automation/start')
def start_automation():
    data = request.get_json(force=True, silent=True) or {}
    service_type = data.get('serviceType') or data.get('service_type')
    if not service_type:
        return jsonify({'message': 'serviceType is required'}), 400

    with automation_lock:
        t = Thread(target=_run_automation, args=(service_type, data), daemon=True)
        t.start()

    return jsonify({'message': 'started', 'serviceType': service_type})


@app.get('/api/automation/cron')
def run_cron_once():
    # Pull pending orders from Node server and trigger automation
    try:
        # Import app_main here for login checks
        try:
            import main as app_main  # type: ignore
        except Exception:
            try:
                from . import main as app_main  # type: ignore
            except Exception:
                app_main = None  # type: ignore

        res = requests.get(f"{NODE_SERVER_URL}/api/automation/pending", timeout=5)
        if not res.ok:
            return jsonify({'message': 'upstream error'}), 502
        payload = res.json()
        started = []
        # Hiển thị tất cả orderId đang chờ
        try:
            pending_ids = payload.get('pendingOrderIds') or [o.get('orderId') for o in payload.get('orders', [])]
            print('[cron] Pending orders:', pending_ids)
        except Exception:
            pass
        for item in payload.get('orders', [])[:3]:
            order_id = item.get('orderId')
            service_type = item.get('serviceType')
            codes = [t.get('code') for t in item.get('transactions', [])]
            # claim order
            claim = requests.post(f"{NODE_SERVER_URL}/api/automation/claim", json={'orderId': order_id}, timeout=5)
            if not claim.ok:
                continue
            # Kiểm tra đăng nhập trước khi xử lý automation
            if service_type == 'tra_cuu_ftth' and app_main and not app_main.is_logged_in(app_main.driver):
                print(f'[cron] Chưa đăng nhập, bỏ qua order {order_id}')
                continue
                
            # start local automation
            print(f"[cron] Đang xử lý order {order_id} (service={service_type}) với {len(codes)} mã ...")
            _run_automation(service_type, {'orderId': order_id, 'codes': codes})
            started.append(order_id)
        return jsonify({'started': started})
    except Exception as e:
        return jsonify({'message': str(e)}), 500


def start_api_server(host: str = '0.0.0.0', port: int = 8080):
    def run():
        app.run(host=host, port=port, debug=False, use_reloader=False)

    thread = Thread(target=run, daemon=True)
    thread.start()
    return thread

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock API Server cho Viettel Pay Tool
Provides sample data for 6 services
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import threading
import time

app = Flask(__name__)
CORS(app)  # Cho phép CORS để gọi từ ứng dụng khác

# Dữ liệu mẫu cho các dịch vụ
SAMPLE_DATA = {
    "tra_cuu_ftth": {
        "description": "Tra cứu FTTH", 
        "sample_codes": [
            "84903123456", "84903234567", "84903345678", 
            "84903456789", "84903567890", "84903678901",
            "84903789012", "84903890123", "84903901234", "84904012345"
        ]
    },
    "gach_dien_evn": {
        "description": "Gạch điện EVN",
        "sample_codes": [
            "PE01234567890", "PE01345678901", "PE01456789012",
            "PE01567890123", "PE01678901234", "PE01789012345",
            "PE01890123456", "PE01901234567", "PE02012345678", "PE02123456789"
        ],
        "default_phone": "0987654321",
        "default_pin": "123456"
    },
    "nap_tien_da_mang": {
        "description": "Nạp tiền đa mạng",
        "sample_phones": [
            "0987123456", "0988234567", "0989345678", 
            "0985456789", "0986567890", "0984678901",
            "0983789012", "0982890123", "0981901234", "0980012345"
        ],
        "default_pin": "123456",
        "default_form": "Nạp trả trước",
        "default_amount": "50.000đ"
    },
    "nap_tien_viettel": {
        "description": "Nạp tiền mạng Viettel",
        "sample_phones": [
            "0967123456", "0968234567", "0969345678",
            "0965456789", "0966567890", "0964678901", 
            "0963789012", "0962890123", "0961901234", "0960012345"
        ],
        "default_pin": "123456",
        "default_amount": "100000"
    },
    "thanh_toan_tv_internet": {
        "description": "Thanh toán TV - Internet",
        "sample_codes": [
            "HTV001234567", "HTV002345678", "HTV003456789",
            "HTV004567890", "HTV005678901", "HTV006789012",
            "HTV007890123", "HTV008901234", "HTV009012345", "HTV010123456"
        ],
        "default_pin": "123456"
    },
    "tra_cuu_no_tra_sau": {
        "description": "Tra cứu nợ thuê bao trả sau",
        "sample_phones": [
            "0977123456", "0978234567", "0979345678",
            "0975456789", "0976567890", "0974678901",
            "0973789012", "0972890123", "0971901234", "0970012345"
        ]
    }
}

@app.route('/', methods=['GET'])
def home():
    """API Home endpoint"""
    return jsonify({
        "status": "success",
        "message": "Mock API Server cho Viettel Pay Tool",
        "endpoints": [
            "/api/data/tra_cuu_ftth",
            "/api/data/gach_dien_evn", 
            "/api/data/nap_tien_da_mang",
            "/api/data/nap_tien_viettel",
            "/api/data/thanh_toan_tv_internet",
            "/api/data/tra_cuu_no_tra_sau"
        ]
    })

@app.route('/api/data/<service_type>', methods=['GET'])
def get_sample_data(service_type):
    """Lấy dữ liệu mẫu cho từng loại dịch vụ"""
    try:
        # Simulate API delay
        time.sleep(random.uniform(0.5, 1.5))
        
        if service_type not in SAMPLE_DATA:
            return jsonify({
                "status": "error",
                "message": "Service type not found"
            }), 404

        service_data = SAMPLE_DATA[service_type]
        
        # Tạo response data tùy theo loại dịch vụ
        if service_type == "tra_cuu_ftth":
            return jsonify({
                "status": "success",
                "service": service_data["description"],
                "data": {
                    "subscriber_codes": random.sample(service_data["sample_codes"], 
                                                    random.randint(3, 7))
                }
            })
            
        elif service_type == "gach_dien_evn":
            return jsonify({
                "status": "success", 
                "service": service_data["description"],
                "data": {
                    "bill_codes": random.sample(service_data["sample_codes"], 
                                               random.randint(3, 6)),
                    "receiver_phone": service_data["default_phone"],
                    "pin": service_data["default_pin"]
                }
            })
            
        elif service_type == "nap_tien_da_mang":
            return jsonify({
                "status": "success",
                "service": service_data["description"], 
                "data": {
                    "phone_numbers": random.sample(service_data["sample_phones"],
                                                  random.randint(4, 8)),
                    "pin": service_data["default_pin"],
                    "payment_type": service_data["default_form"],
                    "amount": service_data["default_amount"]
                }
            })
            
        elif service_type == "nap_tien_viettel":
            return jsonify({
                "status": "success",
                "service": service_data["description"],
                "data": {
                    "phone_numbers": random.sample(service_data["sample_phones"],
                                                  random.randint(4, 8)), 
                    "pin": service_data["default_pin"],
                    "amount": service_data["default_amount"]
                }
            })
            
        elif service_type == "thanh_toan_tv_internet":
            return jsonify({
                "status": "success",
                "service": service_data["description"],
                "data": {
                    "subscriber_codes": random.sample(service_data["sample_codes"],
                                                    random.randint(3, 7)),
                    "pin": service_data["default_pin"]
                }
            })
            
        elif service_type == "tra_cuu_no_tra_sau":
            return jsonify({
                "status": "success",
                "service": service_data["description"],
                "data": {
                    "phone_numbers": random.sample(service_data["sample_phones"],
                                                  random.randint(5, 9))
                }
            })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "success",
        "message": "API server is running",
        "timestamp": time.time()
    })

def run_api_server():
    """Chạy API server trong thread riêng"""
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)

def start_api_server():
    """Khởi động API server trong background"""
    server_thread = threading.Thread(target=run_api_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == '__main__':
    print("Starting Mock API Server...")
    print("API endpoints available at:")
    print("  - http://127.0.0.1:8080/")
    print("  - http://127.0.0.1:8080/api/data/<service_type>")
    print("  - http://127.0.0.1:8080/api/health")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        app.run(host='127.0.0.1', port=8080, debug=True)
    except KeyboardInterrupt:
        print("\nAPI Server stopped.")
