#!/usr/bin/env python3
"""
Test Internal Proxy API
Test API nội bộ proxy server để gọi thuhohpk.com
"""

import requests
import json
from datetime import datetime

# Cấu hình
BASE_URL = "http://localhost:5000"  # Server nội bộ
PROXY_ENDPOINT = "/api/proxy/thuhohpk"

# Service types mapping (giống như trong proxy.ts)
SERVICE_TYPES = {
    'tra_cuu_ftth': 'check_ftth',
    'gach_dien_evn': 'env', 
    'nap_tien_da_mang': 'deposit',
    'nap_tien_viettel': 'deposit_viettel',
    'thanh_toan_tv_internet': 'payment_tv',
    'tra_cuu_no_tra_sau': 'check_debt'
}

def test_proxy_health():
    """Test health check endpoint"""
    print("🏥 Testing proxy health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/proxy/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_proxy_info():
    """Test proxy info endpoint"""
    print("\n📋 Testing proxy info...")
    try:
        response = requests.get(f"{BASE_URL}/api/proxy/test", timeout=10)
        print(f"✅ Info check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Info check failed: {e}")
        return False

def test_proxy_service(service_type):
    """Test proxy cho một service cụ thể"""
    print(f"\n🔍 Testing proxy for service: {service_type}")
    
    try:
        url = f"{BASE_URL}{PROXY_ENDPOINT}/{service_type}"
        print(f"🌐 URL: {url}")
        
        response = requests.get(url, timeout=30)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Parse data giống như trong ServiceContent.tsx
            if data.get('data') and data['data'].get('data'):
                api_data = data['data']['data']
                if isinstance(api_data, str):
                    codes = api_data.split(",")
                    codes = [c.strip() for c in codes if c.strip()]
                    print(f"🔢 Codes count: {len(codes)}")
                    print(f"📝 Sample codes: {codes[:3]}")
                else:
                    print(f"📄 Data type: {type(api_data)}")
                    print(f"📄 Data: {api_data}")
            else:
                print("⚠️ No data in response")
                
        else:
            print(f"❌ Error response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
        return False

def test_all_services():
    """Test tất cả services"""
    print("\n" + "="*60)
    print("🚀 Testing all services via internal proxy...")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print("="*60)
    
    # Test health check trước
    if not test_proxy_health():
        print("❌ Proxy server không hoạt động!")
        return False
    
    if not test_proxy_info():
        print("❌ Proxy info không hoạt động!")
        return False
    
    # Test từng service
    results = {}
    for service_type in SERVICE_TYPES.keys():
        print(f"\n{'='*50}")
        print(f"📡 Testing: {service_type} -> {SERVICE_TYPES[service_type]}")
        print(f"{'='*50}")
        
        success = test_proxy_service(service_type)
        results[service_type] = success
        
        if success:
            print(f"✅ {service_type}: SUCCESS")
        else:
            print(f"❌ {service_type}: FAILED")
    
    # Tổng kết
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for service_type, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{service_type:25} -> {status}")
    
    print(f"\n🎯 Overall: {success_count}/{total_count} services working")
    
    if success_count == total_count:
        print("🎉 All services working perfectly!")
    elif success_count > 0:
        print("⚠️ Some services working, some failed")
    else:
        print("💥 All services failed!")
    
    return success_count > 0

def test_direct_vs_proxy():
    """So sánh direct call vs proxy call"""
    print("\n" + "="*60)
    print("🔍 COMPARISON: Direct vs Proxy")
    print("="*60)
    
    service_type = "nap_tien_da_mang"  # Test với service này
    
    # Test direct call (sẽ fail vì HTTP/2 issues)
    print(f"\n📡 Direct call to thuhohpk.com...")
    try:
        direct_url = f"https://thuhohpk.com/api/list-bill-not-completed?service_type=deposit"
        headers = {
            'Authorization': 'Basic RGVtb2RpZW10aHU6MTIzNDU2',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(direct_url, headers=headers, timeout=30)
        print(f"✅ Direct call: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Direct data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Direct call failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Direct call error: {e}")
    
    # Test proxy call
    print(f"\n📡 Proxy call via internal server...")
    try:
        proxy_url = f"{BASE_URL}/api/proxy/thuhohpk/{service_type}"
        response = requests.get(proxy_url, timeout=30)
        print(f"✅ Proxy call: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Proxy data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Proxy call failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Proxy call error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Internal Proxy API Test...")
    print(f"📍 Target: {BASE_URL}")
    print(f"🔐 Credentials: Demodiemthu:123456")
    print(f"🌐 External API: https://thuhohpk.com")
    print()
    
    try:
        # Test chính
        success = test_all_services()
        
        if success:
            # So sánh direct vs proxy
            test_direct_vs_proxy()
        
        print("\n✨ Test completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
    
    print("\n💡 Tips:")
    print("- Đảm bảo server đang chạy trên localhost:5000")
    print("- Kiểm tra console server để xem proxy logs")
    print("- Nếu proxy fail, kiểm tra network và firewall")
