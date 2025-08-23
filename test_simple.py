#!/usr/bin/env python3
"""
Test đơn giản API thuhohpk.com
Chạy: python test_simple.py
"""

import requests
import base64

def test_simple():
    """Test đơn giản nhất có thể"""
    
    print("🚀 Testing API thuhohpk.com...")
    
    # Basic Authentication từ Postman collection
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    # Test 1: Basic connectivity
    try:
        print("\n1️⃣ Testing basic connectivity...")
        response = requests.get("https://thuhohpk.com", timeout=10)
        print(f"✅ Basic connect: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic connect failed: {e}")
    
    # Test 2: API endpoint với service_type=deposit
    try:
        print("\n2️⃣ Testing API endpoint...")
        url = "https://thuhohpk.com/api/list-bill-not-completed"
        params = {"service_type": "deposit"}
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"✅ API Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📄 Response Data: {data}")
            except:
                print(f"📄 Raw Response: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print(f"💡 Error type: {type(e).__name__}")
    
    # Test 3: CORS test (không cần Origin header)
    try:
        print("\n3️⃣ Testing CORS...")
        response = requests.options(
            "https://thuhohpk.com/api/list-bill-not-completed",
            headers={
                "Access-Control-Request-Method": "GET"
            },
            timeout=10
        )
        print(f"✅ CORS Status: {response.status_code}")
        print(f"📊 CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

if __name__ == "__main__":
    test_simple()
    print("\n✨ Test completed!")
