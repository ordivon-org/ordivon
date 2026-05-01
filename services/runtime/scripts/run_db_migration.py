import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from state.db.session import get_db_connection


def run_migration():
    from shared.config.settings import settings

    print(f"DEBUG: Using database at {settings.db_abs_path}")
    sql_path = project_root / "scripts" / "migrations" / "20240417_core_completion.sql"
    if not sql_path.exists():
        print(f"Migration file not found: {sql_path}")
        return

    sql_content = sql_path.read_text(encoding="utf-8")

    conn = get_db_connection(read_only=False)
    try:
        # Split by ';' and clean up
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]
        for stmt in statements:
            try:
                print(f"Executing: {stmt[:50]}...")
                conn.execute(stmt)
            except Exception as e:
                # If column already exists, duckdb might throw an error.
                # For this specific migration, we'll log and continue for ALTER TABLE
                if "already exists" in str(e).lower():
                    print(f"Skipping (already exists): {e}")
                else:
                    print(f"Error in statement: {e}")
                    # In a real migration system we might rollback, but for now we continue
        print("Migration process finished.")
    except Exception as e:
        print(f"Migration runner failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
