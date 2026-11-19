"""
Run every analysis query in sql/02..05 against the SQLite database and save
each result to sql/results/<query>.csv (and print it).

Usage:  python scripts/run_sql.py
"""
from pathlib import Path
import re
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "dala_market.db"
RES = ROOT / "sql" / "results"
RES.mkdir(exist_ok=True)

pd.set_option("display.width", 160, "display.max_columns", 20, "display.max_rows", 30)


def statements(path: Path):
    text = path.read_text()
    for stmt in text.split(";"):
        if not re.search(r"\bSELECT\b", stmt, re.I):
            continue
        m = re.search(r"--\s*(Q\d+)\.\s*(.+)", stmt)
        qid, title = (m.group(1), m.group(2).strip()) if m else ("Q", path.stem)
        yield qid, title, stmt


con = sqlite3.connect(DB)
for f in sorted((ROOT / "sql").glob("0[2-9]_*.sql")):
    for qid, title, sql in statements(f):
        df = pd.read_sql_query(sql, con)
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:50]
        df.to_csv(RES / f"q{int(qid[1:]):02d}_{slug}.csv", index=False)
        print(f"\n=== {qid}. {title}  ({f.name}) ===")
        print(df.head(15).to_string(index=False))
con.close()
