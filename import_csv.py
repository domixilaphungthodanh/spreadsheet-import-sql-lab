import argparse
from contextlib import closing
import csv
from datetime import date
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "database/workshop.db"
FIELDS = ("ticket_code", "service", "received_on", "status")
STATUSES = {"pending", "in_progress", "completed"}
UPSERT = """
INSERT INTO tickets(ticket_code,service,received_on,status) VALUES(?,?,?,?)
ON CONFLICT(ticket_code) DO UPDATE SET
    service=excluded.service, received_on=excluded.received_on, status=excluded.status
WHERE (tickets.service,tickets.received_on,tickets.status)
   IS NOT (excluded.service,excluded.received_on,excluded.status)
"""


def validated_values(row, seen):
    if len(row) != len(FIELDS):
        raise ValueError("Sai số cột")
    code, service, day, status = (value.strip() for value in row)
    code = code.upper()
    if not all((code, service, day, status)):
        raise ValueError("Có ô bắt buộc bị trống")
    if not re.fullmatch(r"SC-[0-9]{3}", code):
        raise ValueError("Mã phiếu phải theo dạng SC-001")
    if code in seen:
        raise ValueError(f"Mã trùng trong file {code}")
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError as error:
        raise ValueError("Ngày không hợp lệ, dùng YYYY-MM-DD") from error
    if status not in STATUSES:
        raise ValueError(f"Trạng thái lạ {status}")
    seen.add(code)
    return code, service, day, status


def import_file(source, db=DEFAULT_DB):
    source, db = Path(source), Path(db)
    schema = (ROOT / "sql/schema.sql").read_text(encoding="utf-8")
    counts = dict(added=0, updated=0, unchanged=0)
    seen = set()
    line = 1
    try:
        with source.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = next(reader, [])
            if len(header) != len(FIELDS) or set(header) != set(FIELDS):
                raise ValueError("Cần đúng bốn cột ticket_code, service, received_on, status")
            positions = [header.index(field) for field in FIELDS]
            db.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(db)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(schema)
                while True:
                    line = reader.line_num + 1
                    row = next(reader, None)
                    if row is None:
                        break
                    if len(row) != len(FIELDS):
                        raise ValueError("Sai số cột")
                    values = validated_values([row[index] for index in positions], seen)
                    previous = connection.execute(
                        "SELECT service,received_on,status FROM tickets WHERE ticket_code=?",
                        (values[0],),
                    ).fetchone()
                    cursor = connection.execute(UPSERT, values)
                    outcome = "unchanged" if cursor.rowcount == 0 else "added" if previous is None else "updated"
                    counts[outcome] += 1
    except (ValueError, csv.Error, OSError, sqlite3.Error) as error:
        raise ValueError(f"{source}, dòng {line}: {error}") from error
    return counts


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    try:
        counts = import_file(args.csv, args.db)
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    print("Thêm {added}, cập nhật {updated}, giữ nguyên {unchanged}.".format(**counts))


if __name__ == "__main__":
    main()

