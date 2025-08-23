#!/usr/bin/env python3
"""
Server-side API proxy để bypass browser CORS issues
Chạy: python server_api_proxy.py
"""

import requests
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Basic Authentication credentials
USERNAME = "Demodiemthu"
PASSWORD = "123456"
CREDENTIALS = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()

# Service types mapping
SERVICE_TYPES = {
    'tra_cuu_ftth': 'check_ftth',
    'gach_dien_evn': 'env',
    'nap_tien_da_mang': 'deposit',
    'nap_tien_viettel': 'deposit_viettel',
    'thanh_toan_tv_internet': 'payment_tv',
    'tra_cuu_no_tra_sau': 'check_debt'
}

def call_thuhohpk_api(service_type):
    """Gọi API thuhohpk.com từ server side"""
    try:
        api_service_type = SERVICE_TYPES.get(service_type, service_type)
        url = f"https://thuhohpk.com/api/list-bill-not-completed?service_type={api_service_type}"
        
        headers = {
            'Authorization': f'Basic {CREDENTIALS}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"🚀 Calling API: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"✅ Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Data: {data}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        print(f"💥 Exception: {e}")
        return {"error": str(e)}

@app.route('/api/proxy/thuhohpk/<service_type>', methods=['GET'])
def proxy_api(service_type):
    """Proxy endpoint để gọi API thuhohpk.com"""
    try:
        print(f"📡 Proxy request for service: {service_type}")
        
        # Gọi API external
        result = call_thuhohpk_api(service_type)
        
        return jsonify({
            "status": "success",
            "service_type": service_type,
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Proxy error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/proxy/test', methods=['GET'])
def test_proxy():
    """Test endpoint để kiểm tra proxy hoạt động"""
    return jsonify({
        "status": "success",
        "message": "Proxy server is running",
        "timestamp": datetime.now().isoformat(),
        "available_services": list(SERVICE_TYPES.keys())
    })

@app.route('/api/proxy/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting API Proxy Server...")
    print(f"🔐 Credentials: {USERNAME}:{PASSWORD}")
    print(f"📡 Available services: {list(SERVICE_TYPES.keys())}")
    print("🌐 Server will run on http://localhost:5000")
    print("📋 Usage:")
    print("  - GET /api/proxy/test - Test proxy")
    print("  - GET /api/proxy/health - Health check")
    print("  - GET /api/proxy/thuhohpk/{service_type} - Call external API")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
