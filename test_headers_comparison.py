#!/usr/bin/env python3
"""
Test và so sánh headers giữa Python và React
Chạy: python test_headers_comparison.py
"""

import requests
import base64
import json
from datetime import datetime

def test_python_headers():
    """Test Python headers giống hệt đang dùng"""
    
    # Basic Authentication
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    # Headers giống hệt Python script hiện tại
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🔐 Python Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    # Test API call
    url = "https://thuhohpk.com/api/list-bill-not-completed?service_type=check_ftth"
    
    try:
        print(f"\n🚀 Testing Python API call...")
        print(f"📡 URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📄 Response Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"📄 Raw Response: {response.text[:200]}...")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Python Error: {e}")

def test_react_equivalent():
    """Test headers tương đương với React"""
    
    # Headers mà React sẽ gửi
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    # Headers giống React (đã cập nhật)
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"\n🌐 React Equivalent Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    # Test với các User-Agent khác nhau
    user_agents = [
        'Mozilla/5.0',  # React cũ
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',  # React mới
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'  # Chrome thật
    ]
    
    url = "https://thuhohpk.com/api/list-bill-not-completed?service_type=check_ftth"
    
    for i, user_agent in enumerate(user_agents, 1):
        print(f"\n🧪 Test {i}: User-Agent = {user_agent}")
        
        test_headers = headers.copy()
        test_headers['User-Agent'] = user_agent
        
        try:
            response = requests.get(url, headers=test_headers, timeout=30)
            print(f"  ✅ Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  📄 Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    print(f"  📄 Raw: {response.text[:100]}...")
            else:
                print(f"  ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"  💥 Error: {e}")

def test_http2_compatibility():
    """Test HTTP/2 compatibility issues"""
    
    print(f"\n🔍 Testing HTTP/2 Compatibility...")
    
    # Test với requests session
    session = requests.Session()
    
    # Force HTTP/1.1
    session.headers.update({
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://thuhohpk.com/api/list-bill-not-completed?service_type=check_ftth"
    
    try:
        print(f"📡 Testing với HTTP/1.1 session...")
        response = session.get(url, headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Protocol: {response.raw.version}")
        
    except Exception as e:
        print(f"💥 HTTP/1.1 Error: {e}")

def test_curl_equivalent():
    """Test tương đương với curl command"""
    
    print(f"\n🔄 Testing cURL equivalent...")
    
    username = "Demodiemthu"
    password = "123456"
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://thuhohpk.com/api/list-bill-not-completed?service_type=check_ftth"
    
    # Tạo cURL command
    curl_cmd = f'curl -H "Authorization: Basic {credentials}" -H "Content-Type: application/json" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "{url}"'
    
    print(f"📋 cURL Command:")
    print(f"  {curl_cmd}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✅ Python equivalent status: {response.status_code}")
        
    except Exception as e:
        print(f"💥 Python equivalent error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Headers Comparison Test...")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test Python headers hiện tại
    test_python_headers()
    
    # Test React equivalent
    test_react_equivalent()
    
    # Test HTTP/2 compatibility
    test_http2_compatibility()
    
    # Test cURL equivalent
    test_curl_equivalent()
    
    print("\n✨ Test completed!")
    print("\n💡 Tips:")
    print("- Nếu Python hoạt động nhưng React không → HTTP/2 protocol issue")
    print("- Nếu User-Agent khác nhau → Server có thể reject")
    print("- Nếu headers khác nhau → Authentication issue")
    print("- Nếu protocol khác nhau → HTTP/1.1 vs HTTP/2 compatibility")
