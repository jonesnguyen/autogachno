#!/usr/bin/env python3
"""
Test API thuhohpk.com để debug vấn đề CORS và network
Chạy: python test_api.py
"""

import requests
import json
from datetime import datetime

def test_api_endpoint():
    """Test API endpoint với các service types khác nhau"""
    
    # Base URL
    base_url = "https://thuhohpk.com/api/list-bill-not-completed"
    
    # Basic Authentication từ Postman collection
    import base64
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Service types mapping
    service_types = {
        'tra_cuu_ftth': 'check_ftth',
        'gach_dien_evn': 'env',
        'nap_tien_da_mang': 'deposit',
        'nap_tien_viettel': 'deposit_viettel',
        'thanh_toan_tv_internet': 'payment_tv',
        'tra_cuu_no_tra_sau': 'check_debt'
    }
    
    print(f"🔄 Testing API: {base_url}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔐 Auth: Basic {username}:{password}")
    print("=" * 60)
    
    for service_name, api_service_type in service_types.items():
        print(f"\n📡 Testing: {service_name} -> {api_service_type}")
        
        try:
            # Test với params
            params = {'service_type': api_service_type}
            response = requests.get(
                base_url, 
                params=params, 
                headers=headers, 
                timeout=30
            )
            
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # Kiểm tra format dữ liệu
                    if isinstance(data, dict) and 'data' in data:
                        if isinstance(data['data'], str):
                            codes = data['data'].split(',')
                            print(f"🔢 Codes count: {len(codes)}")
                            print(f"📝 Sample codes: {codes[:3]}")
                        elif isinstance(data['data'], list):
                            print(f"🔢 Array length: {len(data['data'])}")
                            print(f"📝 Sample items: {data['data'][:3]}")
                    elif isinstance(data, list):
                        print(f"🔢 Array length: {len(data)}")
                        print(f"📝 Sample items: {data[:3]}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"📄 Raw response: {response.text[:200]}...")
                    
            else:
                print(f"❌ Error response: {response.text}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout error - API không phản hồi trong 30 giây")
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 Connection error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            
        print("-" * 40)

def test_cors_headers():
    """Test CORS headers"""
    print(f"\n🌐 Testing CORS headers...")
    
    try:
        # Test OPTIONS request (preflight)
        response = requests.options(
            "https://thuhohpk.com/api/list-bill-not-completed",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Token,Content-Type'
            },
            timeout=10
        )
        
        print(f"OPTIONS Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        
    except Exception as e:
        print(f"CORS test error: {e}")

def test_network_connectivity():
    """Test network connectivity cơ bản"""
    print(f"\n🌍 Testing network connectivity...")
    
    try:
        # Test DNS resolution
        import socket
        host = "thuhohpk.com"
        ip = socket.gethostbyname(host)
        print(f"✅ DNS resolution: {host} -> {ip}")
        
        # Test basic connectivity
        response = requests.get("https://thuhohpk.com", timeout=10)
        print(f"✅ Basic connectivity: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Network test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting API test...")
    
    # Test network connectivity trước
    test_network_connectivity()
    
    # Test CORS headers
    test_cors_headers()
    
    # Test API endpoints
    test_api_endpoint()
    
    print("\n✨ Test completed!")
    print("\n💡 Tips:")
    print("- Nếu có lỗi CORS: API server không cho phép cross-origin requests")
    print("- Nếu có lỗi network: Kiểm tra firewall, proxy, hoặc server down")
    print("- Nếu có lỗi timeout: Server quá tải hoặc network chậm")
    print("- Nếu có lỗi auth: Token không hợp lệ hoặc hết hạn")
