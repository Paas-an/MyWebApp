# Original-data audit — 7 October 2026

The published history still contained the original OCR names and dates and
incomplete landing weights. This update applies the reviewed corrections and
checks the quantities against Fiskeridirektoratet catch-year files for 2020–2025.
The 2022 and 2023 originals are preserved September snapshots; the other four
annual files were downloaded on 7 October. All 6,173,660 source lines were scanned.

The original export contains 248 work rows linked to 62 unchanged PDF attachments
in 92 archived messages. The public result has 48 vessels and 246 unloading entries:
three Langenes workdays form one owner-confirmed cargo, two Ramoen work rows share
another cargo, and one owner-confirmed row is split between Bautar and Bjørkhaug.
All work dates are retained. Original emails, PDFs and workbooks remain unchanged.

Confirmed corrections include Tangenes to Langenes; Norditar to Nordstar;
Prawn to Olympic Prawn; Kågtind to Kågtind II; Sara Karin to 2 July 2025;
Atlantic Star to 9–10 July 2025; and Lodairo's timesheet amount from 420 to 820 tonnes.
Lodairo remains a timesheet amount, not a confirmed original-register quantity.

The Langenes cargo on 29 June–1 July 2022 totals 418.64 tonnes and counts once.
Gadus Poseidon on 6 October 2025 has 470.11 tonnes of original product weight;
the old 337.71-tonne figure omitted positive-product lines with zero round weight.
Synes on 3 January 2025 is found in catch-year 2024, at 210.09 tonnes.
Arctic Swan on 7 January 2022 has 673.00 tonnes across catch years 2021 and 2022.

## Quantity decisions

Product weight is summed in kilograms, including products with zero round weight,
then divided by 1,000 and rounded once per cargo to two decimals. Vessel IDs,
dates and municipalities remain distinct; names are compared without case.
Original duplicate lines or mixed document versions stop indexing.

The publication retains only corroborated amounts as `landing`: the official
quantity agrees with the written timesheet within one tonne (whole-tonne source
precision), the previously selected amount agrees within 0.011 tonne where no
written weight exists, or the cargo has an explicit owner confirmation as with
Langenes. The one-tonne rule is an audit tolerance, not a guarantee about personal
unloading scope. No unmatched date-only candidate replaces an estimate.

Where quantities disagree, the written timesheet amount is retained if available.
Otherwise the previous estimate or unresolved reference amount is kept under its
own label. Owner-provided values remain owner-provided. Original-data links on
unresolved rows are comparison sources, not evidence that the displayed amount
is a verified register amount. Notes show both quantities and preserve conflicts.

| Public quantity category | Entries |
| --- | ---: |
| Original product weight | 179 |
| Timesheet amount | 25 |
| Unresolved amount | 34 |
| Owner-reported amount | 5 |
| Estimate | 3 |

The displayed sum is **74,759.31 tonnes**, including all five categories. It is
labelled as a sum of listed amounts, not a wholly verified personal unloading
total. Senja on 4 January 2022 and Ramoen on 22 April 2025 still require cargo-scope
confirmation. Langøy on 18 September 2023 retains its estimate because the earlier
comparison included weight without a confirmed landing municipality.

The private `publication-changes.json` records each source ID, before/after quantity,
decision and original document references. It is excluded from this repository,
together with employee information, pay and email metadata.

The importer accepts several catch-year citations for one landing and preserves
municipality in cargo identity. Regression tests cover year boundaries, shared
cargos, uncertainty labels, name casing, duplicate references and private-field
exclusion. Engineering history is unchanged and matches the supplied workbook.

Source: [Fiskeridirektoratet original data and documentation](https://www.fiskeridir.no/statistikk-tall-og-analyse/data-og-statistikk-om-yrkesfiske/apne-data-fangstdata-seddel-koblet-med-fartoydata).
