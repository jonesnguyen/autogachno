#!/usr/bin/env python3
"""
Script để cập nhật dữ liệu cũ của nạp tiền đa mạng trong database
Phân tích code để xác định loại dịch vụ và số tiền
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kết nối database
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL không được cấu hình")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Lỗi kết nối database: {e}")
        return None

def analyze_multinetwork_code(code):
    """Phân tích code để xác định loại dịch vụ và số tiền"""
    if '|' in code:
        # Gạch nợ trả sau: sđt|số tiền
        parts = code.split('|')
        if len(parts) == 2:
            try:
                amount = int(parts[1])
                valid_amounts = [10000, 20000, 30000, 50000, 100000, 200000, 300000, 500000]
                if amount in valid_amounts:
                    return {
                        'type': 'postpaid',
                        'phone': parts[0].strip(),
                        'amount': amount,
                        'valid': True
                    }
                else:
                    return {
                        'type': 'postpaid',
                        'phone': parts[0].strip(),
                        'amount': amount,
                        'valid': False,
                        'error': f'Số tiền {amount} không hợp lệ'
                    }
            except ValueError:
                return {
                    'type': 'postpaid',
                    'phone': parts[0].strip(),
                    'amount': None,
                    'valid': False,
                    'error': 'Số tiền không phải số'
                }
        else:
            return {
                'type': 'unknown',
                'phone': code,
                'amount': None,
                'valid': False,
                'error': 'Sai định dạng (cần: sđt|số tiền)'
            }
    else:
        # Nạp trả trước: chỉ số điện thoại
        return {
            'type': 'prepaid',
            'phone': code.strip(),
            'amount': None,
            'valid': True
        }

def update_multinetwork_transactions():
    """Cập nhật dữ liệu nạp tiền đa mạng trong database"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lấy tất cả giao dịch nạp tiền đa mạng
            cur.execute("""
                SELECT st.id, st.code, st.notes, st.amount, st.status
                FROM service_transactions st
                JOIN orders o ON st."orderId" = o.id
                WHERE o."serviceType" = 'nap_tien_da_mang'
                ORDER BY st."createdAt" DESC
            """)
            
            transactions = cur.fetchall()
            logger.info(f"Tìm thấy {len(transactions)} giao dịch nạp tiền đa mạng")
            
            updated_count = 0
            for tx in transactions:
                code = tx['code']
                logger.info(f"Phân tích code: {code}")
                
                # Phân tích code
                analysis = analyze_multinetwork_code(code)
                
                # Tạo notes mới
                if analysis['type'] == 'prepaid':
                    new_notes = f"Multi-network: Nạp trả trước - {analysis['phone']}"
                    new_amount = None
                elif analysis['type'] == 'postpaid' and analysis['valid']:
                    new_notes = f"Multi-network: Gạch nợ trả sau - {analysis['phone']} | Số tiền: {analysis['amount']:,}đ"
                    new_amount = analysis['amount']
                else:
                    # Trường hợp lỗi
                    new_notes = f"Multi-network: Lỗi định dạng - {code} | {analysis.get('error', 'Không xác định')}"
                    new_amount = None
                
                # Cập nhật database
                cur.execute("""
                    UPDATE service_transactions 
                    SET notes = %s, amount = %s, "updatedAt" = NOW()
                    WHERE id = %s
                """, (new_notes, new_amount, tx['id']))
                
                updated_count += 1
                logger.info(f"Đã cập nhật: {code} -> {new_notes}")
            
            conn.commit()
            logger.info(f"Hoàn thành cập nhật {updated_count} giao dịch")
            
    except Exception as e:
        logger.error(f"Lỗi cập nhật database: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Hàm chính"""
    logger.info("Bắt đầu cập nhật dữ liệu nạp tiền đa mạng...")
    
    try:
        update_multinetwork_transactions()
        logger.info("Hoàn thành cập nhật dữ liệu!")
    except Exception as e:
        logger.error(f"Lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
