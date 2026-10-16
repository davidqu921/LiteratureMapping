"""Reproduce publication-level coded coverage, without recoding blank cells.

Run python analyze.py from any directory. Python standard library only.
The frozen CSV has three header rows: groups, attributes, definitions.
X is positive; an empty cell is unmarked, not a negative or an N/A.
Unexpected cell values and duplicate DOI identifiers fail explicitly.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "final_map.csv"
REVIEWS = {"10.1145/3703155", "10.1145/3776734.3794532"}


def calculate(rows, labels):
    n = len(rows)
    sets = {labels[i]: {r[2].lower() for r in rows if r[i].strip().upper() == "X"}
            for i in range(4, 17)}
    system = sets[labels[15]]
    user = set.union(*(sets[labels[i]] for i in (13, 14, 16)))
    counts = {k: {"n": len(v), "percent": round(100 * len(v) / n, 1),
                  "dois": sorted(v)} for k, v in sets.items()}
    pairs = {f"{labels[i]} | {labels[j]}": len(sets[labels[i]] & sets[labels[j]])
             for left, right in [(range(4, 7), range(7, 12)),
                                 (range(4, 7), range(12, 17)),
                                 (range(7, 12), range(12, 17))]
             for i in left for j in right}
    return {"N": n, "counts": counts, "pair_counts": pairs,
            "any_user": {"n": len(user), "percent": round(100 * len(user) / n, 1),
                         "dois": sorted(user)},
            "system_intersections": {labels[i]: sorted(system & sets[labels[i]])
                                     for i in (13, 14, 16)},
            "system_any_user": sorted(system & user),
            "partition": {"system_only": len(system - user),
                          "user_only": len(user - system), "both": len(system & user),
                          "neither_marked": n - len(system | user)},
            "evaluator_unmarked": n - len(set.union(*(sets[labels[i]] for i in (4, 5, 6))))}


def main():
    rows = list(csv.reader(SOURCE.open(encoding="utf-8-sig", newline="")))
    labels = [s.strip() for s in rows[1]]
    data = [r for r in rows[3:] if any(s.strip() for s in r)]
    if any(len(r) != 17 for r in rows):
        raise ValueError("Expected 17 columns, including empty metadata separator.")
    identifiers = [r[2].strip().lower() for r in data]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate DOI: inspect versions before analysis.")
    for r in data:
        for i in range(4, 17):
            if r[i].strip().upper() not in {"", "X"}:
                raise ValueError(f"Unrecognized label {r[2]} {labels[i]}: {r[i]!r}")
        if r[12].strip() and any(r[i].strip() for i in (13, 14, 15, 16)):
            raise ValueError(f"None co-occurs with another outcome: {r[2]}")
    full = calculate(data, labels)
    sensitivity = calculate([r for r in data if r[2].lower() not in REVIEWS], labels)
    out = ROOT / "generated"
    out.mkdir(exist_ok=True)
    result = {"input_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "unit": "publication record, not independent study",
              "cell_policy": "X=marked; blank=unmarked, not verified absence; no explicit N/A present",
              "main": full, "excluding_two_identified_reviews": sensitivity}
    (out / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    with (out / "codebook.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["zero_based_column", "group", "attribute", "supplied_definition"])
        for i in range(4, 17):
            w.writerow([i, "evaluator (inferred group heading)" if i < 7 else "behavior" if i < 12 else "outcome", labels[i], rows[2][i]])
    with (out / "coded_records.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["doi", "title_as_supplied"]+labels[4:])
        for r in data: w.writerow([r[2], r[1]]+["marked" if s.strip() else "unmarked" for s in r[4:]])
    # Readable tables use ordinary template font size, spacing, and margins.
    outcome_rows = []
    display = {12: "No impact (None)", 13: "User opinion", 14: "User action",
               15: "System performance", 16: "User task performance"}
    for i in (15, 13, 14, 16, 12):
        c = full["counts"][labels[i]]
        overlap = "---" if i in (12, 15) else str(len(full["system_intersections"][labels[i]]))
        outcome_rows.append(f"{display[i]} & {c['n']} & {c['percent']:.1f} & {overlap} " + r"\\")
    outcome_rows.append(f"Any user outcome & {full['any_user']['n']} & {full['any_user']['percent']:.1f} & {len(full['system_any_user'])} " + r"\\")
    t1 = r"""\begin{table}[t]
\centering
\begin{tabular}{lrrr}
\toprule
Marked outcome & $n$ & \% & $\cap S$ \\
\midrule
""" + "\n".join(outcome_rows) + r"""
\bottomrule
\end{tabular}
\caption{Outcome labels in the supplied map ($N=31$ publications). $\cap S$: also marked system performance. Any user outcome is the union of opinion, action, and task performance. Labels overlap; unmarked does not mean absent.}
\label{tab:outcomes}
\end{table}"""
    t2 = r"""\begin{figure*}[t]
\centering
\includegraphics[width=\linewidth]{figures/behavior_outcomes.pdf}
\caption{Literature heatmap connecting sycophantic behaviors to outcome categories ($N=31$ publications). Cells count co-marked records; purple intensity represents count/$N$. Row $n$ gives each behavior's coverage. User task performance is the codebook's User performance; None denotes no coded impact measure. Categories overlap. A zero means no co-marked record, not evidence of no effect.}
\label{fig:matrix}
\end{figure*}"""
    for name, table in (("outcomes", t1), ("matrix", t2)):
        (out / (name+".tex")).write_text(table+"\n", encoding="utf-8")
    # One main .tex file contains the generated table and vector-figure inclusion.
    mainfile = ROOT / "main.tex"
    if mainfile.exists():
        text = mainfile.read_text(encoding="utf-8")
        for name, table in (("OUTCOMES", t1), ("MATRIX", t2)):
            pattern = rf"(?s)% BEGIN GENERATED {name}.*?% END GENERATED {name}"
            replacement = f"% BEGIN GENERATED {name}\n{table}\n% END GENERATED {name}"
            text, n = re.subn(pattern, lambda _: replacement, text)
            if n != 1: raise ValueError(f"Expected exactly one {name} table marker")
        mainfile.write_text(text, encoding="utf-8")
    print(json.dumps({"N": full['N'], "counts": {k:v['n'] for k,v in full['counts'].items()},
                      "system_any_user": full['system_any_user'],
                      "excluding_reviews_N": sensitivity['N']}, indent=2))


if __name__ == "__main__":
    main()
