# LiteratureMapping

**Reproducible literature maps from human-coded publication attributes.**

LiteratureMapping turns a coded CSV into pairwise count heatmaps, citation tables, and traceable record lists. It supports grouped spreadsheet exports, validates their structure, and produces LaTeX sources that researchers can inspect, adapt, and compile locally or in Overleaf. Optional Crossref retrieval supplies DOI-verified bibliography metadata.

The current application maps **AI sycophancy** across behavior definitions, evaluator categories, and outcome measures. This code artifact supports a secondary-research project prepared for an AAAI-27 workshop: human coding determines membership and labels; the software calculates and displays their coverage.

[All-panel heatmap](output/final_map/main_heatmaps.pdf) · [Data specification](docs/DATA_FORMAT.md) · [Evidence audit](docs/EVIDENCE_AUDIT.md)

## Workflow

```text
Human coding workbook
  Mapping Discrepancies -> retained records -> FINAL MAP CSV
                                               |
                         JSON group configuration
                                               |
                            CSV validation and set intersections
                              /                |                \
                      Count heatmaps    Citation/key tables    Audit reports
                              \                |                /
                               LaTeX review documents / Overleaf

DOI keys -> optional Crossref retrieval -> checked BibTeX metadata
Full-text checks -> separate evidence audit and proposed coding corrections
```

The general generator discovers group boundaries from configured headers, retains zero-count categories, and sizes tables to the available LaTeX width. It does not screen or code papers automatically. Counts describe the supplied corpus; shading does not represent an effect size or a causal relationship.

## Repository map

| Path | Purpose |
| --- | --- |
| [`scripts/`](scripts/) | Reusable CSV-to-LaTeX generator, sycophancy-specific findings analysis, and optional Crossref retrieval. |
| [`configs/`](configs/) | Group/column configurations for the current corpus and the example dataset. |
| [`data/`](data/) | Original sycophancy workbook and FINAL MAP CSV export. |
| [`examples/`](examples/) | Runnable 17-record education example and the earlier spreadsheet template. |
| [`output/final_map/`](output/final_map/) | Existing sycophancy maps, count/key matrices, bibliography cache, and reports. |
| [`output/sample/`](output/sample/) | Existing outputs for the example dataset. |
| [`docs/`](docs/) | Input/output specification, counting rules, evidence audit, and unresolved research decisions. |
| [`tests/`](tests/) | Offline regression tests for parsing, counts, bibliography handling, and retrieval constraints. |
| [`legacy/`](legacy/) | Preserved original table fragments and poster-format artifacts, formerly in `files/`. |
| `build/` | Ignored scratch directory used by the commands below; generated on demand. |

The general scripts live under `scripts/`, and example inputs under `examples/`. Run module commands from the repository root. Explicit relative paths are interpreted from the current working directory. Manuscript development stays local in the Git-ignored `paper/` directory; it is not required to run this artifact.

## Requirements and quick start

The mapping, findings, and bibliography scripts use the **Python standard library only**. The current checks were run with Python **3.14.6**. No API key is required.

From a terminal in `LiteratureMapping`:

```sh
python -m scripts.csv_to_latex --out build/sample
python -m unittest discover -s tests -v
```

The first command reads `examples/sample_lit_map.csv` and `configs/sample.json`, then creates three map pairs and `build/sample/overleaf.zip`. The second runs the 12 offline regression tests. The example is about education and is separate from the sycophancy corpus.

For PDFs, install a TeX distribution with PDFLaTeX and BibTeX, or upload the generated source ZIP to Overleaf. Maps use standard packages including `tabularx`, `array`, `xcolor`, `geometry`, and `natbib`. LaTeX compilation is offline once its packages are installed. Core map generation needs neither LaTeX nor third-party Python packages.

## Reproduce the sycophancy maps

The current human coding is in `data/lit-map 2026s sycophancy.xlsx`, principally **Mapping Discrepancies**. The retained 31 records and 13 shared attributes match its FINAL MAP tab and the CSV export. The original workbook also contains earlier evaluator fields and screening records; consult the audit before interpreting missing marks.

Generate a fresh copy without replacing the existing review outputs:

```sh
python -m scripts.csv_to_latex "data/lit-map 2026s sycophancy - FINAL MAP.csv" --config configs/final_map.json --out build/final_map
python -m scripts.analyze_map "data/lit-map 2026s sycophancy - FINAL MAP.csv" --config configs/final_map.json --out build/final_map
```

Expected results are **31 publication records**, **three attribute groups**, and **55 pairwise cells**:

| Pair | Rows | Columns | Cells |
| --- | --- | --- | ---: |
| `map_01` | Evaluator categories | Sycophancy behavior labels | 15 |
| `map_02` | Evaluator categories | Outcome categories | 15 |
| `map_03` | Sycophancy behavior labels | Outcome categories | 25 |

Each pair has a count CSV, a CSV of contributing citation keys, a heatmap `.tex`, and a citation-table `.tex`. `report.json` records configuration and validation warnings; `findings_evidence.json` records outcome unions/intersections, their DOI lists, and the input hash. The unnamed first-group warning is expected for this export: the configuration supplies the label `Evaluation method`.

All heatmaps use the same purple scale, `cell count / 31`. A publication may appear in multiple cells. The findings script computes set unions at the publication level; adding overlapping heatmap cells would give incorrect totals.

The current original coding yields system performance in **12/31**, user opinion in **11/31**, user action in **8/31**, and user task performance in **4/31** records. At least one user outcome is marked in **15/31**, and system plus any user outcome in **1/31**. These are coding-based coverage findings, with specific full-text qualifications and proposed reviews in [the evidence audit](docs/EVIDENCE_AUDIT.md).

Generation updates sources and reports, **not PDFs**. It preserves an existing `references.bib`; other generated files with the same names are replaced. Review new outputs before promoting them to `output/final_map/`.

## Retrieve and use real BibTeX

The repository contains cached Crossref JSON and BibTeX for all 31 corpus DOIs. Rebuild the bibliography from this cache with:

```sh
python -m scripts.fetch_bibtex "data/lit-map 2026s sycophancy - FINAL MAP.csv" --config configs/final_map.json --out output/final_map
```

Complete cache hits make no network requests. Missing entries trigger HTTPS GET requests to `api.crossref.org`, using the DOI and a software user-agent, without sending coding cells or documents. The client makes serial requests at least one second apart, observes rate-limit/retry headers, limits response sizes, and rejects redirects outside Crossref HTTPS. It uses the [free public Crossref service](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/), with no credentials or paid Metadata Plus subscription. Crossref receives requested DOIs and normal connection information on a cache miss.

The script checks DOI agreement in both JSON and BibTeX, required bibliography fields, title correspondence, and unsafe TeX commands. It preserves raw responses with retrieval provenance, writes `crossref_audit.csv` and `crossref_report.json`, and produces:

- `references_crossref.bib`: merged Crossref entries with citation keys aligned to the CSV.
- `references_crossref_latex.bib`: the same metadata with LaTeX-compatible field formatting, protected title case, and explicit month names.

It does not replace `references.bib` automatically. If any entry fails, the report records the failure and the merged bibliography is not replaced. Inspect the report, then copy the approved `references_crossref_latex.bib` to `build/final_map/references.bib` and rerun the map-generation command to include it in the source ZIP. Preserve any bibliography you have edited before replacing it. Crossref metadata is not a substitute for checking a paper's methods or findings.

## Compile and inspect the maps

Upload `build/final_map/overleaf.zip` as a new Overleaf project. Choose PDFLaTeX and either `main.tex` (heatmaps, citation tables, and bibliography) or `main_heatmaps.tex` (counts only). If no checked bibliography has been installed, the review document uses the explicitly unverified CSV-derived `references_draft.bib`.

For local compilation, after installing the bibliography and regenerating the sources:

```sh
cd build/final_map
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main.tex
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error main_heatmaps.tex
cd ../..
```

The generated documents are review layouts (A4 landscape for full maps, A4 portrait for heatmaps). Existing `output/final_map/main_heatmaps.pdf` contains all three panels. Check the destination venue's layout and embedded-font requirements before incorporating generated tables into a publication.

## Adapt the design to another review

Start with [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md): it specifies header rows, grouping, keys, mark tokens, missing-value semantics, and output schemas. Supply a CSV and JSON configuration to `scripts.csv_to_latex` for new corpora. Group boundaries belong in data/configuration rather than Python column slices.

`scripts/analyze_map.py` is specific to the sycophancy schema. Adapt its outcome definitions, denominators, and validation checks explicitly before using it for another research question. Keep human decisions, added full-text extractions, derived outputs, and external background literature distinguishable.

The existing tests check all 55 original intersections against raw CSV data, category boundaries, zero-count attributes, malformed inputs, preservation of manual bibliographies, outcome partitions, DOI validation, cached retrieval, and redirect constraints. Review compiled pages for readable labels, resolved citations, and unclipped tables.

## Research scope and reuse

This artifact makes an existing coding map inspectable and reproducible. It does not establish complete field coverage, independently recode all papers, or recover missing search and adjudication history. Its unit is a publication record, and the corpus includes review articles. Proposed corrections are documented separately rather than silently incorporated into the counts.

No project-wide reuse license has yet been specified. Use the linked source records and evidence audit when describing the work.
