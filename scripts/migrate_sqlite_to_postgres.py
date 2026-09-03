import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text, MetaData, Table

# Setup paths and environment
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

dotenv_path = REPOSITORY_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

def parse_datetime(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        val_clean = val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(val_clean)
        except ValueError:
            return None
    return None

def parse_json(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return None
    return None

def log(msg=""):
    print(msg, flush=True)

def main():
    sqlite_db_path = REPOSITORY_ROOT / "job_agent.db"
    pg_url = os.getenv("DATABASE_URL")
    if not pg_url:
        log("ERROR: DATABASE_URL not set in environment.")
        sys.exit(1)

    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)

    log("=== Starting SQLite to PostgreSQL Migration ===")
    log(f"SQLite Source: {sqlite_db_path}")
    
    # 1. Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # 2. Connect to PostgreSQL
    pg_engine = create_engine(pg_url, pool_pre_ping=True)
    metadata = MetaData()
    metadata.reflect(bind=pg_engine)

    table_order = [
        "companies",
        "resumes",
        "candidate_profiles",
        "jobs",
        "applications",
        "job_runs",
        "recruiters",
        "notifications",
    ]

    sqlite_counts = {}
    migrated_counts = {}

    # Define per-table column conversions
    boolean_cols = {
        "companies": ["enabled"],
        "applications": ["notification_sent"],
    }
    json_cols = {
        "resumes": ["domains"],
        "candidate_profiles": ["profile_data"],
        "job_runs": ["summary_data"],
    }
    datetime_cols = {
        "companies": ["created_at", "updated_at"],
        "resumes": ["created_at", "updated_at"],
        "candidate_profiles": ["updated_at"],
        "jobs": ["posted_at", "first_seen_at", "last_seen_at"],
        "applications": ["created_at"],
        "job_runs": ["started_at", "completed_at", "finished_at"],
        "recruiters": ["created_at"],
        "notifications": ["created_at"],
    }

    # 3. Perform Migration within a single PostgreSQL transaction
    with pg_engine.begin() as conn:
        for tbl_name in table_order:
            # Read SQLite rows
            sqlite_cursor.execute(f'SELECT * FROM "{tbl_name}"')
            rows = sqlite_cursor.fetchall()
            sqlite_counts[tbl_name] = len(rows)

            if not rows:
                migrated_counts[tbl_name] = 0
                log(f"Table '{tbl_name}': 0 rows to migrate.")
                continue

            pg_table = metadata.tables[tbl_name]
            clean_rows = []
            for row in rows:
                row_dict = dict(row)
                
                # Convert Booleans
                for col in boolean_cols.get(tbl_name, []):
                    if col in row_dict and row_dict[col] is not None:
                        row_dict[col] = bool(row_dict[col])

                # Convert JSON
                for col in json_cols.get(tbl_name, []):
                    if col in row_dict and row_dict[col] is not None:
                        row_dict[col] = parse_json(row_dict[col])

                # Convert Datetimes
                for col in datetime_cols.get(tbl_name, []):
                    if col in row_dict and row_dict[col] is not None:
                        row_dict[col] = parse_datetime(row_dict[col])

                clean_rows.append(row_dict)

            # Execute bulk insert for table
            conn.execute(pg_table.insert(), clean_rows)
            migrated_counts[tbl_name] = len(clean_rows)
            log(f"Table '{tbl_name}': Migrated {len(clean_rows)} rows successfully.")

        # 4. Synchronize PostgreSQL ID Sequences
        log("\n=== Synchronizing PostgreSQL Sequences ===")
        for tbl_name in table_order:
            if sqlite_counts[tbl_name] > 0:
                conn.execute(text(f"""
                    SELECT setval(pg_get_serial_sequence('{tbl_name}', 'id'), COALESCE((SELECT MAX(id) FROM "{tbl_name}"), 1));
                """))
                log(f"Sequence synchronized for table '{tbl_name}'.")

    # 5. Post-Migration Verification
    log("\n=== Post-Migration Verification ===")
    pg_counts = {}
    with pg_engine.connect() as conn:
        for tbl_name in table_order:
            cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl_name}"')).scalar()
            pg_counts[tbl_name] = cnt

    log("\n--- Row Count Parity Check ---")
    all_parity = True
    for tbl_name in table_order:
        s_cnt = sqlite_counts[tbl_name]
        p_cnt = pg_counts[tbl_name]
        match = (s_cnt == p_cnt)
        if not match:
            all_parity = False
        status = "PASSED" if match else "FAILED"
        log(f"Table {tbl_name:<20}: SQLite={s_cnt:<5} | Postgres={p_cnt:<5} | Parity: {status}")

    # Verify ID Preservation
    log("\n--- Primary Key Preservation Check ---")
    pk_check_passed = True
    with pg_engine.connect() as conn:
        for tbl_name in table_order:
            if sqlite_counts[tbl_name] > 0:
                sqlite_cursor.execute(f'SELECT id FROM "{tbl_name}"')
                sqlite_ids = set(r[0] for r in sqlite_cursor.fetchall())
                
                pg_res = conn.execute(text(f'SELECT id FROM "{tbl_name}"')).fetchall()
                pg_ids = set(r[0] for r in pg_res)

                if sqlite_ids == pg_ids:
                    log(f"Table {tbl_name:<20}: {len(sqlite_ids)} / {len(pg_ids)} IDs matched exactly.")
                else:
                    pk_check_passed = False
                    log(f"ERROR: Table {tbl_name} ID mismatch!")

    # Verify Relationships
    log("\n--- Relationship Integrity Check ---")
    rel_check_passed = True
    with pg_engine.connect() as conn:
        orphan_apps = conn.execute(text("""
            SELECT COUNT(*) FROM applications 
            WHERE job_id NOT IN (SELECT id FROM jobs)
        """)).scalar()
        if orphan_apps == 0:
            log("Applications -> Jobs relationship intact (0 orphan applications).")
        else:
            rel_check_passed = False
            log(f"ERROR: Found {orphan_apps} orphan applications!")

        orphan_resumes = conn.execute(text("""
            SELECT COUNT(*) FROM applications 
            WHERE resume_id IS NOT NULL AND resume_id NOT IN (SELECT id FROM resumes)
        """)).scalar()
        if orphan_resumes == 0:
            log("Applications -> Resumes relationship intact (0 orphan resume links).")
        else:
            rel_check_passed = False
            log(f"ERROR: Found {orphan_resumes} orphan resume links!")

    total_sqlite = sum(sqlite_counts.values())
    total_migrated = sum(migrated_counts.values())
    total_pg = sum(pg_counts.values())

    log("\n=== Migration Summary ===")
    log(f"Total SQLite Rows: {total_sqlite}")
    log(f"Total Migrated Rows: {total_migrated}")
    log(f"Total Postgres Rows: {total_pg}")
    log(f"Row Parity Status: {'PASSED' if all_parity else 'FAILED'}")
    log(f"PK Preservation Status: {'PASSED' if pk_check_passed else 'FAILED'}")
    log(f"Relationship Status: {'PASSED' if rel_check_passed else 'FAILED'}")

    if all_parity and pk_check_passed and rel_check_passed:
        log("\nMIGRATION COMPLETED SUCCESSFULLY!")
    else:
        log("\nMIGRATION FAILED VERIFICATION CHECKS.")
        sys.exit(1)

if __name__ == "__main__":
    main()
