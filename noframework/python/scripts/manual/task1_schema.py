import argparse
from pathlib import Path
from dotenv import load_dotenv

from infinite_scalability.store import Store


def main():
    load_dotenv(".env.test")
    parser = argparse.ArgumentParser(description="Task 1 manual check: schema & lifecycle.")
    parser.add_argument("--persist", action="store_true", help="Keep DB after run")
    parser.add_argument("--db-path", default=None, help="Optional path for DB")
    args = parser.parse_args()

    db_path = Path(args.db_path) if args.db_path else None
    store = Store(db_path=db_path, persist=args.persist)
    try:
        cur = store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        print("Tables:")
        for row in cur.fetchall():
            print(f"- {row[0]}")
    finally:
        store.close()
        if not args.persist and db_path:
            print("Ephemeral DB removed.")


if __name__ == "__main__":
    main()
