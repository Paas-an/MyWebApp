# Vessel history

`/vessels` uses one shared list component for engineering and unloading. The Info
switch shows summaries beneath boat names and a total-tonnage badge above the
unloading list. Totals include estimates, which remain labelled in the history.
Each boat independently
opens its history, and one Norwegian alphabetical sort controls both lists.

Each list scrolls within a height of `26rem` (about six collapsed rows), capped
at 65% of the viewport height on shorter screens. Adjust `--vessel-list-max-height`
in `VesselList.razor.css` to change the size. Opening a boat keeps its dated history
inside the same scrolling area; the heading, total badge and shared controls stay outside it.

`IVesselHistorySource` separates data access from the page and list. The initial
implementation reads static JSON. A later HTTP API can implement the same
interface without changing the list controls. No backend or Docker runtime is
required for this MVP.

## Updating unloading history

Use the reviewed, complete CSV export, not an unreviewed OCR export:

```powershell
python scripts/import_vessel_history.py "path/to/work-history-complete.csv"
python -m unittest discover -s tests -p "test_*.py"
```

The importer writes `wwwroot/data/vessels/unloading.json`. Commit that file along
with any code changes and publish the site normally. The source CSV and Excel
workbook stay outside the website repository. Only explicitly selected public
fields are exported; payroll, employee details, email metadata, original OCR text
and local file paths are never copied. The Excel workbook was cross-checked
against the supplied CSV by stable entry ID, boat name and tonnes for the first import.

Rules:

- Each documented landing is one unloading. Multiple work rows linked to the
  same landing retain all distinct work periods but contribute cargo weight once.
- The supplied `fish_tonnes` is kept at its exported precision. Period averages
  remain labelled estimates and are included in totals at the owner's request,
  even when their source `include_in_fish_summary` flag is `no`. Other excluded
  weights remain excluded. Blank weight is unknown,
  while zero remains a real value.
- Fangstdata vessel IDs and unambiguous name aliases already present in the
  source join spelling variants. No fuzzy name matching is performed. Unresolved
  names remain as supplied; an ID is a Fangstdata ID, not an IMO number.
- The owner-confirmed split in `unloading-splits.json` replaces the combined
  Bjørnhaug / Bautar row on 2025-09-29 with Bautar (85 tonnes) and Bjørkhaug
  (225 tonnes), both on the same date. Bautar joins its existing vessel history.
  The importer applies this correction automatically while keeping the original
  CSV and Excel payroll records intact. Edit this file to adjust the allocation;
  its parts must add up to the original 310 tonnes. If the original row's name,
  date or weight changes, the importer requires the correction to be reviewed.
- Stable entry IDs, dates, status values and conflicting weights are checked
  before writing. Partially overlapping landing references require review rather
  than being counted twice. A failed import leaves the existing output intact.

## Adding engineering jobs

`wwwroot/data/vessels/engineering.json` intentionally has an empty vessel list
until issue #39 is supplied with records. It uses the same schema:

```json
{
  "schemaVersion": 1,
  "category": "engineering",
  "vessels": [{
    "id": "stable-vessel-id",
    "name": "Actual vessel name",
    "note": null,
    "entries": [{
      "id": "stable-job-id",
      "periods": [{ "start": "2026-09-20", "end": null }],
      "tonnes": null,
      "tonnageKind": null,
      "includeInTotal": false,
      "description": "Actual work performed",
      "sourceUrls": []
    }]
  }]
}
```

This is a format example, not a real job. Dates use ISO `YYYY-MM-DD`, weights are
JSON numbers in metric tonnes, and IDs remain stable across edits. A boat may
appear in both files; its engineering and unloading entries remain separate.

The route's SEO shell is generated with the existing `PublishSeo.ps1` workflow,
and missing `/data/*` URLs return errors instead of the SPA fallback.

## Browser checks

With Playwright available to Node and its Chromium browser installed, start the
site and run the optional interaction checks from another terminal:

```powershell
dotnet run --configuration Release --no-launch-profile --urls http://127.0.0.1:5053
# In a second terminal:
node tests/Vessels.browser.cjs
```

`VESSELS_BASE_URL` overrides the server URL. `PLAYWRIGHT_CHROMIUM_EXECUTABLE`
can select an existing Edge or Chrome executable, and `VESSELS_SCREENSHOT_DIR`
optionally saves desktop and mobile screenshots to an existing directory.
The checks cover shared sorting, Info independent of expansion, keyboard use,
empty and populated engineering lists, mobile overflow, and failed data loads.
Engineering test records are intercepted in the browser and never saved to the
public data file.
