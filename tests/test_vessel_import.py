import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vessel_import", ROOT / "scripts/import_vessel_history.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(**values):
    return dict({
        "entry_id": "first", "boat_name": "test boat", "date": "2025-01-02", "end_date": "",
        "fish_tonnes": "120.25", "fish_tonnage_status": "extracted", "include_in_fish_summary": "yes",
        "employee": "PRIVATE NAME", "piecework_pay_nok": "5000", "description": "PRIVATE PAYROLL NOTES",
    }, **values)


class VesselImportTests(unittest.TestCase):
    def test_confirmed_split_preserves_date_total_and_existing_boat_history(self):
        splits = json.loads(module.DEFAULT_SPLITS.read_text(encoding="utf-8"))
        split = splits[0]
        original = row(entry_id=split["entry_id"], boat_name=split["boat_name"], date=split["date"],
                       end_date=split["date"], fish_tonnes=split["fish_tonnes"],
                       assignment_kind="multiple_or_unclear_boats", fish_tonnage_status="user_entered")
        existing = row(entry_id="existing-bautar", boat_name="bautar", landing_boat_id="1997003984",
                       landing_boat_name="BAUTAR", fish_tonnes="50")
        data, report = module.import_unloading([original, existing], splits)
        self.assertEqual(report["includedTonnes"], "360.0")
        self.assertEqual(report["unloadings"], 3)
        self.assertEqual(report["splitRowsAdded"], 1)
        self.assertEqual({v["name"] for v in data["vessels"]}, {"Bautar", "Bjørkhaug"})
        for name, tonnes in [("Bautar", 85), ("Bjørkhaug", 225)]:
            vessel = next(v for v in data["vessels"] if v["name"] == name)
            entry = next(e for e in vessel["entries"] if e["periods"][0]["start"] == "2025-09-29")
            self.assertEqual(entry["tonnes"], tonnes)
            self.assertEqual(entry["tonnageKind"], "reported")
            self.assertTrue(entry["includeInTotal"])
            self.assertIsNone(vessel["note"])
        self.assertEqual(original["boat_name"], split["boat_name"], "The source row must remain intact")

    def test_split_rejects_changed_source_or_unbalanced_allocation(self):
        splits = json.loads(module.DEFAULT_SPLITS.read_text(encoding="utf-8"))
        split = splits[0]
        original = row(entry_id=split["entry_id"], boat_name=split["boat_name"], date=split["date"],
                       fish_tonnes=split["fish_tonnes"])
        with self.assertRaisesRegex(ValueError, "Source changed"):
            module.import_unloading([dict(original, fish_tonnes="311")], splits)
        split["parts"][0]["fish_tonnes"] = "86"
        with self.assertRaisesRegex(ValueError, "preserve the original total"):
            module.import_unloading([original], splits)

    def test_shared_landing_counts_once_and_preserves_work_dates(self):
        landing = dict(landing_source_url="https://fangstdata.no/offload/2025-1-3/123",
                       landing_boat_id="123", landing_boat_name="TEST BOAT",
                       fish_tonnage_status="landing_reference")
        data, report = module.import_unloading([row(**landing), row(entry_id="second", date="2025-01-03", **landing)])
        self.assertEqual(report["includedTonnes"], "120.25")
        self.assertEqual(report["unloadings"], 1)
        self.assertEqual([p["start"] for p in data["vessels"][0]["entries"][0]["periods"]], ["2025-01-03", "2025-01-02"])

    def test_zero_missing_and_estimate_remain_distinct(self):
        data, report = module.import_unloading([
            row(fish_tonnes="0"),
            row(entry_id="second", fish_tonnes=""),
            row(entry_id="third", fish_tonnes="75", fish_tonnage_status="estimated_average", include_in_fish_summary="no"),
            row(entry_id="fourth", fish_tonnes="25", include_in_fish_summary="no"),
        ])
        entries = data["vessels"][0]["entries"]
        self.assertEqual(report["includedTonnes"], "75.0")
        self.assertEqual(sum(entry["includeInTotal"] for entry in entries), 2)
        self.assertTrue(any(entry["tonnes"] is None for entry in entries))
        self.assertTrue(any(entry["tonnes"] == 75 and entry["includeInTotal"] for entry in entries))
        self.assertTrue(any(entry["tonnes"] == 25 and not entry["includeInTotal"] for entry in entries))

    def test_aliases_merge_only_with_shared_identity_evidence(self):
        data, _ = module.import_unloading([
            row(boat_name="test boal", landing_boat_id="123", landing_boat_name="TEST BOAT"),
            row(entry_id="second", boat_name="test boat", landing_boat_id="123", landing_boat_name="TEST BOAT"),
            row(entry_id="third", boat_name=" Test Boal "),
            row(entry_id="fourth", boat_name="test boaf"),
        ])
        self.assertEqual(len(data["vessels"]), 2)
        self.assertEqual(len(next(v for v in data["vessels"] if v["id"] == "fangstdata-123")["entries"]), 3)

    def test_name_casing_does_not_split_vessels_or_disable_canonical_name(self):
        data, _ = module.import_unloading([
            row(boat_name="RAMOEN"), row(entry_id="second", boat_name="ramoen"),
            row(entry_id="third", boat_name="Ramoen"),
            row(entry_id="fourth", boat_name="feillest navn", landing_boat_id="123", landing_boat_name="KÅGTIND II"),
            row(entry_id="fifth", boat_name="kågtind", landing_boat_id="123", landing_boat_name="Kågtind ii"),
        ])
        self.assertEqual(len(data["vessels"]), 2)
        self.assertEqual({v["name"] for v in data["vessels"]}, {"Ramoen", "Kågtind II"})
        self.assertEqual(len(next(v for v in data["vessels"] if v["name"] == "Ramoen")["entries"]), 3)

    def test_conflicting_shared_weights_and_duplicate_ids_fail(self):
        landing = dict(landing_source_url="https://fangstdata.no/offload/2025-1-3/123", fish_tonnage_status="landing_reference")
        with self.assertRaisesRegex(ValueError, "Conflicting quantities"):
            module.import_unloading([row(**landing), row(entry_id="second", fish_tonnes="999", **landing)])
        with self.assertRaisesRegex(ValueError, "duplicate entry ID"):
            module.import_unloading([row(), row()])

    def test_no_private_columns_or_raw_description_are_exported(self):
        data, _ = module.import_unloading([row()])
        encoded = json.dumps(data)
        for private in ["PRIVATE", "employee", "piecework", "5000"]:
            self.assertNotIn(private, encoded)

    def test_official_dataset_distinguishes_dates_and_vessels_but_merges_same_landing(self):
        source = dict(landing_source_url="https://register.fiskeridir.no/uttrekk/fangstdata_2023.csv.zip",
                      landing_dates="2023-07-24", landing_boat_id="123", fish_tonnage_status="landing_reference")
        data, report = module.import_unloading([
            row(date="2023-07-24", **source),
            row(entry_id="second", date="2023-07-23", public_note="Arbeid dagen før landing.", **source),
            row(entry_id="third", date="2023-08-24", **dict(source, landing_dates="2023-08-24")),
            row(entry_id="fourth", date="2023-07-24", boat_name="another boat", **dict(source, landing_boat_id="456")),
        ])
        self.assertEqual(report["unloadings"], 3)
        self.assertEqual(report["includedTonnes"], "360.75")
        entries = [e for v in data["vessels"] for e in v["entries"]]
        self.assertEqual(len({e["id"] for e in entries}), 3)
        self.assertTrue(any(e["description"] == "Arbeid dagen før landing." for e in entries))

    def test_official_source_rejects_missing_identity_and_overlapping_cargo(self):
        source = dict(landing_source_url="https://register.fiskeridir.no/uttrekk/fangstdata_2023.csv.zip",
                      landing_dates="2023-07-24", landing_boat_id="123", fish_tonnage_status="landing_reference")
        for change in [{"landing_boat_id":""}, {"landing_dates":""}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.import_unloading([row(**dict(source, **change))])
        with self.assertRaisesRegex(ValueError, "Overlapping landing"):
            module.import_unloading([row(**source), row(entry_id="second", **dict(source, landing_dates="2023-07-24;2023-07-25"))])

    def test_catch_year_sources_can_precede_landing_and_span_years(self):
        sources = "https://register.fiskeridir.no/uttrekk/fangstdata_2021.csv.zip ; https://register.fiskeridir.no/uttrekk/fangstdata_2022.csv.zip"
        base = row(date="2022-01-07", landing_dates="2022-01-07", landing_boat_id="123",
                   landing_municipality="ÅLESUND", landing_source_url=sources,
                   fish_tonnage_status="landing_reference", fish_tonnes="673.00")
        data, report = module.import_unloading([base, dict(base, entry_id="second", date="2022-01-06")])
        entry = data["vessels"][0]["entries"][0]
        self.assertEqual(report["unloadings"], 1)
        self.assertEqual(report["includedTonnes"], "673.0")
        self.assertEqual(len(entry["sourceUrls"]), 2)
        self.assertEqual(len(entry["periods"]), 2)
        _, report = module.import_unloading([base, dict(base, entry_id="other-town", landing_municipality="ØRSTA")])
        self.assertEqual(report["unloadings"], 2)

    def test_unverified_shared_cargo_stays_labelled_and_counts_once(self):
        base = row(landing_dates="2022-01-07", landing_boat_id="123",
                   landing_source_url="https://register.fiskeridir.no/uttrekk/fangstdata_2021.csv.zip",
                   fish_tonnage_status="unverified_reference", public_note="Mengden er uavklart.")
        data, report = module.import_unloading([base, dict(base, entry_id="second", date="2025-01-03")])
        entry = data["vessels"][0]["entries"][0]
        self.assertEqual(report["includedTonnes"], "120.25")
        self.assertEqual(entry["tonnageKind"], "unverified")
        self.assertEqual(len(entry["periods"]), 2)
        self.assertEqual(entry["description"], "Mengden er uavklart.")

    def test_bad_dates_and_non_finite_weights_fail(self):
        for values in [{"date": ""}, {"end_date": "2024-01-01"}, {"fish_tonnes": "NaN"}, {"fish_tonnes": "-10"}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                module.import_unloading([row(**values)])

    def test_overlapping_landing_groups_fail_before_double_counting(self):
        first = "https://fangstdata.no/offload/2025-1-3/123"
        second = "https://fangstdata.no/offload/2025-1-4/123"
        with self.assertRaisesRegex(ValueError, "Overlapping landing"):
            module.import_unloading([
                row(fish_tonnage_status="landing_reference", landing_source_url=first),
                row(entry_id="second", fish_tonnage_status="landing_reference", landing_source_url=first + " " + second),
            ])

    def test_published_data_has_only_public_fields_and_consistent_totals(self):
        data = json.loads((ROOT / "wwwroot/data/vessels/unloading.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["category"], "unloading")
        identities = set()
        sources = set()
        for vessel in data["vessels"]:
            self.assertEqual(set(vessel), {"id", "name", "note", "entries"})
            self.assertNotIn(vessel["id"], identities)
            identities.add(vessel["id"])
            self.assertTrue(vessel["name"].strip())
            for entry in vessel["entries"]:
                self.assertEqual(set(entry), {"id", "periods", "tonnes", "tonnageKind", "includeInTotal", "description", "sourceUrls"})
                self.assertTrue(entry["periods"])
                for period in entry["periods"]:
                    module.parse_date(period["start"], "start")
                    self.assertGreaterEqual(period["end"] or period["start"], period["start"])
                if entry["tonnageKind"] == "estimated" and entry["tonnes"] is not None:
                    self.assertTrue(entry["includeInTotal"])
                for url in entry["sourceUrls"]:
                    if url.startswith("https://fangstdata.no/"):
                        self.assertNotIn(url, sources, "The same landing must not be counted twice")
                        sources.add(url)


if __name__ == "__main__":
    unittest.main()
