import importlib.util
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("engineering_import", ROOT / "scripts/import_engineering_history.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(name="Testbåt", day="2026-09-15", description="Kontroll av gyro", **extra):
    return {"båt": name, "dato": day, "info": description, **extra}


class EngineeringImportTests(unittest.TestCase):
    def test_groups_repeated_visits_and_preserves_date_ranges(self):
        data, report = module.import_engineering([
            row(day=datetime(2026, 9, 15)),
            row(name=" TESTBÅT ", day="2026-06-22 2026-06-26", description="Kamera og REM"),
        ])
        self.assertEqual(report["vessels"], 1)
        self.assertEqual(report["visits"], 2)
        entries = data["vessels"][0]["entries"]
        self.assertEqual(entries[0]["periods"], [{"start": "2026-09-15", "end": None}])
        self.assertEqual(entries[1]["periods"], [{"start": "2026-06-22", "end": "2026-06-26"}])
        self.assertEqual(entries[1]["description"], "Kamera og REM")

    def test_missing_dates_are_rejected_and_missing_descriptions_stay_unknown(self):
        with self.assertRaisesRegex(ValueError, "dato is required"):
            module.import_engineering([row(day=None)])
        data, report = module.import_engineering([row(description=None)])
        self.assertIsNone(data["vessels"][0]["entries"][0]["description"])
        self.assertEqual(len(report["warnings"]), 1)

    def test_image_dates_create_distinct_visits_without_exporting_image_contents(self):
        records = [{"boat": "MV Atlantic", "dates": ["2026-06-17", "2026-07-09"]}]
        original = row(name="MV Atlantic ", day=None, description="Service")
        expanded = module.expand_image_dates([original], records)
        data, report = module.import_engineering(expanded)
        self.assertEqual(report["visits"], 2)
        self.assertEqual([e["periods"][0]["start"] for e in data["vessels"][0]["entries"]],
                         ["2026-07-09", "2026-06-17"])
        self.assertIsNone(original["dato"], "Do not change the original workbook row")
        with self.assertRaisesRegex(ValueError, "Review image dates"):
            module.expand_image_dates([dict(original, dato="2026-06-17")], records)

    def test_engineering_visits_do_not_contribute_tonnage(self):
        data, _ = module.import_engineering([row()])
        entry = data["vessels"][0]["entries"][0]
        self.assertIsNone(entry["tonnes"])
        self.assertFalse(entry["includeInTotal"])

    def test_requires_explicit_correction_for_malformed_dates(self):
        with self.assertRaisesRegex(ValueError, "Invalid date"):
            module.import_engineering([row(day="202608-25")])
        data, report = module.import_engineering([row(day="202608-25")], {"202608-25": "2026-08-25"})
        self.assertEqual(data["vessels"][0]["entries"][0]["periods"][0]["start"], "2026-08-25")
        self.assertEqual(len(report["warnings"]), 1)

    def test_rejects_impossible_dates_reversed_ranges_and_missing_names(self):
        for value in ("2026-02-30", "2026-06-26 2026-06-22", 1234):
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.import_engineering([row(day=value)])
        with self.assertRaisesRegex(ValueError, "boat name is required"):
            module.import_engineering([row(name=" ")])
        with self.assertRaisesRegex(ValueError, "No visits"):
            module.import_engineering([])

    def test_ids_survive_sorting_and_description_edits(self):
        original, _ = module.import_engineering([row(), row(day="2026-09-16")])
        changed, _ = module.import_engineering([row(day="2026-09-16"), row(description="Ny beskrivelse")])
        self.assertEqual(original["vessels"][0]["id"], changed["vessels"][0]["id"])
        self.assertEqual([e["id"] for e in original["vessels"][0]["entries"]],
                         [e["id"] for e in changed["vessels"][0]["entries"]])

    def test_duplicate_visits_require_distinct_explicit_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate visit"):
            module.import_engineering([row(), row(description="Annet arbeid")])
        data, _ = module.import_engineering([row(id="visit-1"), row(id="visit-2")])
        self.assertEqual(len(data["vessels"][0]["entries"]), 2)
        with self.assertRaisesRegex(ValueError, "duplicate visit"):
            module.import_engineering([row(id="visit-1"), row(name="Another boat", id="visit-1")])

    def test_exports_only_public_columns_and_keeps_prefixes(self):
        data, _ = module.import_engineering([row(name="MS Freøy viking", private="NOT FOR EXPORT")])
        self.assertEqual(data["vessels"][0]["name"], "MS Freøy Viking")
        self.assertNotIn("NOT FOR EXPORT", str(data))


if __name__ == "__main__":
    unittest.main()
