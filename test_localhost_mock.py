#!/usr/bin/env python3
"""
Test Localhost Mock API
Test API mock tương tự thuhohpk.com trên localhost:3000
"""

import requests
import json
from datetime import datetime

# Cấu hình
BASE_URL = "http://localhost:3000"

# Service types mapping
SERVICE_TYPES = {
    'tra_cuu_ftth': 'check_ftth',
    'gach_dien_evn': 'env', 
    'nap_tien_da_mang': 'deposit',
    'nap_tien_viettel': 'deposit_viettel',
    'thanh_toan_tv_internet': 'payment_tv',
    'tra_cuu_no_tra_sau': 'check_debt'
}

def test_flask_api_info():
    """Test Flask API info"""
    print("📋 Testing Flask API info...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_flask_api_service(service_type, api_service_type):
    """Test Flask API cho một service"""
    print(f"\n🔍 Testing: {service_type} -> {api_service_type}")
    
    try:
        url = f"{BASE_URL}/api/list-bill-not-completed?service_type={api_service_type}"
        print(f"🌐 URL: {url}")
        
        # Flask API yêu cầu cả Token và Basic Auth
        headers = {
            'Token': 'c0d2e27448f511b41dd1477781025053',
            'Authorization': 'Basic RGVtb2RpZW10aHU6MTIzNDU2'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Parse data
            if data.get('data'):
                api_data = data['data']
                if isinstance(api_data, str):
                    codes = api_data.split(",")
                    codes = [c.strip() for c in codes if c.strip()]
                    print(f"🔢 Codes count: {len(codes)}")
                    if codes:
                        print(f"📝 Sample codes: {codes[:3]}")
                    else:
                        print("⚠️ No codes found")
                else:
                    print(f"📄 Data type: {type(api_data)}")
                    print(f"📄 Data: {api_data}")
            else:
                print("⚠️ No data in response")
                
            return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Flask API test failed: {e}")
        return False

def test_flask_bill_completed():
    """Test POST /api/tool-bill-completed"""
    print(f"\n🔍 Testing POST /api/tool-bill-completed")
    
    try:
        url = f"{BASE_URL}/api/tool-bill-completed"
        print(f"🌐 URL: {url}")
        
        payload = {
            "account": "0912345678"
        }
        
        headers = {
            'Token': 'c0d2e27448f511b41dd1477781025053',
            'Authorization': 'Basic RGVtb2RpZW10aHU6MTIzNDU2'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Flask bill-completed test failed: {e}")
        return False

def main():
    """Main function"""
    print("�� Starting Localhost Flask API Test...")
    print(f"📍 Target: {BASE_URL}")
    print(f"🌐 Flask API tương tự: https://thuhohpk.com")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test info trước
    if not test_flask_api_info():
        print("❌ Flask API không hoạt động!")
        return
    
    # Test tất cả services
    results = {}
    
    for service_type, api_service_type in SERVICE_TYPES.items():
        print(f"{'='*50}")
        success = test_flask_api_service(service_type, api_service_type)
        results[service_type] = success
        
        if success:
            print(f"✅ {service_type}: SUCCESS")
        else:
            print(f"❌ {service_type}: FAILED")
    
    # Test bill-completed
    print(f"\n{'='*50}")
    bill_success = test_flask_bill_completed()
    if bill_success:
        print("✅ bill-completed: SUCCESS")
    else:
        print("❌ bill-completed: FAILED")
    
    # Tổng kết
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for service_type, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{service_type:25} -> {status}")
    
    print(f"bill-completed{'':20} -> {'✅ SUCCESS' if bill_success else '❌ FAILED'}")
    
    print(f"\n🎯 Overall: {success_count}/{total_count} services working + bill-completed: {'✅' if bill_success else '❌'}")
    
    if success_count == total_count and bill_success:
        print("🎉 All endpoints working perfectly!")
    elif success_count > 0:
        print("⚠️ Some endpoints working, some failed")
    else:
        print("💥 All endpoints failed!")
    
    print("\n💡 Usage:")
    print(f"  - Flask API Base: {BASE_URL}/api/list-bill-not-completed")
    print(f"  - Service types: {', '.join(SERVICE_TYPES.values())}")
    print(f"  - Example: {BASE_URL}/api/list-bill-not-completed?service_type=check_ftth")
    print(f"  - Bill completed: {BASE_URL}/api/tool-bill-completed")
    print(f"  - Health check: {BASE_URL}/health")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()
