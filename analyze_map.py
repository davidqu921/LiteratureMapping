"""Compute auditable, publication-level evidence for heat-map findings."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from csv_to_latex import ROOT, read_map


def analyze(source, config, out):
    names, groups, papers, members, warnings = read_map(source, config)
    out.mkdir(parents=True, exist_ok=True)
    by_name = {(g["title"], names[c]): members[c] for g in groups for c in g["columns"]}
    outcomes = {name: keys for (group, name), keys in by_name.items() if group == "Outcomes"}
    human = set().union(*(outcomes[n] for n in ["User opinion", "User action", "User performance"]))
    system = outcomes["System performance"]
    universe = {p["key"] for p in papers}
    order = {p["key"]: i for i, p in enumerate(papers)}
    def describe(keys, denominator=None):
        base = len(papers) if denominator is None else denominator
        return {"n": len(keys), "denominator": base, "percent": round(100 * len(keys) / base, 1) if base else None,
                "dois": sorted(keys, key=order.__getitem__)}
    categories = {g["title"]: {names[c]: describe(members[c]) for c in g["columns"]} for g in groups}
    evidence = {
        "source": str(source.resolve()), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "unit": "publication (CSV row), not participant, experiment, or independent empirical study",
        "paper_count": len(papers), "categories": categories,
        "outcome_partition": {"human_only": describe(human - system), "system_only": describe(system - human),
                              "both_human_and_system": describe(human & system),
                              "neither_human_nor_system": describe(universe - human - system)},
        "human_outcome_union": describe(human),
        "none_and_other_conflicts": describe(outcomes["None"] & (human | system)),
        "definition_outcomes": {}, "evaluation_unmarked": describe(set(groups[0]["unmarked_papers"])),
        "warnings": warnings,
    }
    for label, count in categories["Definition of sycophancy"].items():
        keys = set(count["dois"])
        evidence["definition_outcomes"][label] = {
            "system": describe(keys & system, len(keys)), "human_union": describe(keys & human, len(keys))}
    (out / "findings_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "findings_counts.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["group", "attribute", "papers", "denominator", "percent"])
        for group, attributes in categories.items():
            for name, result in attributes.items():
                writer.writerow([group, name, result["n"], result["denominator"], result["percent"]])
        for name, result in evidence["outcome_partition"].items():
            writer.writerow(["Mutually exclusive outcome partition", name, result["n"], result["denominator"], result["percent"]])
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/final_map.json")
    parser.add_argument("--out", type=Path, default=ROOT / "output/final_map")
    args = parser.parse_args()
    result = analyze(args.csv, json.loads(args.config.read_text(encoding="utf-8-sig")), args.out)
    print(json.dumps({k: {n: v for n, v in data.items() if n != "dois"} for k, data in result["outcome_partition"].items()}, indent=2))
