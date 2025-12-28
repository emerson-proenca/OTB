import os
import sqlite3
from pathlib import Path

import pandas as pd

# --- CONFIGURATION ---
INPUT_FILE = "abc.jsonl"  # fide_tournaments.jsonl
BASE_NAME = "fide_tournaments"  # fide_tournaments


def convert_data():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} not found")
        return

    print("[READ] Reading .jsonl")
    df = pd.read_json(INPUT_FILE, lines=True)

    print("[SAVE] Saving as .csv")
    df.to_csv(f"{BASE_NAME}.csv", index=False, encoding="utf-8")

    print("[SAVE] Saving as .parquet")
    df.to_parquet(f"{BASE_NAME}.parquet", index=False)

    print("[SAVE] Saving as .db")
    conn = sqlite3.connect(f"{BASE_NAME}.db")
    df.to_sql("tournaments", conn, if_exists="replace", index=False)
    conn.close()

    print(f"[DONE] {Path(f'{BASE_NAME}.csv').resolve()}")
    print(f"[DONE] {Path(f'{BASE_NAME}.parquet').resolve()}")
    print(f"[DONE] {Path(f'{BASE_NAME}.db').resolve()}")


if __name__ == "__main__":
    convert_data()
