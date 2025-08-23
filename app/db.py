import os
import psycopg2
from typing import List, Optional, Dict, Any
from datetime import datetime
import json as pyjson
import sys

# Thêm thư mục gốc vào path để import config
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app.config import DB_DATABASE_URL

def db_ensure_user(user_id: str, email: str) -> None:
    try:
        with psycopg2.connect(DB_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
                exists = cur.fetchone()
                if exists:
                    return
                cur.execute(
                    """
                    INSERT INTO users (id, email, first_name, last_name, role, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, email, 'Admin', 'Local', 'admin', 'active')
                )
                print(f"[DB] Tạo user mặc định {email} ({user_id})")
    except Exception as e:
        print(f"[DB] Lỗi đảm bảo user tồn tại: {e}")

def update_database_immediately(order_id: str, code: str, status: str, amount: Any,
                                notes: str, details: Optional[Dict[str, Any]] = None) -> bool:
    try:
        order_id = (order_id or "").strip()
        code = (code or "").strip()

        with psycopg2.connect(os.getenv('DATABASE_URL', DB_DATABASE_URL)) as conn:
            with conn.cursor() as cur:
                result_obj = {
                    'code': code,
                    'status': 'completed' if status == 'success' else status,
                    'amount': str(amount) if amount is not None else None,
                    'notes': notes,
                    'details': details or None,
                }
                result_json = pyjson.dumps(result_obj, ensure_ascii=False)

                # 1) Update orders
                cur.execute(
                    """
                    UPDATE orders
                    SET status = %s,
                        result_data = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    ('completed' if status == 'success' else status, result_json, order_id)
                )
                row_order = cur.fetchone()
                if row_order:
                    print(f"   ✅ Đã cập nhật orders (id={row_order[0]}) với trạng thái {status}")
                else:
                    print(f"   ⚠️ Không update được bảng orders (id={order_id})")

                # 2) Update service_transactions theo order_id (bỏ điều kiện status/code)
                cur.execute(
                    """
                    UPDATE service_transactions
                    SET status = %s,
                        amount = COALESCE(%s, amount),
                        notes = %s,
                        processing_data = %s,
                        updated_at = NOW()
                    WHERE order_id = %s
                    RETURNING id
                    """,
                    (
                        'success' if status == 'success' else 'failed' if status == 'failed' else status,
                        str(amount) if isinstance(amount, (int, float)) else None,
                        notes,
                        result_json,
                        order_id,   # <-- chỉ còn 5 tham số, khớp 5 %s
                    )
                )
                tran_rows = cur.fetchall()  # có thể có nhiều giao dịch cùng order_id
                if tran_rows:
                    updated_ids = ", ".join(r[0] for r in tran_rows if r and r[0])
                    print(f"   ✅ Đã cập nhật {len(tran_rows)} service_transactions (id: {updated_ids}) với trạng thái {status}")
                else:
                    print(f"   ⚠️ Không update được service_transactions cho order_id={order_id}")

                # Commit (with-conn sẽ commit nếu không có exception, nhưng gọi tường minh cho chắc)
                conn.commit()

                # 3) Nếu status=success, tự động gọi API mark_bill_completed
                if status == 'success':
                    print(f"   🚀 Status=success, tự động gọi API mark_bill_completed cho {code}")
                    try:
                        # Import và gọi hàm mark_bill_completed
                        from .test1 import mark_bill_completed
                        
                        # Gọi API với order_id (hàm sẽ tự lấy code từ database)
                        result = mark_bill_completed(order_id)
                        if result and result.get('success'):
                            print(f"   ✅ API mark_bill_completed thành công cho {code}")
                        else:
                            print(f"   ⚠️ API mark_bill_completed thất bại cho {code}: {result.get('msg', 'Unknown error')}")
                    except Exception as e:
                        print(f"   ❌ Lỗi khi gọi API mark_bill_completed: {e}")

                return bool(row_order or tran_rows)

    except Exception as e:
        print(f"   ❌ Lỗi cập nhật DB trực tiếp: {e}")
        return False

def db_find_order_id(service_type: str, code: str, user_id: Optional[str] = None) -> Optional[str]:
    try:
        with psycopg2.connect(DB_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        SELECT st.order_id
                        FROM service_transactions st
                        JOIN orders o ON o.id = st.order_id
                        WHERE st.code = %s
                          AND o.service_type = %s
                          AND o.user_id = %s
                          AND st.status IN ('pending','processing')
                        ORDER BY st.created_at DESC
                        LIMIT 1
                        """,
                        (code, service_type, user_id)
                    )
                else:
                    cur.execute(
                        """
                        SELECT st.order_id
                        FROM service_transactions st
                        JOIN orders o ON o.id = st.order_id
                        WHERE st.code = %s
                          AND o.service_type = %s
                          AND st.status IN ('pending','processing')
                        ORDER BY st.created_at DESC
                        LIMIT 1
                        """,
                        (code, service_type)
                    )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        print(f"[DB] Lỗi tìm orderId cho code='{code}': {e}")
        return None

def db_check_pending_orders_for_code(service_type: str, code: str, user_id: Optional[str] = None) -> List[str]:
    try:
        with psycopg2.connect(DB_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        SELECT st.order_id
                        FROM service_transactions st
                        JOIN orders o ON o.id = st.order_id
                        WHERE st.code = %s
                          AND o.service_type = %s
                          AND o.user_id = %s
                          AND st.status IN ('pending','processing')
                        ORDER BY st.created_at DESC
                        """,
                        (code, service_type, user_id)
                    )
                else:
                    cur.execute(
                        """
                        SELECT st.order_id
                        FROM service_transactions st
                        JOIN orders o ON o.id = st.order_id
                        WHERE st.code = %s
                          AND o.service_type = %s
                          AND st.status IN ('pending','processing')
                        ORDER BY st.created_at DESC
                        """,
                        (code, service_type)
                    )
                rows = cur.fetchall()
                return [r[0] for r in rows]
    except Exception as e:
        print(f"[DB] Lỗi kiểm tra pending cho code='{code}': {e}")
        return []

def db_insert_orders_from_lines(service_type: str, user_id: str, lines: List[str]) -> int:
    codes = [ln.strip() for ln in lines if ln and ln.strip()]
    if not codes:
        return 0
    try:
        with psycopg2.connect(DB_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                count = 0
                for code in codes:
                    cur.execute(
                        """
                        INSERT INTO orders (user_id, service_type, status, input_data)
                        VALUES (%s, %s, 'pending', %s)
                        RETURNING id
                        """,
                        (user_id, service_type, code)
                    )
                    cur.fetchone()
                    count += 1
                print(f"[DB] Đã tạo {count} orders cho service '{service_type}'.")
                return count
    except Exception as e:
        print(f"[DB] Lỗi insert orders: {e}")
        return 0

def db_fetch_service_data(service_type: str, payment_type: str = None) -> Optional[Dict[str, Any]]:
    try:
        with psycopg2.connect(os.getenv('DATABASE_URL', DB_DATABASE_URL)) as conn:
            with conn.cursor() as cur:
                if service_type == "nap_tien_da_mang" and payment_type:
                    if payment_type == "prepaid":
                        cur.execute(
                            """
                            SELECT DISTINCT ON (st.code) st.code, st.order_id, st.created_at
                            FROM service_transactions st
                            JOIN orders o ON o.id = st.order_id
                            WHERE o.service_type = %s
                              AND st.status IN ('pending','processing')
                              AND st.code LIKE '%%|%%'
                            ORDER BY st.code, st.created_at DESC
                            """,
                            (service_type,)
                        )
                    elif payment_type == "postpaid":
                        cur.execute(
                            """
                            SELECT DISTINCT ON (st.code) st.code, st.order_id, st.created_at
                            FROM service_transactions st
                            JOIN orders o ON o.id = st.order_id
                            WHERE o.service_type = %s
                              AND st.status IN ('pending','processing')
                              AND st.code NOT LIKE '%%|%%'
                            ORDER BY st.code, st.created_at DESC
                            """,
                            (service_type,)
                        )
                    else:
                        cur.execute(
                            """
                            SELECT DISTINCT ON (st.code) st.code, st.order_id, st.created_at
                            FROM service_transactions st
                            JOIN orders o ON o.id = st.order_id
                            WHERE o.service_type = %s
                              AND st.status IN ('pending','processing')
                            ORDER BY st.code, st.created_at DESC
                            """,
                            (service_type,)
                        )
                else:
                    cur.execute(
                        """
                        SELECT DISTINCT ON (st.code) st.code, st.order_id, st.created_at
                        FROM service_transactions st
                        JOIN orders o ON o.id = st.order_id
                        WHERE o.service_type = %s
                          AND st.status IN ('pending','processing')
                        ORDER BY st.code, st.created_at DESC
                        """,
                        (service_type,)
                    )
                rows = cur.fetchall()
                codes = []
                code_order_map = []
                for code_val, order_val, _ in rows:
                    if not code_val:
                        continue
                    codes.append(code_val)
                    if order_val:
                        code_order_map.append({'code': code_val, 'orderId': order_val})
                latest_order_id = None
                if rows:
                    latest_row = max(rows, key=lambda r: r[2] or datetime.min)
                    latest_order_id = latest_row[1]
                result: Dict[str, Any] = {}
                if service_type in ("tra_cuu_ftth", "thanh_toan_tv_internet"):
                    result["subscriber_codes"] = codes[:10]
                elif service_type == "gach_dien_evn":
                    result["bill_codes"] = codes[:10]
                elif service_type in ("nap_tien_da_mang", "nap_tien_viettel", "tra_cuu_no_tra_sau"):
                    result["subscriber_codes"] = codes[:10]
                else:
                    result["codes"] = codes[:10]
                result["order_id"] = latest_order_id
                result["code_order_map"] = code_order_map
                return result
    except Exception as e:
        print(f"[DB] Lỗi đọc DB cho {service_type}: {e}")
        return None

def db_get_account_credentials(order_id: str) -> Optional[tuple[str, str]]:
    """
    Lấy thông tin đăng nhập (email, password) từ order_id.
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Tuple (email, password) hoặc None nếu không tìm thấy
    """
    try:
        with psycopg2.connect(os.getenv('DATABASE_URL', DB_DATABASE_URL)) as conn:
            with conn.cursor() as cur:
                # Tìm user_id từ order_id
                cur.execute(
                    """
                    SELECT o.user_id, u.email, u.password
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    WHERE o.id = %s
                    """,
                    (order_id,)
                )
                row = cur.fetchone()
                
                if not row:
                    print(f"   ⚠️ Không tìm thấy order với id: {order_id}")
                    return None
                
                user_id, email, password = row
                
                if not email:
                    print(f"   ⚠️ User {user_id} không có email")
                    return None
                
                if not password:
                    print(f"   ⚠️ User {user_id} không có password")
                    return None
                
                print(f"   ✅ Đã lấy credentials cho order {order_id}: {email}")
                return (email, password)
                
    except Exception as e:
        print(f"   ❌ Lỗi lấy credentials cho order {order_id}: {e}")
        return None

def db_get_code_by_order_id(order_id: str) -> Optional[str]:
    """
    Lấy code từ order_id từ bảng service_transactions.
    
    Args:
        order_id: ID của đơn hàng
        
    Returns:
        Code tương ứng hoặc None nếu không tìm thấy
    """
    try:
        with psycopg2.connect(os.getenv('DATABASE_URL', DB_DATABASE_URL)) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT code
                    FROM service_transactions
                    WHERE order_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (order_id,)
                )
                row = cur.fetchone()
                
                if row:
                    code = row[0]
                    print(f"   📋 Lấy được code: {code} cho order_id: {order_id}")
                    return code
                else:
                    print(f"   ⚠️ Không tìm thấy code cho order_id: {order_id}")
                    return None
                
    except Exception as e:
        print(f"   ❌ Lỗi lấy code cho order_id {order_id}: {e}")
        return None

__all__ = [
    "db_ensure_user",
    "update_database_immediately",
    "db_find_order_id",
    "db_check_pending_orders_for_code",
    "db_insert_orders_from_lines",
    "db_fetch_service_data",
    "db_get_account_credentials",
    "db_get_code_by_order_id",
]


