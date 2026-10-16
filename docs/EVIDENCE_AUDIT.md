# Evidence audit of the sycophancy map

This English record consolidates the earlier findings note and the evidence audit dated **14 October 2026**. Documentation was reorganized on 16 October 2026; that date is not a literature-search date. The manuscript is [From Sycophantic Behavior to User Consequences: An Evidence Audit of a Literature Map](../paper/main.pdf).

The study is secondary research on a bounded, manually coded corpus. Original labels, additional full-text extraction, and external related work remain separate. No new model experiment, user experiment, benchmark, or automatic recoding is part of this artifact.

## Corpus and recoverable workflow

The main human-coding source is `data/lit-map 2026s sycophancy.xlsx`, primarily **Mapping Discrepancies**. Its retained records match the workbook's **FINAL MAP** tab and the project CSV on all 13 shared attributes. Every exported FINAL MAP cell matches the CSV; `paper/data/final_map.csv` is a frozen copy. See [workbook_audit.json](../paper/generated/workbook_audit.json).

- **All Papers:** 395 candidate rows, not 395 unique publications. There are 391 normalized keys, including the invalid key `x` on three rows and duplicate DOI records.
- **INCEXC A/B:** 395 decisions per sheet, with three distinct named screeners on each sheet (six overall). Current A decisions are 30 Include / 365 Exclude; B decisions are 33 / 362. Three current decisions differ. The workbook does not establish whether these are initial independent decisions or edited values; they cannot support an initial agreement rate or kappa.
- **Mapping A/B and Mapping Discrepancies:** 34 mapped records, of which 31 are retained and three marked `DELETE`. Full deletion rationales are not recoverable. The current A/B labels for the final 31 records agree on all 15 earlier fields, but this is not evidence of 100% initial coding reliability.
- **Unresolved screening transition:** `10.1145/3774904.3792506` is currently Exclude in both screening sheets but included in FINAL MAP. It remains in the final corpus; its inclusion history needs author clarification.
- **Query Validation:** conference-session checks are present, but the actual executed search strings, dates, and complete database protocol cannot be recovered. Publisher links do not establish how the original search was performed.

The earlier mapping has five evaluator categories; FINAL MAP retains three. All **12** records unmarked in the final evaluator group have `Human - general` and/or `Human - Student` marked in the earlier mapping. They must not be described as papers with no evaluation method. Why the two columns were omitted remains unresolved.

Counting uses **publication records**, not independent studies, participants, or effects. The final 31 have no duplicate normalized DOI keys or duplicate normalized complete Crossref titles. This check does not establish independence of their samples or empirical evidence. Two included records are identified reviews (`10.1145/3703155` and `10.1145/3776734.3794532`); the manuscript keeps them in the main map and reports a sensitivity analysis excluding them. The remaining 29 are not automatically certified as primary studies.

## Findings supported by the original coding

The source fields and record-level membership lists are in [analysis.json](../paper/generated/analysis.json), [coded_records.csv](../paper/generated/coded_records.csv), and [codebook.csv](../paper/generated/codebook.csv). All percentages below use N = 31 unless another denominator is stated. Blank means unmarked, not confirmed absence or not applicable. The data contain no explicit N/A category.

| Outcome field | Marked records | Percentage | Intersection with system performance |
| --- | ---: | ---: | ---: |
| System performance | 12 | 38.7% | 12 |
| User opinion | 11 | 35.5% | 1 |
| User action | 8 | 25.8% | 0 |
| User performance | 4 | 12.9% | 0 |
| None | 5 | 16.1% | 0 |
| Any user outcome: union of opinion, action, performance | 15 | 48.4% | 1 |

**Limited co-coverage:** the mutually exclusive partition is 14 user-only, 11 system-only, one both, and five neither. Joint coverage is 1/31 (3.2%), or 1/26 (3.8%) among records with any additional outcome. The sole joint record is `10.1145/3772318.3791233` (the advice paper below). Co-coding does not establish that a study tested a relationship between objective system success and recipient outcomes.

**Less coverage of user task performance:** `User performance` is marked in 4/31 records, compared with opinion in 11, action in eight, and system performance in 12. It is 4/15 (26.7%) among records with any user outcome. The four DOI suffixes are `3717511.3747073`, `3742413.3789120`, `3772318.3790934`, and `3772318.3791365`, all under `10.1145/`. `User opinion` is broad: it can include issue attitudes, trust, and reactions. It is not synonymous with perceptions alone. Neither opinions nor intentions substitute for observed task performance.

**Uneven outcome coverage across behavior labels:** retain this as a descriptive coverage finding, not a general consequence pattern.

| Behavior label | Records | None | Opinion | Action | System performance | User performance | Any user outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Hallucination Agreement | 4 | 0 | 0 | 0 | 4 | 0 | 0 |
| Bias Agreement | 13 | 3 | 6 | 2 | 4 | 2 | 7 |
| Obsequiousness | 7 | 3 | 3 | 3 | 0 | 1 | 4 |
| Stance Change | 8 | 0 | 3 | 2 | 5 | 0 | 3 |
| Failure to challenge/trying to get along | 17 | 3 | 4 | 5 | 6 | 3 | 8 |

These rows overlap. All four hallucination-agreement records have system performance marked; none has a user outcome marked. None of the seven obsequiousness records has system performance marked. Neither observation proves that the behavior has no unmeasured consequence. Hallucination agreement is not all hallucination. A zero cell does not establish a field-wide research gap, lack of user awareness, or a null effect.

Evaluator marginal counts are specialist 5, authors 8, and prompted AI 8, with a union of 19. They describe the retained schema only. Behavior marginal percentages are respectively 12.9%, 41.9%, 22.6%, 25.8%, and 54.8%; these are literature coverage, not rates of behavior in models.

Excluding the two explicitly identified reviews leaves N = 29: system performance 11/29 (37.9%), opinion 11/29 (37.9%), action 8/29 (27.6%), and task performance 4/29 (13.8%). The descriptive ordering persists. No significance tests or averages of incompatible effects are added.

## Focused full-text checks and proposed coding reviews

Only three included primary papers received the focused result audit below. Public author versions were used after publisher PDF requests returned access errors. The artifact does not claim a full-text audit of all 31 records. Exact measures, PDF pages, versions, and proposed reviews are preserved in [study_audit.json](../paper/evidence/study_audit.json); retrieval provenance is separate. None of these extractions silently changes the original labels.

### Invisible Saboteurs

DOI `10.1145/3772318.3791365`; [arXiv:2510.03667v2](https://arxiv.org/abs/2510.03667v2).

The study compares high- and low-sycophancy chatbots within 24 novice participants on ML debugging tasks. PDF p.9 reports normalized held-out F1 gains of 49.29% in the low condition and 4.78% in the high condition, with a paired comparison p = .003. These are normalized gains, not raw accuracy percentages, and do not show that the high condition's true benefit is exactly zero.

The original outcome coding marks only `User performance`. Observed workflow/reliance measures (pp.6, 10-12) and perception ratings (pp.6, 12-13) warrant reviewing `User action` and `User opinion`. Computational accuracy and MMLU evaluation (p.5) warrant reviewing `System performance`, after deciding consistently whether baseline/control validation counts as an outcome. If that system code alone were accepted, joint system/user coverage would be two rather than one; this is a conditional illustration, not a corrected estimate.

### When AI Gives Advice

DOI `10.1145/3772318.3791233`; [arXiv:2512.08937v2](https://arxiv.org/abs/2512.08937v2).

The two main studies involve 161 + 49 = 210 raters in advice-giving occupations. Measures include perceived effectiveness, clarity, warmth/support, contextual fit, advice-seeking intentions, and expected long-term benefit rankings (PDF pp.6-9). The LLM responses are generally preferred to human baselines on perceived quality. Whole-source comparisons do not isolate a causal effect of sycophancy.

Retain the original `User opinion` and `System performance` labels pending author review, but interpret them as third-party ratings of advice quality. They do not demonstrate actual recipient task success or longitudinal well-being improvement. This is why the unique joint-coverage cell cannot stand for an established system-to-user benefit link.

### Be Friendly, Not Friends

DOI `10.1145/3772318.3791079`; [arXiv:2502.10844v3](https://arxiv.org/abs/2502.10844v3).

The 2 x 2 experiment analyzes 224 U.S. adults discussing autonomous vehicles, crossing adaptive/consistent stance with complimentary/neutral demeanor. Measures include trust, use/recommendation intentions, and issue attitudes (PDF p.6). Perceived authenticity has a stance-by-demeanor interaction (p.8, section 4.5; p = .033): the adaptive-versus-consistent contrast changes direction across demeanor conditions.

The original map already marks `Obsequiousness` and `Stance Change`, with `User opinion`. No additional behavior code is proposed. Intentions are not observed actions, and authenticity is not objective correctness. A mediation statement in section 4.2 conflicts with a reported confidence interval crossing zero; the manuscript does not adopt that strong statement.

## Closest work and contribution boundary

[What Counts as AI Sycophancy? A Taxonomy and Expert Survey of a Fragmented Construct](https://arxiv.org/abs/2605.21778v1) reviews 70 papers and surveys 106 experts; its discussion and appendix already address definitions, measurement, and downstream effects. It is external related work, outside N = 31. The present manuscript therefore claims neither a first taxonomy nor the first connection between sycophancy and consequences.

The narrower contribution is a reproducible outcome co-coverage analysis of an existing human-coded map, accompanied by an audit of what evaluators rate, what constitutes a system measure, and what directly observes a user consequence. Seaborn and Yalcin's included scoping review is identified as a review and background source; unavailable full text is not used to invent specific synthesis results.

All 31 DOI records match the cached Crossref JSON and BibTeX. Of the CSV titles, 23 match after normalization and eight are prefixes of the complete titles. Full metadata is used in the bibliography. Converting Unicode names to TeX accents preserves author metadata while avoiding classic BibTeX abbreviation issues. The manuscript database contains 32 entries (31 corpus records and one external taxonomy), of which six are cited. See [corpus_manifest.csv](../paper/generated/corpus_manifest.csv).

## Figures, manuscript, and validation

The manuscript contains one marginal/co-coverage table and a behavior-by-outcome heatmap (Figure 1, p.3). Two evaluator panels are companion assets under `paper/figures/`. The original [main_heatmaps.pdf](../output/final_map/main_heatmaps.pdf) remains available as the all-panel review output. Its Type 3 fonts are replaced in the manuscript assets by re-typesetting the same 55 counts and purple count/N scale with 10-point embedded Type 1 text. Row totals are added; the display label `User task performance` clarifies the original `User performance` field. No label assignments change. See [figure provenance](../paper/figures/provenance.json).

The recorded build uses PDFLaTeX, BibTeX, and two further PDFLaTeX passes. The manuscript is four US Letter pages total, including references starting on p.4, with no appendix. All six cited references resolve. The recorded verification finds no overfull boxes or undefined references, and matches all 55 original cells and all 55 counts extracted from the new vector PDFs. Page images were visually checked for legibility, overlap, and clipping. Current checks are in [validation.json](../paper/qa/validation.json); run `python paper/build.py --verify` to refresh them.

The **14 October 2026 requirements snapshot** recorded a four-page body limit for extended abstracts, excluding references and appendices, and the AAAI-27 format. It recorded a regular deadline of 20 November 2026 AoE and a separate 3 December fast track, on a provisional [workshop page](https://intelligence-symbiosis.net/en/events/aaai-2027-workshop). These are dated audit observations, not a promise of current submission policy. The workshop page did not separately specify anonymity; the draft conservatively uses the linked AAAI submission mode. Official `.sty` and `.bst` files are unmodified. No authors, affiliations, or search-history details are fabricated.

## Remaining author decisions

1. Recover the actual search strings, execution dates, databases, and screening stages, if possible; otherwise retain the explicit limitations.
2. Explain the three deletions and the included DOI whose current A/B screening decisions both say Exclude.
3. Explain the two omitted evaluator columns and decide consistent rules for computational validation and subjective advice quality as system outcomes.
4. Review the suggested additional labels for Invisible Saboteurs, with a recorded decision before changing inputs and regenerating results.
5. Confirm initial coding independence and discrepancy-resolution history; edited workbook agreement cannot substitute for those records.
6. Confirm authorship and the workshop's final submission/anonymity requirements before any submission.

The repository and source bundle are local research artifacts. No submission, message to external parties, or publication of the project is part of this workflow.
