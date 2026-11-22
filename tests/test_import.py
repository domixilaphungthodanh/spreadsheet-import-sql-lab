import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from import_csv import import_file, ROOT


class ImportTests(unittest.TestCase):
    def test_sequence_and_rollback(self):
        with TemporaryDirectory() as folder:
            db = Path(folder)/"workshop.db"
            for name, expected, total in [
                ("first", (2,0,0), 2), ("second", (1,1,0), 3), ("second", (0,0,2), 3)
            ]:
                result = import_file(ROOT/f"examples/{name}.csv", db)
                self.assertEqual(tuple(result.values()), expected)
                with closing(sqlite3.connect(db)) as connection:
                    self.assertEqual(connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], total)
            before = db.read_bytes()
            with self.assertRaisesRegex(ValueError, "dòng 3"):
                import_file(ROOT/"examples/invalid.csv", db)
            self.assertEqual(db.read_bytes(), before)
            with closing(sqlite3.connect(db)) as connection:
                self.assertEqual(connection.execute(
                    "SELECT status FROM tickets WHERE ticket_code='SC-002'").fetchone(), ("completed",))

    def test_bom_and_validation(self):
        with TemporaryDirectory() as folder:
            db, csv = Path(folder)/"db", Path(folder)/"input.csv"
            header = "ticket_code,service,received_on,status\n"
            valid = "SC-006,Thay dầu,2026-02-28,pending\n"
            csv.write_text(header+valid, encoding="utf-8-sig")
            self.assertEqual(import_file(csv, db)["added"], 1)
            for row, error in [
                (" sc-006 ,Thay dầu,2026-02-28,pending", "Mã trùng"),
                ("SC-007,Thay dầu,2026-02-30,pending", "Ngày không hợp lệ"),
                ("SC-007,Thay dầu,2026-02-28,other", "Trạng thái lạ"),
            ]:
                with self.subTest(row=row):
                    csv.write_text(header+valid+row, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, f"dòng 3: {error}"):
                        import_file(csv, db)

