import sys
import os
from pathlib import Path

# 将 apps/api 加入路径
sys.path.append(str(Path(__file__).resolve().parent.parent / "apps" / "api"))

try:
    from app.core.config import settings
    from app.core.db import init_db, get_db_connection
    from app.services.object_service import ObjectService
    from app.utils.crypto import make_id
except ImportError as e:
    print(f"FAILED: Import error - {e}")
    sys.exit(1)

def test_config():
    print(f"Checking Config: DB_PATH={settings.db_abs_path}")
    assert "financial-ai-os" in str(settings.db_abs_path)
    print("SUCCESS: Config validated.")

def test_db_init():
    print("Initializing Database...")
    init_db()
    conn = get_db_connection(read_only=True)
    try:
        res = conn.execute("SELECT COUNT(*) FROM system_init").fetchone()
        print(f"SUCCESS: Database initialized. Init records: {res[0]}")
    finally:
        conn.close()

def test_wiki_object():
    print("Testing Wiki Object persistence...")
    test_content = "This is a smoke test strategy."
    test_fm = {"test_id": make_id("smoke"), "status": "verified"}
    
    path = ObjectService.save_wiki_object(
        category="research",
        name="smoke_test_report",
        content=test_content,
        frontmatter=test_fm
    )
    
    abs_path = Path(path)
    assert abs_path.exists()
    print(f"SUCCESS: Wiki object created at {abs_path}")
    
    # Verify content
    content = abs_path.read_text(encoding="utf-8")
    assert "status: verified" in content
    assert test_content in content
    print("SUCCESS: Wiki content verified.")

if __name__ == "__main__":
    print("=== PFIOS Data Layer Smoke Test ===")
    try:
        test_config()
        test_db_init()
        test_wiki_object()
        print("=== ALL MIDPOINT CHECKS PASSED ===")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
