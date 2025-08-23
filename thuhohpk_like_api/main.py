from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import base64
import requests
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Token for authentication
VALID_TOKEN = "c0d2e27448f511b41dd1477781025053"

# External API configuration
EXTERNAL_API_BASE = "https://thuhohpk.com/api"
EXTERNAL_TOKEN = "c0d2e27448f511b41dd1477781025053"



def verify_token(f):
    """Decorator to verify token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Token')
        if not token or token != VALID_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/list-bill-not-completed', methods=['GET'])
@verify_token
def list_bill_not_completed():
    """
    Endpoint to get list of bills not completed
    This endpoint proxies the request to https://thuhohpk.com/api/list-bill-not-completed
    
    Optional query parameter: service_type
    Authentication via headers:
    - X-Username: username for external API
    - X-Password: password for external API
    """
    
    # Get authentication from headers
    username = request.headers.get('X-Username')
    password = request.headers.get('X-Password')
    
    # Validate credentials
    if not username or not password:
        return jsonify({
            "error": "Missing credentials",
            "message": "X-Username and X-Password headers are required"
        }), 400
    
    print(f"🔐 Using credentials from headers: {username}:{password[:3]}***")
    
    # Get query parameters
    service_type = request.args.get('service_type')
    
    # Build parameters for external API
    params = {}
    if service_type:
        params['service_type'] = service_type
    
    # Call external API with credentials from headers
    print(f"Calling external API: {EXTERNAL_API_BASE}/list-bill-not-completed with params: {params}")
    
    api_response = call_external_api('list-bill-not-completed', username, password, method='GET', params=params)
    
    # Log chi tiết api_response
    print("=" * 50)
    print("📡 API RESPONSE DETAILS:")
    print(f"   Success: {api_response.get('success')}")
    print(f"   Status Code: {api_response.get('status_code', 'N/A')}")
    print(f"   Error: {api_response.get('error', 'None')}")
    
    if 'data' in api_response:
        print(f"   Data Type: {type(api_response['data'])}")
        if isinstance(api_response['data'], dict):
            print(f"   Data Keys: {list(api_response['data'].keys())}")
            print(f"   Data Content: {api_response['data']}")
        elif isinstance(api_response['data'], str):
            print(f"   Data Length: {len(api_response['data'])}")
            print(f"   Data Preview: {api_response['data'][:200]}...")
        else:
            print(f"   Data: {api_response['data']}")
    
    if 'headers' in api_response:
        print(f"   Response Headers: {api_response['headers']}")
    
    print("=" * 50)
    
    if api_response['success']:
        # Successfully got response from external API
        print(f"External API response status: {api_response['status_code']}")
        
        if api_response['status_code'] == 200:
            # Return the external API response
            return jsonify({
                "source": "external_api",
                "external_status": api_response['status_code'],
                "credentials_used": f"{username}:***",
                **api_response['data']  # Spread the external API response
            })
        else:
            # External API returned error status
            return jsonify({
                "source": "external_api_error",
                "external_status": api_response['status_code'],
                "external_response": api_response['data'],
                "credentials_used": f"{username}:***",
                "error": f"External API returned status {api_response['status_code']}"
            }), api_response['status_code']
    
    else:
        # External API call failed, return error
        print(f"External API failed: {api_response['error']}")
        return jsonify({
            "source": "external_api_failed",
            "error": "Failed to connect to external API",
            "external_api_error": api_response['error'],
            "credentials_used": f"{username}:***"
        }), 503

def call_external_api(endpoint, username, password, method='GET', params=None, data=None):
    """
    Helper function to call external API
    Uses credentials provided as parameters
    """
    url = f"{EXTERNAL_API_BASE}/{endpoint}"
    headers = {
        'Token': EXTERNAL_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Use credentials passed as parameters
    auth = (username, password)
    
    print(f"🔐 Calling external API with credentials: {username}:{password[:3]}***")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, auth=auth, params=params, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, auth=auth, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Log raw response details
        print(f"🌐 Raw External API Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content Type: {response.headers.get('content-type', 'unknown')}")
        
        # Parse response data
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"   JSON Data: {response_data}")
        else:
            response_data = response.text
            print(f"   Text Data Length: {len(response_data)}")
            print(f"   Text Data Preview: {response_data[:200]}...")
        
        # Return response data
        return {
            'success': True,
            'status_code': response.status_code,
            'data': response_data,
            'headers': dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'fallback_available': False
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}",
            'fallback_available': False
        }



@app.route('/api/tool-bill-completed', methods=['POST'])
@verify_token
def tool_bill_completed():
    """
    Endpoint to mark bill as completed
    This endpoint proxies the request to https://thuhohpk.com/api/tool-bill-completed
    
    Expects JSON body with 'account' field
    Authentication via headers:
    - X-Username: username for external API
    - X-Password: password for external API
    """
    
    try:
        # Get authentication from headers
        username = request.headers.get('X-Username')
        password = request.headers.get('X-Password')
        
        # Validate credentials
        if not username or not password:
            return jsonify({
                "error": "Missing credentials",
                "message": "X-Username and X-Password headers are required"
            }), 400
        
        print(f"🔐 Using credentials from headers: {username}:{password[:3]}***")
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'account' not in data:
            return jsonify({"error": "Account number is required"}), 400
        
        account = data['account']
        
        print(f"Calling external API: {EXTERNAL_API_BASE}/tool-bill-completed with account: {account}")
        
        # Call external API with credentials from headers
        api_response = call_external_api('tool-bill-completed', username, password, method='POST', data=data)
        
        # Log chi tiết api_response
        print("=" * 50)
        print("📡 TOOL BILL COMPLETED API RESPONSE:")
        print(f"   Success: {api_response.get('success')}")
        print(f"   Status Code: {api_response.get('status_code', 'N/A')}")
        print(f"   Error: {api_response.get('error', 'None')}")
        print(f"   Fallback Available: {api_response.get('fallback_available', 'N/A')}")
        
        if 'data' in api_response:
            print(f"   Data Type: {type(api_response['data'])}")
            if isinstance(api_response['data'], dict):
                print(f"   Data Keys: {list(api_response['data'].keys())}")
                print(f"   Data Content: {api_response['data']}")
            elif isinstance(api_response['data'], str):
                print(f"   Data Length: {len(api_response['data'])}")
                print(f"   Data Preview: {api_response['data'][:200]}...")
            else:
                print(f"   Data: {api_response['data']}")
        
        if 'headers' in api_response:
            print(f"   Response Headers: {api_response['headers']}")
        
        print("=" * 50)
        
        if api_response['success']:
            # Successfully got response from external API
            print(f"External API response status: {api_response['status_code']}")
            
            if api_response['status_code'] == 200:
                # Return the external API response
                return jsonify({
                    "source": "external_api",
                    "external_status": api_response['status_code'],
                    "credentials_used": f"{username}:***",
                    **api_response['data']  # Spread the external API response
                })
            else:
                # External API returned error status
                return jsonify({
                    "source": "external_api_error",
                    "external_status": api_response['status_code'],
                    "external_response": api_response['data'],
                    "credentials_used": f"{username}:***",
                    "error": f"External API returned status {api_response['status_code']}"
                }), api_response['status_code']
        
        else:
            # External API call failed, return error
            print(f"External API failed: {api_response['error']}")
            return jsonify({
                "source": "external_api_failed", 
                "error": "Failed to connect to external API",
                "external_api_error": api_response['error'],
                "credentials_used": f"{username}:***"
            }), 503
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "App Vien Thong API Proxy",
        "version": "1.1.0",
        "external_api": EXTERNAL_API_BASE
    })

@app.route('/api/test-external', methods=['GET'])
@verify_token
def test_external_connection():
    """Test endpoint to check external API connectivity
    Authentication via headers:
    - X-Username: username for external API
    - X-Password: password for external API
    """
    
    # Get authentication from headers
    username = request.headers.get('X-Username')
    password = request.headers.get('X-Password')
    
    # Validate credentials
    if not username or not password:
        return jsonify({
            "error": "Missing credentials",
            "message": "X-Username and X-Password headers are required"
        }), 400
    
    print(f"🔐 Testing external API with credentials: {username}:{password[:3]}***")
    
    # Call external API with credentials from headers
    api_response = call_external_api('list-bill-not-completed', username, password, method='GET')
    
    # Log chi tiết api_response
    print("=" * 50)
    print("📡 TEST EXTERNAL CONNECTION API RESPONSE:")
    print(f"   Success: {api_response.get('success')}")
    print(f"   Status Code: {api_response.get('status_code', 'N/A')}")
    print(f"   Error: {api_response.get('error', 'None')}")
    print(f"   Fallback Available: {api_response.get('fallback_available', 'N/A')}")
    
    if 'data' in api_response:
        print(f"   Data Type: {type(api_response['data'])}")
        if isinstance(api_response['data'], dict):
            print(f"   Data Keys: {list(api_response['data'].keys())}")
            print(f"   Data Content: {api_response['data']}")
        elif isinstance(api_response['data'], str):
            print(f"   Data Length: {len(api_response['data'])}")
            print(f"   Data Preview: {api_response['data'][:200]}...")
        else:
            print(f"   Data: {api_response['data']}")
    
    if 'headers' in api_response:
        print(f"   Response Headers: {api_response['headers']}")
    
    print("=" * 50)
    
    return jsonify({
        "external_api_url": EXTERNAL_API_BASE,
        "connection_test": api_response,
        "credentials_used": f"{username}:***",
        "timestamp": "2024-08-19"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("Starting App Vien Thong API Proxy Server...")
    print(f"Proxying to external API: {EXTERNAL_API_BASE}")
    print("Available endpoints:")
    print("- GET  /api/list-bill-not-completed (proxies to external API)")
    print("- POST /api/tool-bill-completed (proxies to external API)")
    print("- GET  /api/test-external (test external API connection)")
    print("- GET  /health")
    print("\nAuthentication required:")
    print(f"- Token header: {VALID_TOKEN}")
    print("- X-Username header: username for external API")
    print("- X-Password header: password for external API")
    print("\nNote: Credentials are passed via headers for each request")
    print("      This allows dynamic authentication per request")
    print("Note: If external API fails, system will return error response")
    
    app.run(debug=True, host='0.0.0.0', port=3000)