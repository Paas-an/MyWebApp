"""Export public vessel history from the reviewed CSV. Uses Python's standard library."""
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_SPLITS = Path(__file__).resolve().parents[1] / "Features/Vessels/unloading-splits.json"


def normalize(value):
    return " ".join(unicodedata.normalize("NFC", value or "").split()).casefold()


def identifier(prefix, value):
    return prefix + "-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def display_name(value):
    # Preserve abbreviations in canonical names while avoiding all-caps headings.
    return " ".join(word if word in {"I", "II", "III", "IV"} else word.capitalize()
                    for word in value.strip().split())


def parse_date(value, field):
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid {field}: {value!r}") from error


def parse_tonnes(value):
    if not value or not value.strip():
        return None
    try:
        amount = Decimal(value.replace(",", "."))
    except InvalidOperation as error:
        raise ValueError(f"Invalid tonnage: {value!r}") from error
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"Invalid tonnage: {value!r}")
    return amount


def apply_splits(rows, splits):
    """Apply owner-confirmed allocations without changing the original timesheet export."""
    rules = {split["entry_id"]: split for split in splits}
    if len(rules) != len(splits):
        raise ValueError("Duplicate split entry ID")
    result = []
    for row in rows:
        split = rules.get(row["entry_id"])
        if split is None:
            result.append(row)
            continue
        original_tonnes = parse_tonnes(row["fish_tonnes"])
        if (normalize(row["boat_name"]) != normalize(split["boat_name"])
                or row["date"] != split["date"]
                or (row.get("end_date") or row["date"]) != split["date"]
                or original_tonnes != parse_tonnes(split["fish_tonnes"])):
            raise ValueError(f"Source changed; review split for {row['entry_id']}")
        parts = split["parts"]
        weights = [parse_tonnes(part["fish_tonnes"]) for part in parts]
        if len(parts) < 2 or any(weight is None for weight in weights) or sum(weights) != original_tonnes:
            raise ValueError("Split quantities must preserve the original total")
        for part in parts:
            if not part["key"].strip():
                raise ValueError("Split parts need stable keys")
            result.append(dict(row,
                entry_id=f"{row['entry_id']}-{part['key']}",
                boat_name=part["boat_name"], boat_key=normalize(part["boat_name"]),
                fish_tonnes=part["fish_tonnes"], fish_tonnage_status="user_entered",
                assignment_kind="boat_candidate",
                landing_boat_id="", landing_boat_name="", landing_source_url=""))
    return result


def import_unloading(rows, splits=()):
    required = {"entry_id", "boat_name", "date", "fish_tonnes", "fish_tonnage_status", "include_in_fish_summary"}
    if rows and not required.issubset(rows[0]):
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(required - rows[0].keys())))

    source_row_count = len(rows)
    rows = apply_splits(rows, splits)

    aliases = defaultdict(set)
    canonical_names = defaultdict(set)
    for row in rows:
        boat_id = row.get("landing_boat_id", "").strip()
        if boat_id:
            for value in (row["boat_name"], row.get("boat_key"), row.get("landing_boat_name")):
                if normalize(value):
                    aliases[normalize(value)].add(boat_id)
            if row.get("landing_boat_name", "").strip():
                canonical_names[boat_id].add(row["landing_boat_name"].strip())

    vessels = {}
    entries = {}
    source_groups = {}
    seen_ids = set()
    merged_rows = 0
    for row in rows:
        source_id = row["entry_id"].strip()
        if not source_id or source_id in seen_ids:
            raise ValueError(f"Missing or duplicate entry ID: {source_id}")
        seen_ids.add(source_id)
        name = " ".join(row["boat_name"].split())
        if not name:
            raise ValueError(f"Missing boat name for {source_id}")
        boat_id = row.get("landing_boat_id", "").strip()
        if not boat_id:
            matches = aliases.get(normalize(name), set())
            if len(matches) == 1:
                boat_id = next(iter(matches))
        vessel_id = "fangstdata-" + boat_id if boat_id else identifier("name", normalize(name))
        names = canonical_names.get(boat_id, set())
        canonical = next(iter(names)) if len(names) == 1 else name
        combined = row.get("assignment_kind") == "multiple_or_unclear_boats"
        vessel = vessels.setdefault(vessel_id, {
            "id": vessel_id, "name": display_name(canonical),
            "note": "Felles registrering for flere eller uavklarte fartøy." if combined else None,
            "entries": [],
        })

        start = parse_date(row["date"], "date")
        end = parse_date(row.get("end_date") or start, "end_date")
        if end < start:
            raise ValueError(f"End date precedes start date for {source_id}")
        period = {"start": start, "end": end if end != start else None}
        tonnes = parse_tonnes(row["fish_tonnes"])
        status = row["fish_tonnage_status"]
        tonnage_kind = {
            "landing_reference": "landing", "estimated_average": "estimated",
            "user_entered": "reported", "extracted": "timesheet",
        }.get(status)
        if tonnage_kind is None:
            raise ValueError(f"Unknown tonnage status: {status!r}")
        inclusion = row["include_in_fish_summary"].strip().casefold()
        if inclusion not in {"yes", "no"}:
            raise ValueError(f"Unknown inclusion flag: {inclusion!r}")
        # The owner includes estimated quantities in website totals, even when
        # the source's fish-summary flag excludes those estimates.
        included = tonnes is not None and (inclusion == "yes" or tonnage_kind == "estimated")
        sources = sorted(set(re.findall(
            r"https://fangstdata\.no/offload/\d{4}-\d{1,2}-\d{1,2}/\d+\b",
            row.get("landing_source_url", ""))))
        if tonnage_kind == "landing" and not sources:
            raise ValueError(f"Landing weight has no usable source for {source_id}")
        # A cargo linked to several work rows is one unloading, with all work periods.
        group_key = (vessel_id, tuple(sources)) if tonnage_kind == "landing" else (vessel_id, source_id)
        for source in sources:
            if source in source_groups and source_groups[source] != group_key:
                raise ValueError(f"Overlapping landing references require review: {source}")
            source_groups[source] = group_key
        existing = entries.get(group_key)
        if existing:
            if existing["tonnes"] != (float(tonnes) if tonnes is not None else None) or existing["includeInTotal"] != included:
                raise ValueError(f"Conflicting quantities for the same landing: {sources}")
            if period not in existing["periods"]:
                existing["periods"].append(period)
            merged_rows += 1
            continue
        entry = {
            "id": identifier("unloading", "|".join(sources) if tonnage_kind == "landing" else source_id),
            "periods": [period], "tonnes": float(tonnes) if tonnes is not None else None,
            "tonnageKind": tonnage_kind, "includeInTotal": included,
            "description": None, "sourceUrls": sources,
        }
        entries[group_key] = entry
        vessel["entries"].append(entry)

    for vessel in vessels.values():
        for entry in vessel["entries"]:
            entry["periods"].sort(key=lambda period: period["start"], reverse=True)
        vessel["entries"].sort(key=lambda entry: (entry["periods"][0]["start"], entry["id"]), reverse=True)
    data = {"schemaVersion": 1, "category": "unloading",
            "vessels": sorted(vessels.values(), key=lambda vessel: normalize(vessel["name"]))}
    total = sum((Decimal(str(entry["tonnes"])) for entry in entries.values() if entry["includeInTotal"]), Decimal(0))
    report = {"sourceRows": source_row_count, "splitRowsAdded": len(rows) - source_row_count,
              "vessels": len(vessels), "unloadings": len(entries),
              "mergedLandingRows": merged_rows,
              "estimatedEntries": sum(entry["tonnageKind"] == "estimated" for entry in entries.values()),
              "includedTonnes": str(total)}
    return data, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Reviewed work-history-complete.csv")
    parser.add_argument("--splits", type=Path, default=DEFAULT_SPLITS, help="Owner-confirmed vessel allocations")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "wwwroot/data/vessels/unloading.json")
    args = parser.parse_args()
    splits = json.loads(args.splits.read_text(encoding="utf-8"))
    with args.source.open(encoding="utf-8-sig", newline="") as file:
        data, report = import_unloading(list(csv.DictReader(file)), splits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
