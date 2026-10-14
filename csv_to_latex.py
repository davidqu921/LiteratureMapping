"""Generate pairwise literature maps from flat or grouped CSVs (stdlib only)."""

import argparse
import csv
import itertools
import json
import re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent


def tex(value):
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(c, c) for c in value)


def read_map(source, config):
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = [[cell.strip() for cell in row] for row in csv.reader(stream)]
    header_row = config.get("attribute_header_row", 1) - 1
    metadata_row = config.get("metadata_header_row", header_row + 1) - 1
    start = config.get("data_start_row", header_row + 2) - 1
    if min(header_row, metadata_row) < 0 or start <= max(header_row, metadata_row) or start >= len(rows):
        raise ValueError("Invalid header/data row numbers, or CSV contains no paper rows.")
    width = len(rows[header_row])
    if any(len(row) != width for row in rows[:start]):
        raise ValueError("Header rows must have the same number of columns.")
    names, meta = rows[header_row], rows[metadata_row]
    key_name = config.get("key_column", "key")
    if meta.count(key_name) != 1:
        raise ValueError(f"Expected exactly one metadata column named {key_name!r}.")
    key_col = meta.index(key_name)
    metadata_names = [key_name, config.get("title_column", "Title"), config.get("url_column", "URL")]
    metadata_cols = {i for i, name in enumerate(meta) if name in metadata_names}
    groups, warnings = [], []
    if "groups" in config:
        used = set()
        for group in config["groups"]:
            columns = []
            for name in group["attributes"]:
                if names.count(name) != 1:
                    raise ValueError(f"Attribute {name!r} must occur exactly once in the header.")
                col = names.index(name)
                if col in used or col in metadata_cols:
                    raise ValueError(f"Attribute {name!r} overlaps another group or metadata.")
                columns.append(col)
                used.add(col)
            groups.append({"title": group["title"], "columns": columns})
    else:
        group_row = config.get("group_header_row", 1) - 1
        if group_row < 0 or group_row >= start:
            raise ValueError("Group header must precede the paper rows.")
        current = None
        for col, name in enumerate(names):
            if col in metadata_cols:
                continue
            heading = rows[group_row][col]
            if heading:
                current = {"title": config.get("group_titles", {}).get(heading, heading), "columns": []}
                groups.append(current)
            if not name:
                continue
            if current is None:
                title = config.get("unnamed_group_title", "Unnamed group")
                warnings.append(f"CSV has no heading for the first group; configured label: {title}.")
                current = {"title": title, "columns": []}
                groups.append(current)
            current["columns"].append(col)
    if len(groups) < 2 or any(not group["columns"] for group in groups):
        raise ValueError("At least two nonempty attribute groups are required.")
    if len({g["title"] for g in groups}) != len(groups):
        raise ValueError("Group titles must be unique.")
    attribute_cols = {c for g in groups for c in g["columns"]}
    missing = {i for i, name in enumerate(names) if name and i not in metadata_cols} - attribute_cols
    if missing:
        raise ValueError(f"Attributes not assigned to a group: {[names[i] for i in sorted(missing)]}")
    for group in groups:
        labels = [names[c] for c in group["columns"]]
        if len(set(labels)) != len(labels):
            raise ValueError(f"Duplicate attribute names in {group['title']}.")
    papers, seen = [], set()
    positives = {str(x).strip().casefold() for x in config.get("positive_values", ["X"])}
    negatives = {str(x).strip().casefold() for x in config.get("negative_values", [""])}
    if positives & negatives:
        raise ValueError("Positive and negative marker values overlap.")
    for line, row in enumerate(rows[start:], start + 1):
        if not any(row):
            continue
        if len(row) != width:
            raise ValueError(f"CSV row {line}: expected {width} columns, got {len(row)}.")
        key = row[key_col]
        if not re.fullmatch(r"[A-Za-z0-9:._/\-]+", key):
            raise ValueError(f"CSV row {line}: missing or unsafe citation key {key!r}.")
        if key in seen:
            raise ValueError(f"CSV row {line}: duplicate citation key {key!r}.")
        seen.add(key)
        marked = set()
        for col in attribute_cols:
            value = row[col].casefold()
            if value in positives:
                marked.add(col)
            elif value not in negatives:
                raise ValueError(f"CSV row {line}, column {col + 1} ({names[col]}): unknown marker {row[col]!r}.")
        ignored = [i + 1 for i, value in enumerate(row) if value and i not in attribute_cols | metadata_cols]
        if ignored:
            raise ValueError(f"CSV row {line}: unexpected content in ignored columns {ignored}.")
        def field(name):
            return row[meta.index(name)] if name in meta else ""
        papers.append({"key": key, "title": field(config.get("title_column", "Title")) or key,
                       "url": field(config.get("url_column", "URL")), "marked": marked})
    if not papers:
        raise ValueError("CSV contains no papers.")
    memberships = {col: {p["key"] for p in papers if col in p["marked"]} for col in attribute_cols}
    for group in groups:
        unmarked = [p["key"] for p in papers if not p["marked"].intersection(group["columns"])]
        if unmarked:
            warnings.append(f"{len(unmarked)} papers have no marked attribute in {group['title']}; blanks remain unmarked.")
        group["unmarked_papers"] = unmarked
    return names, groups, papers, memberships, warnings


def render_table(names, row_group, col_group, memberships, paper_order, heatmap, total):
    columns = col_group["columns"]
    heading = f"{row_group['title']} vs {col_group['title']}"
    caption = (f"{heading}. Counts of papers with both attributes marked (N={total}). "
               "Shade = count / N; papers can occur in multiple cells." if heatmap else
               f"{heading}. Citations for papers with both attributes marked; dash = no marked overlap.")
    result = [r"\begin{table}[!htbp]", r"\centering", r"\small",
              r"\setlength{\tabcolsep}{4pt}", r"\renewcommand{\arraystretch}{1.3}",
              r"\caption{" + tex(caption) + "}",
              r"\begin{tabularx}{\linewidth}{|>{\raggedright\arraybackslash}p{0.23\linewidth}|" +
              ">{\\centering\\arraybackslash}X|" * len(columns) + "}", r"\hline",
              r"\textbf{" + tex(row_group["title"]) + "} & " +
              " & ".join(r"\textbf{\hspace{0pt}" + tex(names[c]) + "}" for c in columns) + r" \\ \hline"]
    for r in row_group["columns"]:
        cells = []
        for c in columns:
            keys = sorted(memberships[r] & memberships[c], key=paper_order.__getitem__)
            if heatmap:
                shade = round(100 * len(keys) / total)
                cells.append(r"\cellcolor{purple!" + str(shade) + "}" + str(len(keys)))
            else:
                cells.append(" ".join(r"\cite{" + key + "}" for key in keys) or "---")
        result.append(tex(names[r]) + " & " + " & ".join(cells) + r" \\ \hline")
    return "\n".join(result + [r"\end{tabularx}", r"\end{table}", ""])


def draft_bib(papers):
    lines = ["% DRAFT: CSV-sourced metadata only, NOT publisher BibTeX.",
             "% Verify full titles, authors, years and venues before submission.",
             "% Put verified entries with the SAME keys into references.bib.", ""]
    for paper in papers:
        lines += ["@misc{" + paper["key"] + ",", "  title = {{" + tex(paper["title"]) + "}},"]
        if paper["url"]:
            lines.append("  howpublished = {\\url{" + tex(paper["url"]) + "}},")
        if paper["key"].startswith("10."):
            lines.append("  doi = {" + paper["key"] + "},")
        lines += ["  note = {Draft metadata from source CSV; authors, year and venue not verified}", "}", ""]
    return "\n".join(lines)


def document(pairs, papers, warnings, heatmaps_only=False):
    geometry = "a4paper,margin=15mm" if heatmaps_only else "a4paper,landscape,margin=15mm"
    title = "Literature map: counts" if heatmaps_only else "Literature map: review draft"
    lines = [r"\documentclass[10pt]{article}", r"\usepackage[T1]{fontenc}",
             r"\usepackage[utf8]{inputenc}", r"\usepackage[" + geometry + r"]{geometry}",
             r"\usepackage[table]{xcolor}", r"\usepackage{tabularx,array}",
             r"\usepackage[numbers]{natbib}", r"\usepackage[hidelinks]{hyperref}",
             r"\setlength{\emergencystretch}{2em}",
             r"\hyphenation{ob-se-qui-ous-ness}", r"\begin{document}",
             r"\section*{" + title + "}",
             f"Source CSV: {len(papers)} papers. Blank cells mean unmarked, not confirmed absence. "
             "Categories are multi-label; cell counts must not be summed as unique papers.",
             r"\par\smallskip " + tex(" ".join(warnings))]
    if not heatmaps_only:
        lines += [r"\par\smallskip\textbf{Bibliography status:} "
                  r"\IfFileExists{references.bib}{Using references.bib; see the accompanying bibliography audit for provenance and checks.}"
                  r"{CSV-only draft entries; full titles, authors, years and venues require verification.}",
                  r"\nocite{" + ",".join(p["key"] for p in papers) + "}"]
    for i, stem in enumerate(pairs):
        if i and not heatmaps_only:
            lines.append(r"\clearpage")
        lines.append(r"\input{" + stem + "_heatmap.tex}")
        if not heatmaps_only:
            lines.append(r"\input{" + stem + "_citations.tex}")
    if not heatmaps_only:
        lines += [r"\clearpage", r"\small", r"\bibliographystyle{unsrt}",
                  r"\IfFileExists{references.bib}{\bibliography{references}}{\bibliography{references_draft}}"]
    return "\n".join(lines + [r"\end{document}", ""])


def generate(source, config, out):
    names, groups, papers, memberships, warnings = read_map(source, config)
    out.mkdir(parents=True, exist_ok=True)
    generated = []
    def write(name, content):
        (out / name).write_text(content, encoding="utf-8")
        generated.append(name)
    order = {paper["key"]: i for i, paper in enumerate(papers)}
    pairs = []
    for i, (rows, cols) in enumerate(itertools.combinations(groups, 2), 1):
        stem = f"map_{i:02d}"
        pairs.append(stem)
        for heatmap, suffix in [(True, "heatmap"), (False, "citations")]:
            write(f"{stem}_{suffix}.tex", render_table(names, rows, cols, memberships, order, heatmap, len(papers)))
        for suffix, counts in [("counts", True), ("keys", False)]:
            name = f"{stem}_{suffix}.csv"
            with (out / name).open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow([rows["title"] + " / " + cols["title"]] + [names[c] for c in cols["columns"]])
                for r in rows["columns"]:
                    cells = [sorted(memberships[r] & memberships[c], key=order.__getitem__) for c in cols["columns"]]
                    writer.writerow([names[r]] + [len(x) if counts else "; ".join(x) for x in cells])
            generated.append(name)
    write("references_draft.bib", draft_bib(papers))
    write("main.tex", document(pairs, papers, warnings))
    write("main_heatmaps.tex", document(pairs, papers, warnings, heatmaps_only=True))
    report = {
        "source": str(source.resolve()), "paper_count": len(papers),
        "groups": [{"title": g["title"], "attributes": [
            {"name": names[c], "csv_column": c + 1, "marked_papers": len(memberships[c])}
            for c in g["columns"]], "unmarked_papers": g["unmarked_papers"]} for g in groups],
        "pairs": [{"file": stem, "rows": a["title"], "columns": b["title"]}
                  for stem, (a, b) in zip(pairs, itertools.combinations(groups, 2))],
        "warnings": warnings, "bibliography": (
            "Using references.bib; see crossref_report.json if supplied for provenance and verification."
            if (out / "references.bib").is_file() else "CSV-only draft; not fetched or externally verified"),
        "heatmap_scale": "100 * overlap_count / paper_count", "config": config,
    }
    write("report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # references.bib is maintained by the researcher and is never overwritten.
    with ZipFile(out / "overleaf.zip", "w", ZIP_DEFLATED) as bundle:
        for name in generated:
            if Path(name).suffix in {".tex", ".bib"}:
                bundle.write(out / name, name)
        if (out / "references.bib").is_file():
            bundle.write(out / "references.bib", "references.bib")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", type=Path, default=ROOT / "sample_lit_map.csv")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "sample.json")
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "sample")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        report = generate(args.csv, config, args.out)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Generated {len(report['pairs'])} map pairs from {report['paper_count']} papers in {args.out.resolve()}")
    for warning in report["warnings"]:
        print(f"Warning: {warning}")


if __name__ == "__main__":
    main()
