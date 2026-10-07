# Unloading history audit — 23 September 2026

Historical audit snapshot. Its proposed data was not published at the time and
its 72,908.71-tonne total is superseded by `original-data-audit-20261007.md`.
Several Fangstdata-based reference amounts below proved incomplete when checked
against all relevant original catch-year files. Do not regenerate current data
from this September snapshot alone.

The previous table contained OCR errors in vessel names, work dates and tonnage,
and lacked 2023 landing references. The corrected import covers 248 work rows
from 92 archived emails and 62 visually reviewed PDF attachments. It produces
246 unloading entries across 48 vessels. Three Langenes work rows share one
cargo, and two Ramoen rows share another;
one owner-confirmed row is allocated to two vessels.

47 source rows change name, date or quantity. Key corrections:

- Tangenes → Langenes, 24 July 2023; 335 tonnes in the timesheet agrees with
  335.9604 tonnes of registered product weight.
- Norditar → Nordstar; the owner confirmed 4 September 2025, with the landing
  recorded on 5 September. Senja's owner-confirmed work date is 4 January 2022.
- Sara Karin moves from 2 May to 2 July 2025. Atlantic Star moves from
  9 November to 9–10 July 2025; its documented 528 tonnes replaces an average.
- Prawn is Olympic Prawn. Kågtind is identified as Kågtind II using the date,
  vessel identity and the 505.551-tonne landing on the following day.
- Lodairo's timesheet says 820 tonnes; 420 was an OCR error.
- 2023 references use the [Fiskeridirektoratet dataset](https://register.fiskeridir.no/uttrekk/fangstdata_2023.csv.zip).
  Ten of twelve estimates are replaced by documented quantities.

The owner confirmed that Ramoen on 2 October 2025 and Nesbakk on 5 February
2022 included fish unloading. For the two email/PDF conflicts, the timesheet
and registered landing support Langøy/Harhaug I on 18 September 2023 and
Gadus Poseidon on 6 October 2025.

On 24 September, the owner confirmed that Langenes on 29 June–1 July 2022
was one continuous unloading with freezer-related waiting time. The official
[2022 dataset](https://register.fiskeridir.no/uttrekk/fangstdata_2022.csv.zip)
contains 33.287 tonnes on 30 June and 385.3514 tonnes on 1 July, including
head products missing from the Fangstdata.no totals. The combined 418.64 tonnes
replaces the separate 17.02- and 197.31-tonne entries and counts once. Identity
is checked by vessel ID 1986003853, callsign JXJU and municipality Ålesund.
Unrelated vessels with the same name are excluded. Name comparisons ignore case.

The total changes from 74,258.12 to 72,908.71 tonnes. It still includes two
clearly labelled estimates: Senja on 4 January 2022 (499.33 tonnes) and Ramoen
on 22 April 2025 (1,010.03 tonnes). Seven measured quantities differ materially
from the compared register amounts and remain as timesheet quantities. Owner
quantities and the Bautar/Bjørkhaug allocation are preserved. Public row notes
explain these limits; the total is not presented as wholly register-verified.

Registered product weight is the sum of product kilograms divided by 1,000,
not round weight. A vessel's full landing does not by itself prove an individual's
unloaded volume. The [official data documentation](https://www.fiskeridir.no/statistikk-tall-og-analyse/data-og-statistikk-om-yrkesfiske/apne-data-fangstdata-seddel-koblet-med-fartoydata)
describes the annual data and its source registers. Local audit snapshots retain
the source URLs, vessel identities, landing dates, documents and comparison
amounts. No emails, payroll records or employee data are published.

Validation: Python importer tests (including annual-dataset cargo identity,
overlap rejection and private-field exclusion), Release build, and browser
verification of dates, quantities, source links and notes.
