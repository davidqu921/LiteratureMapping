# Data format and counting rules

The reusable map generator consumes an explicitly coded CSV and a JSON configuration. It does not read Excel directly, infer labels from papers, or decide which publications belong in a corpus. Export the agreed coding sheet as CSV before running the generator.

## Source hierarchy

| Source | Role | Editing policy |
| --- | --- | --- |
| `data/lit-map 2026s sycophancy.xlsx` | Human coding and available screening records; primarily **Mapping Discrepancies**, plus **FINAL MAP** | Preserve decisions and their provenance; document proposed corrections separately. |
| `data/lit-map 2026s sycophancy - FINAL MAP.csv` | Export used by the general mapping tools | Update only after approved coding changes. |
| Row 3 of the FINAL MAP CSV | Supplied attribute definitions | Preserve definitions alongside the coding. |
| `docs/EVIDENCE_AUDIT.md` | Additional full-text checks and suggested coding reviews | Keep separate from original human labels. |
| `output/` | Derived counts, citation lists, and reports | Regenerate from the relevant inputs. |

The actual workbook tab is **Mapping Discrepancies** (plural). Its 34 mapped rows comprise 31 retained records and three marked `DELETE`. The retained records and all 13 shared fields match FINAL MAP. The earlier mapping has 15 fields: FINAL MAP omits `Human - general` and `Human - Student`. These are schema differences, not inferred absences of evaluation. See [the evidence audit](EVIDENCE_AUDIT.md).

## General CSV contract

- Encoding: UTF-8, with or without a BOM. Use comma delimiters and standard CSV quoting for titles containing commas or quotes.
- Unit: one publication record per nonempty data row. Keep all header and data rows at the same width. Completely empty data rows are ignored.
- Keys: one required, unique citation key per record. Allowed characters are letters A-Z/a-z, digits, and `: . _ / -`. The key column name is case-sensitive. Normalize DOI keys before export; the general reader checks exact duplicate keys, not case-insensitive DOI equivalence or duplicate publications under different identifiers. Crossref retrieval additionally requires DOI-form keys; arbitrary example keys work for mapping only.
- Metadata: configure the key, title, and URL column names. The general reader requires the key column; titles and URLs are optional, but titles are needed for useful bibliography checks. Metadata columns are excluded from attribute groups.
- Marks: by default, `X` or `x` means marked and an empty cell means unmarked. Leading/trailing whitespace is stripped. Unconfigured values such as `?`, `Yes`, `0`, and `N/A` fail validation.
- Groups: at least two nonempty groups, each with a unique group title. Every attribute must belong to one group. Blank separator columns may be present, but must remain empty in data rows.
- Multi-label data: a publication can have several attributes within and across groups. Do not duplicate a publication row to represent multiple labels.

`positive_values` and `negative_values` configure accepted mark tokens, case-insensitively. The name `negative_values` is a parser convention: it means **unmarked**, not verified absence. The current format does not preserve separate unknown, missing, and not-applicable states. Do not map these states to blank unless that information loss is intentional and documented; extend the format before analyses that require this distinction.

## FINAL MAP layout

The sycophancy export has 17 columns, three header rows, and 31 publication rows.

| Position | Content |
| --- | --- |
| Row 1 | Metadata names and group headings. A heading carries right until the next nonempty group heading. |
| Row 2 | Attribute names. |
| Row 3 | Attribute definitions; preserved in the CSV and skipped when counting publication records. |
| Row 4 onward | Publication metadata and marks. |
| Columns A-C | `URL`, `Title`, `Key` (DOI). |
| Column D | Empty separator. |
| Columns E-G | `Human - Specialist`, `Human - Authors`, `AI - prompted`. |
| Columns H-L | `Hallucination Agreement`, `Bias Agreement`, `Obsequiousness`, `Stance Change`, `Failure to challenge/trying to get along`. |
| Columns M-Q | `None`, `User opinion`, `User action`, `System performance`, `User performance`. |

`configs/final_map.json` uses **1-based** row numbers:

```json
{
  "metadata_header_row": 1,
  "group_header_row": 1,
  "attribute_header_row": 2,
  "data_start_row": 4,
  "key_column": "Key",
  "title_column": "Title",
  "url_column": "URL",
  "unnamed_group_title": "Evaluation method",
  "group_titles": {
    "Definition of Sycophancy (what exactly do they mean by sycophancy)": "Definition of sycophancy",
    "Outcomes (Are they measuring the impact of sycophancy on something else?)": "Outcomes"
  },
  "positive_values": ["X"],
  "negative_values": [""]
}
```

The first group heading is missing in this CSV. `unnamed_group_title` supplies the display label `Evaluation method`, and the report records a warning. It does not infer group boundaries from attribute meanings. Add group headings or use explicit groups if several unnamed groups must be distinguished. `group_titles` only shortens display headings.

In grouped-header mode, the same attribute name may occur in different groups; columns remain distinct internally. Repeated attribute names within one group fail validation.

## Reusing the generator with another corpus

For a single-header CSV, define groups explicitly, as in `configs/sample.json`. A minimal example is:

```csv
key,Title,URL,Agreement,Flattery,Trust,Task score
demo01,Example publication,,X,,X,
demo02,Second example,,,X,,X
```

```json
{
  "attribute_header_row": 1,
  "data_start_row": 2,
  "key_column": "key",
  "groups": [
    {"title": "Behavior", "attributes": ["Agreement", "Flattery"]},
    {"title": "Outcome", "attributes": ["Trust", "Task score"]}
  ]
}
```

Save these as `my_map.csv` and `my_config.json`, then run from the repository root:

```sh
python -m scripts.csv_to_latex my_map.csv --config my_config.json --out build/my_map
```

In explicit-group mode, each referenced attribute name must occur exactly once in the header. For new grouped exports, add attributes and group headings in the CSV and adjust the configuration; no hard-coded column slices need changing in the general generator. This flexibility does **not** apply to the corpus-specific `scripts/analyze_map.py`.

The supplied `examples/sample_lit_map.csv` has 17 records and three groups (Population, Evaluation, Intervention). It is a historical education example, not part of the sycophancy corpus. Its original label `Accessability` is retained to match its configuration.

## Output contract

For G groups, the generator creates G(G-1)/2 unordered group pairs in input order. For each pair:

| File | Content |
| --- | --- |
| `map_NN_counts.csv` | Count matrix with row and column labels. |
| `map_NN_keys.csv` | Matching citation keys, separated by semicolons within each cell. |
| `map_NN_heatmap.tex` | Count matrix with purple shading. |
| `map_NN_citations.tex` | Same intersections as citation lists; a dash for an empty intersection. |

For FINAL MAP, `map_01` is evaluator x behavior (3 x 5), `map_02` is evaluator x outcome (3 x 5), and `map_03` is behavior x outcome (5 x 5): 55 cells in total.

For attribute membership sets A and B, a cell is `|A intersection B|`. Shading is rounded `100 * cell_count / N`, where N is all input publications (31 here). It is not a conditional percentage, effect size, significance test, or measure of behavior prevalence. Zero means no shared marked record in this coding. Multi-label overlap means cells and marginal frequencies cannot be summed to recover N.

The output directory also contains:

| File | Role |
| --- | --- |
| `main.tex` | A4 landscape review document with all heatmaps, citation tables, and references. |
| `main_heatmaps.tex` | A4 portrait document with count heatmaps only. |
| `references_draft.bib` | Unverified fallback made from CSV metadata. |
| `report.json` | Input path, configuration, counts, group/column mapping, unmarked records, warnings, and bibliography status. |
| `overleaf.zip` | Generated LaTeX and bibliography sources for compilation. |

Python generation does not compile or refresh PDFs. Existing `references.bib` is preserved and used when present; all other named generated files may be replaced. Avoid keeping manual edits only in generated tables. `tabularx` wraps text to the available width, but substantially larger maps still need layout review and possible panel splitting.

## Corpus-specific statistics

`scripts/analyze_map.py` expects the FINAL MAP group and outcome names. It writes `findings_counts.csv` and `findings_evidence.json`, including DOI membership lists and an input hash. The main analysis retains all 31 records, including two identified reviews; any sensitivity analysis needs an explicit alternative input and denominator.

- Coverage uses publication records as the denominator, not participants, experiments, or independent studies.
- `any user outcome` is the set union of `User opinion`, `User action`, and `User performance`. Intersections with system performance are computed from these record sets, not by adding heatmap cells.
- `User opinion` includes opinions/reactions and can include issue attitudes; it must not be relabeled entirely as perceptions or trust. `User performance` denotes task-level performance in the codebook.
- `None` is an explicit code for measuring sycophancy without an additional impact measure. It is not a missing value or evidence of a null effect. The findings script reports conflicts where `None` appears together with another outcome; review these before interpreting the results.
- `System performance` is a coding category, not a guarantee of objective accuracy measurement. Follow the full-text evidence when interpreting particular papers.
- A publication marked in two outcome categories need not have tested their association or a causal relation.

The tools do not resolve preprint/publication duplicates, supply missing search history, or silently change human coding after a full-text audit. Keep corrections, extractions, and external related work distinct from the statistical corpus.
