#!/usr/bin/env python3
"""
Test Direct API thuhohpk.com
Test API trực tiếp không qua proxy
"""

import requests
import json
import base64
from datetime import datetime

# Cấu hình
BASE_URL = "https://thuhohpk.com"
USERNAME = "Demodiemthu"
PASSWORD = "123456"
CREDENTIALS = f"{USERNAME}:{PASSWORD}"

# Service types mapping
SERVICE_TYPES = {
    'tra_cuu_ftth': 'check_ftth',
    'gach_dien_evn': 'env', 
    'nap_tien_da_mang': 'deposit',
    'nap_tien_viettel': 'deposit_viettel',
    'thanh_toan_tv_internet': 'payment_tv',
    'tra_cuu_no_tra_sau': 'check_debt'
}

def test_api_directly(service_type, api_service_type):
    """Test API trực tiếp cho một service"""
    print(f"\n🔍 Testing: {service_type} -> {api_service_type}")
    
    try:
        url = f"{BASE_URL}/api/list-bill-not-completed?service_type={api_service_type}"
        print(f"🌐 URL: {url}")
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(CREDENTIALS.encode()).decode()}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
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
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Direct API Test...")
    print(f"📍 Target: {BASE_URL}")
    print(f"🔐 Credentials: {USERNAME}:{PASSWORD}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test tất cả services
    results = {}
    
    for service_type, api_service_type in SERVICE_TYPES.items():
        print(f"{'='*50}")
        success = test_api_directly(service_type, api_service_type)
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
    
    print("\n💡 Usage:")
    print(f"  - API Base: {BASE_URL}/api/list-bill-not-completed")
    print(f"  - Service types: {', '.join(SERVICE_TYPES.values())}")
    print(f"  - Example: {BASE_URL}/api/list-bill-not-completed?service_type=check_ftth")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()
