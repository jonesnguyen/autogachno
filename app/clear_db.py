#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clear (truncate) all data from all tables in a PostgreSQL database.

Usage:
  - python app/clear_db.py
Environment variables:
  - DATABASE_URL (default: postgres://postgres:123456@localhost:5432/autogachno)
  - DB_SCHEMA    (optional, if set: only truncate tables in this schema)
"""

import os
import sys
from contextlib import closing


def import_psycopg2():
    try:
        import psycopg2  # type: ignore
        return psycopg2
    except Exception:
        print("[ERROR] Please install psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
        raise


def get_connection(psycopg2):
    database_url = os.getenv(
        "DATABASE_URL",
        "postgres://postgres:123456@localhost:5432/autogachno",
    )
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"[ERROR] Cannot connect to database: {e}", file=sys.stderr)
        raise


def fetch_tables(cursor, schema_filter: str | None = None) -> list[tuple[str, str]]:
    if schema_filter:
        cursor.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema = %s
            ORDER BY table_schema, table_name
            """,
            (schema_filter,),
        )
    else:
        cursor.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
            """
        )
    return [(r[0], r[1]) for r in cursor.fetchall()]


def quote_ident(schema: str, table: str) -> str:
    return '"' + schema.replace('"', '""') + '".' + '"' + table.replace('"', '""') + '"'


def truncate_all(cursor, tables: list[tuple[str, str]]) -> None:
    if not tables:
        print("No tables to truncate.")
        return
    qualified = ", ".join(quote_ident(s, t) for s, t in tables)
    sql = f"TRUNCATE {qualified} RESTART IDENTITY CASCADE;"
    cursor.execute(sql)
    print(f"Truncated {len(tables)} tables. IDs reset.")


def main():
    psycopg2 = import_psycopg2()
    with closing(get_connection(psycopg2)) as conn, closing(conn.cursor()) as cur:
        schema = os.getenv("DB_SCHEMA")
        tables = fetch_tables(cur, schema)
        print(f"Found {len(tables)} tables" + (f" in schema '{schema}'" if schema else "") + ".")
        truncate_all(cur, tables)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception:
        sys.exit(1)


