# Vessel data

`/vessels` reads `wwwroot/data/vessels/engineering.json` and `unloading.json`.
`VesselHistory.cs` defines the shared public format. Engineering descriptions
remain in the source workbook and are not exported or displayed.

## Engineering history

Edit `assets/Enginering table.xlsx` or the `additionalVisits` records in
`engineering-import-notes.json`, then regenerate the public data:

```powershell
python -m pip install -r scripts/requirements-engineering.txt
python scripts/import_engineering_history.py
python -m unittest discover -s tests -p "test_*.py"
```

Commit the changed source and `wwwroot/data/vessels/engineering.json` together.
Editing the workbook or notes alone does not update the website.

- The first worksheet uses `båt`, `dato` and `info` headers; an `id` column is optional.
  Use `--sheet "Name"` to select another worksheet.
- `dato` accepts an Excel date, `YYYY-MM-DD`, or `YYYY-MM-DD YYYY-MM-DD` for one
  continuous visit. A period counts as one assignment.
- Boat names and dates are required. Blank rows are ignored. Invalid dates,
  formula cells and duplicate visit IDs stop the import.
- Names are grouped without case or extra whitespace; different spellings stay
  separate. Keep an explicit `id` when correcting a visit's date. Separate jobs
  on the same boat and date require distinct IDs.
- For an undated confirmed visit, supply `dateUnknown: true` and a stable `id`.
  It counts as an assignment and displays `Dato ikke registrert`. When the date
  is known, add `dato`, remove `dateUnknown`, keep `id`, and rerun the importer.
- Move supplemental visits into Excel by removing their matching notes records
  in the same update, so they are not counted twice.

The notes also supply dates for MV Atlantic's original undated image row,
correct MV Scotia's `202608-25` typo, and extend Benjaco's September visit through
16 September. Keep these overrides until their corresponding workbook rows are
corrected. The workbook stays outside `wwwroot`.

## Unloading history

Use the reviewed publication CSV, not an earlier OCR export. The private source
CSV is kept outside this repository.

```powershell
python scripts/import_vessel_history.py "path/to/work-history-publication.csv"
python -m unittest discover -s tests -p "test_*.py"
```

Commit the generated `wwwroot/data/vessels/unloading.json` after importing.
Original emails, payroll records and source workbooks stay outside the website.
Only selected public fields and reviewed `public_note` values are exported.

- A shared cargo counts once while retaining all distinct work periods.
  Vessel IDs, landing dates and municipalities identify official references;
  a shared annual dataset URL does not merge separate landings.
- Weights use metric tonnes. Blank means unknown; zero is a real value.
  Estimates are labelled and included in totals. Other excluded weights remain excluded.
- Unresolved quantities retain the `Uavklart mengde` label. A vessel's registered
  landing is not necessarily the amount unloaded during one assignment.
- `unloading-splits.json` holds the confirmed Bautar/Bjørkhaug allocation.
  Its parts must still add up to the original cargo weight.
- Duplicate source IDs, invalid periods, overlapping references and conflicting
  weights fail validation before the output is replaced.

## Display

Both lists use Norwegian alphabetical order. The Info switch shows assignment
counts and weight summaries. Engineering dates remain separate from unloading
history, even when a vessel appears in both lists.

`--vessel-list-max-height` in `VesselList.razor.css` controls list height (`26rem`,
capped at `65vh`). Expanded history stays inside the scrolling area.
