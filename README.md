# corpus-nist-sp800

NIST SP 800 security controls and digital-identity guidance as plain text,
mirrored from NIST GitHub sources for corpus/retrieval use. Two tiers:

- **Prose tier (`sp800-63/`)** — the SP 800-63-3 *Digital Identity Guidelines*
  suite (SP 800-63-3 plus volumes A/B/C) and the SP 800-63 FAQ, as per-section
  Jekyll-source Markdown, kept in the source repositories' own file structure.
- **OSCAL tier (`sp800-53r5/`, `sp800-171r3/`, `sp800-172r3/`, `sp800-218/`,
  `csf-2-0/`)** — NIST OSCAL catalogs split to one text file per control.

Republished courtesy of the National Institute of Standards and Technology.

## Pinned sources

| Source | Commit (pinned) |
|---|---|
| https://github.com/usnistgov/800-63-3 | `7dee3cad9d429dcefc27ba1976a55704bff0800a` |
| https://github.com/usnistgov/800-63-FAQ (default branch `nist-pages`) | `9b8e6a251bab3226cd315ed69d56f3c2f5f3cc93` |
| https://github.com/usnistgov/oscal-content | `78650f02ad9321bb7b817846f8fbd4f2bcd620de` |

## Licence

`LICENSE-63` (verbatim from `usnistgov/800-63-3/LICENSE.md`, identical in the
FAQ repo) — NIST Technical Series Publications:

> All works authored by NIST employees are not subject to Copyright protection
> within the United States; foreign rights are reserved. To the extent NIST may
> assert rights outside of the United States, the public is granted the
> non-exclusive, perpetual, paid-up, royalty-free, worldwide right to reprint
> works in all formats including print, electronically, and online, and in all
> subsequent editions, and derivative works. Please use the recommended
> citation format below followed by “Republished courtesy of the National
> Institute of Standards and Technology.” Some works published by NIST may
> have been written by third parties and may be subject to copyright protection.

`LICENSE-oscal` (verbatim from `usnistgov/oscal-content/LICENSE.md`):

> As a work of the United States government, this project is in the public
> domain within the United States.
>
> Additionally, we waive copyright and related rights in the work worldwide
> through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

## Contents and file counts

| Path | Document | Files | Notes |
|---|---|---:|---|
| `sp800-63/sp800-63-3/` | SP 800-63-3 Digital Identity Guidelines | 11 | per-section Markdown, verbatim |
| `sp800-63/sp800-63a/` | SP 800-63A Enrollment and Identity Proofing | 12 | " |
| `sp800-63/sp800-63b/` | SP 800-63B Authentication and Lifecycle Management | 14 | " |
| `sp800-63/sp800-63c/` | SP 800-63C Federation and Assertions | 14 | " |
| `sp800-63/faq/` | SP 800-63 FAQ (per-question files) | 41 | `63A/` `63B/` `63C/` `general/` |
| `sp800-53r5/` | SP 800-53 Rev. 5 catalog (OSCAL 5.2.0) | 324 | one file per control; enhancements inside the parent file (872 total) |
| `sp800-53r5/baseline-*.txt` | LOW / MODERATE / HIGH / PRIVACY baselines | 4 | selection sets: control-id lists |
| `sp800-171r3/` | SP 800-171 Rev. 3 catalog (OSCAL 1.1.0) | 130 | `3.1.1.txt` … |
| `sp800-172r3/` | SP 800-172 Rev. 3 catalog (OSCAL 1.0.0) | 115 | `3.1.1E.txt` … |
| `sp800-218/` | SP 800-218 SSDF catalog (source `ver1`, OSCAL 1.0.0) | 19 | one file per practice; tasks inside (`PO.1.txt` …) |
| `csf-2-0/` | Cybersecurity Framework 2.0 catalog (OSCAL 1.2.0) | 34 | one file per category; subcategories inside (`GV.OC.txt` …) |

Prose tier: 92 Markdown files. OSCAL tier: 626 text files (622 control + 4
baseline). Total 718, plus licences, this README, and the splitter.

Shape rule: no file exceeds 150 KB. Largest emitted file is
`sp800-53r5/SA-8.txt` at 64,771 B.

## Control-file format (OSCAL tier)

Each control file carries: the control `id`, `title`, family (with the
function/family overview where present), `class`, the full **statement** text
(rendered as a labeled outline; `{{ insert: param, … }}` rendered as
`[label]` or `[Selection (how-many): a; b]`), the **Parameters** (label,
selection choices, guidelines), resolved **References** from the catalog
back-matter, and all enhancement/child controls (`Enhancement AC-2(3)
(ac-2.3) - …` / `Child control PO.1.1 - …`).

Deliberately dropped from the OSCAL render: `assessment-objective`,
`assessment-method`, and `assessment-objects` parts (SP 800-53A assessment
content), and the XML/YAML and `-min` JSON variants of each source file.

File-name conventions: SP 800-53 ids uppercased (`ac-2` → `AC-2.txt`);
SP 800-171/172 ids stripped of their `SP_800_1xx[_3_0_0_]` prefix with
zero-padding removed (`SP_800_171_03.01.01` → `3.1.1.txt`,
`SP_800_172_3_0_0_03.01.01E` → `3.1.1E.txt`); SP 800-218 and CSF ids kept
verbatim (`PO.1.txt`, `GV.OC.txt`). The raw OSCAL id is always the first line
of the file. Baseline id lists reference enhancements as `AC-2.3`, which lives
inside `AC-2.txt`.

Prose tier drops only Jekyll/site machinery (`_config.yml`, `_layouts/`,
`_includes/`, `Gemfile`, `docker-compose.yml`, `assets/`, `static/`,
generated `index.html`, Liquid page assemblers) and binary media; the
per-section publication text is copied verbatim, FAQ collection directories
renamed from `_63B/` etc. to `63B/` only.

## Regeneration

```sh
git clone --depth 1 https://github.com/usnistgov/800-63-3
git clone --depth 1 https://github.com/usnistgov/800-63-FAQ
git clone --depth 1 https://github.com/usnistgov/oscal-content
python3 split_oscal.py --oscal-content ./oscal-content --out .
# then copy the Markdown per the table above (prose tier is a plain file copy)
```

`split_oscal.py` is Python 3 stdlib only; it enforces the 150 KB shape rule
and exits non-zero if any emitted file exceeds it. Re-pin by checking out the
commit listed above in each clone and re-running.
