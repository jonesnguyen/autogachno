#!/usr/bin/env python3
"""
Test Mock API đơn giản
"""

import requests

def test_mock_api():
    """Test mock API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🚀 Testing Mock API endpoints...")
    print(f"📍 Base URL: {base_url}")
    print()
    
    # Test 1: Mock API info
    print("1️⃣ Testing /api/mock/test...")
    try:
        response = requests.get(f"{base_url}/api/mock/test")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content Length: {len(response.text)}")
        print(f"   First 100 chars: {response.text[:100]}")
        
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   ✅ JSON Response: {data}")
            except:
                print(f"   ❌ Not valid JSON")
        else:
            print(f"   ⚠️ Not JSON response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: List bill not completed
    print("2️⃣ Testing /api/list-bill-not-completed...")
    try:
        response = requests.get(f"{base_url}/api/list-bill-not-completed?service_type=check_ftth")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content Length: {len(response.text)}")
        print(f"   First 100 chars: {response.text[:100]}")
        
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   ✅ JSON Response: {data}")
            except:
                print(f"   ❌ Not valid JSON")
        else:
            print(f"   ⚠️ Not JSON response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Proxy API (để so sánh)
    print("3️⃣ Testing /api/proxy/test (for comparison)...")
    try:
        response = requests.get(f"{base_url}/api/proxy/test")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content Length: {len(response.text)}")
        
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   ✅ JSON Response: {data}")
            except:
                print(f"   ❌ Not valid JSON")
        else:
            print(f"   ⚠️ Not JSON response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_mock_api()
