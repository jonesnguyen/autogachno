from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import base64
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Token for authentication
VALID_TOKEN = "c0d2e27448f511b41dd1477781025053"

# Basic auth credentials
BASIC_AUTH = {
    "username": "Demodiemthu",
    "password": "123456"
}

# Mock data for demonstration
MOCK_BILLS = {
    'check_ftth': [
        "t074_gftth_kendt0", "t074_gftth_vudm1", "t074_gmts2_depdt4", 
        "t074_gftth_depdt9", "t074_gmts2_thidv1"
    ],
    'env': [
        "PB160400171832238", "PB160400350158571", "PB160400201958951", 
        "PB1604003045210714", "PB1604001462210714", "PB1604003181410714"
    ],
    'deposit': [
        "0912345618", "0912345619", "0912345620", "0912345621", 
        "0912345622", "0912345623", "0912345624", "0912345625"
    ],
    'deposit_viettel': [
        "0912345618", "0912345619", "0912345620", "0912345621", 
        "0912345622", "0912345623", "0912345624", "0912345625"
    ],
    'payment_tv': [
        "0912345618", "0912345619", "0912345620", "0912345621", 
        "0912345622", "0912345623", "0912345624", "0912345625"
    ],
    'check_debt': [
        "0981131368", "986038917", "987085348", "986849207", 
        "985955970", "986864104", "986322569", "985842989", "986038917"
    ]
}

def verify_token(f):
    """Decorator to verify token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Token')
        if not token or token != VALID_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated_function

def verify_basic_auth(f):
    """Decorator to verify basic authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != BASIC_AUTH["username"] or auth.password != BASIC_AUTH["password"]:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/list-bill-not-completed', methods=['GET'])
@verify_token
@verify_basic_auth
def list_bill_not_completed():
    """
    Endpoint to get list of bills not completed
    Optional query parameter: service_type
    Available service types:
    - check_ftth: Tra cứu FTTH (t074_gftth_...)
    - env: Gạch điện EVN (PB160400...)
    - deposit: Nạp tiền đa mạng (09...)
    - deposit_viettel: Nạp tiền mạng Viettel (09...)
    - payment_tv: Thanh toán TV - Internet (09...)
    - check_debt: Tra cứu nợ thuê bao trả sau (09...)
    """
    
    service_type = request.args.get('service_type', 'all')
    
    # Get bills based on service type
    if service_type == 'all' or not service_type:
        # Return all bills from all services
        all_bills = []
        for bills in MOCK_BILLS.values():
            all_bills.extend(bills)
        bills = all_bills
    else:
        # Get bills for specific service type
        bills = MOCK_BILLS.get(service_type, [])
        if not bills:
            return jsonify({
                "error": f"Invalid service_type: {service_type}. Valid types: {list(MOCK_BILLS.keys())}"
            }), 400
    
    # Format response as comma-separated string
    data = ",".join(bills)
    
    return jsonify({
        "data": data,
        "service_type": service_type,
        "total_bills": len(bills),
        "sample_bills": bills[:3] if bills else []  # Show first 3 bills as sample
    })

@app.route('/api/tool-bill-completed', methods=['POST'])
@verify_token
@verify_basic_auth
def tool_bill_completed():
    """
    Endpoint to mark bill as completed
    Expects JSON body with 'account' field
    """
    
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'account' not in data:
            return jsonify({"error": "Account number is required"}), 400
        
        account = data['account']
        
        # Mock processing - in real implementation, this would update database
        # For demo, we'll return the same account repeated 12 times (like original thuhohpk.com)
        result_accounts = [account] * 12
        result_data = ",".join(result_accounts)
        
        return jsonify({
            "data": result_data,
            "account_processed": account,
            "status": "completed",
            "message": f"Bill for account {account} marked as completed",
            "total_processed": len(result_accounts)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "App Vien Thong API",
        "version": "1.0.0"
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
    print("Starting App Vien Thong API Server...")
    print("Available endpoints:")
    print("- GET  /api/list-bill-not-completed")
    print("- POST /api/tool-bill-completed")
    print("- GET  /health")
    print("\nAuthentication required:")
    print(f"- Token header: {VALID_TOKEN}")
    print(f"- Basic Auth: {BASIC_AUTH['username']}:{BASIC_AUTH['password']}")
    print("\nSample data for each service:")
    for service_type, bills in MOCK_BILLS.items():
        print(f"- {service_type}: {len(bills)} bills (e.g., {bills[0] if bills else 'N/A'})")
    
    app.run(debug=True, host='0.0.0.0', port=3000)