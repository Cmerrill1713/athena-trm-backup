#!/usr/bin/env python3
"""
Prune old traces from telemetry.sqlite and keep DB lean.
Config via env:
  TELEMETRY_DB=./state/telemetry.sqlite
  DAYS_TO_KEEP=14
  MAX_ROWS=50000
"""
import os
import sqlite3
import time


DB = os.environ.get("TELEMETRY_DB", "./state/telemetry.sqlite")
DAYS = int(os.environ.get("DAYS_TO_KEEP", "14"))
MAX_ROWS = int(os.environ.get("MAX_ROWS", "50000"))
NOW = time.time()
CUTOFF = NOW - DAYS * 86400


def main():
    if not os.path.exists(DB):
        print(f"no DB at {DB}, nothing to do")
        return

    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        before = c.execute("select count(*) as n from traces").fetchone()["n"]

        # Prune by age
        c.execute("delete from traces where started_at < ?", (CUTOFF,))

        # Prune by cap (keep most recent MAX_ROWS)
        left = c.execute("select count(*) as n from traces").fetchone()["n"]
        if left > MAX_ROWS:
            offset = left - MAX_ROWS
            # Delete oldest N rows by started_at
            c.execute("""
              delete from traces where trace_id in (
                select trace_id from traces order by started_at asc limit ?
              )""", (offset,))

        # Vacuum to reclaim space
        c.execute("vacuum")

        after = c.execute("select count(*) as n from traces").fetchone()["n"]

    print(f"Telemetry rotated: {before} -> {after} rows (kept {DAYS}d, cap {MAX_ROWS})")


if __name__ == "__main__":
    main()
