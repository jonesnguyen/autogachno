#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dump all rows from all tables in a PostgreSQL database specified by DATABASE_URL.

Usage:
  - python app/dump_db.py
  - Optional environment variables:
      DATABASE_URL: Postgres connection string
      DB_SCHEMA:    Schema to inspect (default: all non-system schemas)
      DB_LIMIT:     Limit number of rows per table (0 or empty = no limit)
"""

import os
import sys
from contextlib import closing


def import_psycopg2():
    try:
        import psycopg2  # type: ignore
        return psycopg2
    except Exception as e:
        print("\n[ERROR] Missing dependency: psycopg2\n"
              "Please install it first:\n"
              "  pip install psycopg2-binary\n", file=sys.stderr)
        raise


def get_connection(psycopg2):
    database_url = os.getenv(
        "DATABASE_URL",
        "postgres://postgres:123456@localhost:5432/autogachno"
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
            WHERE table_type = 'BASE TABLE'
              AND table_schema = %s
            ORDER BY table_schema, table_name
            """,
            (schema_filter,)
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


def format_value(value) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    if len(text) > 200:
        return text[:200] + "…"  # truncate long fields for readability
    return text


def dump_table(cursor, schema: str, table: str, row_limit: int | None) -> None:
    qualified = f'"{schema}"."{table}"'
    # Fetch rows
    sql = f"SELECT * FROM {qualified}"
    if row_limit and row_limit > 0:
        sql += f" LIMIT {row_limit}"
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc.name for desc in cursor.description]

    # Print header
    print(f"\n=== {schema}.{table} ===")
    print(f"Columns: {', '.join(columns)}")
    print(f"Rows: {len(rows)}")

    # Print data
    if rows:
        # Compute column widths (simple)
        widths = [len(col) for col in columns]
        for row in rows:
            for idx, val in enumerate(row):
                widths[idx] = max(widths[idx], len(format_value(val)))

        # Print header row
        header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
        print(header)
        print("-" * len(header))

        # Print each row
        for row in rows:
            line = " | ".join(format_value(val).ljust(widths[i]) for i, val in enumerate(row))
            print(line)


def main():
    psycopg2 = import_psycopg2()
    with closing(get_connection(psycopg2)) as conn, closing(conn.cursor()) as cur:
        schema = os.getenv("DB_SCHEMA")
        limit_env = os.getenv("DB_LIMIT", "").strip()
        row_limit = int(limit_env) if (limit_env.isdigit() and int(limit_env) > 0) else None

        tables = fetch_tables(cur, schema)
        if not tables:
            print("No tables found.")
            return

        print(f"Found {len(tables)} tables" + (f" in schema '{schema}'" if schema else "") + ".")
        for sch, tbl in tables:
            try:
                dump_table(cur, sch, tbl, row_limit)
            except Exception as e:
                print(f"[WARN] Failed to dump {sch}.{tbl}: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        sys.exit(1)


