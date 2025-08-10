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
