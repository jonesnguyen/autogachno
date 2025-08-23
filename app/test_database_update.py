#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test đơn giản: đăng nhập dev -> tạo order -> callback từng code cho 6 dịch vụ
Không import main.py, gọi trực tiếp Node API để tránh phụ thuộc vào Selenium/Python app.
"""

import os
import json
import requests
from typing import List, Dict

BASE_URL = os.getenv("NODE_SERVER_URL", "http://127.0.0.1:5000")

SERVICE_MAP = {
    "Tra cứu FTTH": "tra_cuu_ftth",
    "Tra cứu trả sau": "tra_cuu_no_tra_sau",
    "TV-Internet": "thanh_toan_tv_internet",
    "Gạch điện EVN": "gach_dien_evn",
    "Nạp tiền đa mạng": "nap_tien_da_mang",
    "Nạp tiền Viettel": "nap_tien_viettel",
}

def dev_login(sess: requests.Session) -> None:
    # SKIP_AUTH=1 đã bật => có /api/dev/login
    r = sess.post(f"{BASE_URL}/api/dev/login", json={"email": "Demodiemthu", "password": "123456"}, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Dev login failed: {r.status_code} {r.text}")

def create_order(sess: requests.Session, service_type: str, codes: List[str]) -> str:
    # /api/orders yêu cầu auth; sess đã có cookie sau dev_login
    payload = {
        "serviceType": service_type,
        "inputData": json.dumps({"codes": codes}, ensure_ascii=False),
        # "totalAmount": "0.00"  # tùy chọn
    }
    r = sess.post(f"{BASE_URL}/api/orders", json=payload, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"Create order failed: {r.status_code} {r.text}")
    order = r.json()
    return order["id"]

def callback(sess: requests.Session, order_id: str, code: str, status: str, amount: int | None, notes: str, data: Dict | None = None) -> bool:
    payload = {
        "orderId": order_id,
        "code": code,
        "status": status,
        "amount": str(amount) if isinstance(amount, (int, float)) else None,
        "notes": notes,
    }
    if data:
        payload["data"] = data
    r = sess.post(f"{BASE_URL}/api/automation/callback", json=payload, timeout=10)
    return r.status_code == 200

def test_service(sess: requests.Session, label: str, codes: List[str], amount_each: int | None, notes: str, data_builder=None):
    print(f"\n🔍 [TEST] {label}")
    print("=" * 50)
    service_type = SERVICE_MAP[label]
    order_id = create_order(sess, service_type, codes)
    print(f"📋 Order ID: {order_id}")
    print(f"📱 Số mã: {len(codes)}")

    results = []
    for i, code in enumerate(codes, 1):
        print(f"\n📱 [MÃ {i}/{len(codes)}] {code}")
        data = data_builder(code) if data_builder else None
        ok = callback(sess, order_id, code, "success", amount_each, notes, data)
        if ok:
            print("   ✅ Callback thành công")
            results.append({"code": code, "status": "success"})
        else:
            print("   ❌ Callback thất bại (xem server log)")
            results.append({"code": code, "status": "failed"})
    succ = len([r for r in results if r["status"] == "success"])
    fail = len(results) - succ
    print(f"\n📊 Kết quả {label}: ✅ {succ} | ❌ {fail}")
    return results

def build_ftth_data(_code: str) -> Dict:
    return {
        "type": "ftth_details",
        "details": {
            "contract_code": "MOCK123456",
            "contract_owner": "NGUYỄN VĂN TEST",
            "representative_subscriber": "test_sub_001",
            "service": "Internet",
            "contact_phone": "0123456789",
            "debt_amount": "150,000 VND"
        }
    }

def main():
    print("🧪 [SIMPLE TEST] Node API callback & DB update")
    print("=" * 80)

    sess = requests.Session()
    dev_login(sess)
    print("✅ Dev login OK")

    all_results = {}

    all_results["Tra cứu FTTH"] = test_service(
        sess,
        "Tra cứu FTTH",
        ["t074_gftth_test1", "t074_gftth_test2"],
        amount_each=150000,
        notes="FTTH lookup test ok",
        data_builder=build_ftth_data,
    )

    all_results["Tra cứu trả sau"] = test_service(
        sess,
        "Tra cứu trả sau",
        ["POST001", "POST002"],
        amount_each=120000,
        notes="Postpaid lookup test ok",
    )

    all_results["TV-Internet"] = test_service(
        sess,
        "TV-Internet",
        ["TV001", "TV002"],
        amount_each=180000,
        notes="TV-Internet payment test ok",
    )

    all_results["Gạch điện EVN"] = test_service(
        sess,
        "Gạch điện EVN",
        ["EVN001", "EVN002"],
        amount_each=250000,
        notes="EVN payment test ok",
    )

    all_results["Nạp tiền đa mạng"] = test_service(
        sess,
        "Nạp tiền đa mạng",
        ["0123456789", "0987654321"],
        amount_each=None,
        notes="Topup đa mạng test ok",
    )

    all_results["Nạp tiền Viettel"] = test_service(
        sess,
        "Nạp tiền Viettel",
        ["0321234567", "0334567890"],
        amount_each=None,
        notes="Topup Viettel test ok",
    )

    print("\n" + "="*80)
    print("🎯 [TỔNG KẾT]")
    total_succ = 0
    total_fail = 0
    for name, res in all_results.items():
        succ = len([r for r in res if r["status"] == "success"])
        fail = len(res) - succ
        total_succ += succ
        total_fail += fail
        print(f"📊 {name}: ✅ {succ} | ❌ {fail}")
    print(f"\n🏆 TỔNG CỘNG: ✅ {total_succ} | ❌ {total_fail}")
    if total_fail == 0:
        print("🎉 Tất cả callback đều OK")
    else:
        print("⚠️ Có callback thất bại, xem log server để biết chi tiết")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Test bị dừng bởi người dùng")
    except Exception as e:
        print(f"\n💥 Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
