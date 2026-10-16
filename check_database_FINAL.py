from pathlib import Path
import sqlite3
from config import Config

print("DATABASE_URL:", Config.DATABASE_URL)
if not Config.DATABASE_URL.lower().startswith("sqlite:///"):
    raise SystemExit("ERROR: DATABASE_URL is not SQLite")

path = Path(Config.DATABASE_URL.removeprefix("sqlite:///"))
print("DB PATH:", path)
print("PARENT:", path.parent)
path.parent.mkdir(parents=True, exist_ok=True)

try:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS __startup_test (id INTEGER PRIMARY KEY)")
    con.commit()
    con.close()
    print("SQLITE TEST: OK")
    print("DATABASE IS READY")
except Exception as exc:
    print("SQLITE TEST: FAILED")
    print(type(exc).__name__, exc)
    raise
