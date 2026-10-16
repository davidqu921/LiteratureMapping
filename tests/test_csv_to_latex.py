"""Regression checks for CSV interpretation and map correctness."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.csv_to_latex import ROOT, generate, read_map, tex


class MapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def fixture(self, rows):
        path = self.folder / "input.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            csv.writer(stream).writerows(rows)
        return path

    def test_final_all_55_cells_against_raw_csv(self):
        source = ROOT / "data" / "lit-map 2026s sycophancy - FINAL MAP.csv"
        config = json.loads((ROOT / "configs" / "final_map.json").read_text())
        report = generate(source, config, self.folder)
        self.assertEqual(report["paper_count"], 31)
        self.assertEqual([len(g["attributes"]) for g in report["groups"]], [3, 5, 5])
        self.assertEqual(len(report["groups"][0]["unmarked_papers"]), 12)
        with source.open(encoding="utf-8-sig", newline="") as stream:
            papers = list(csv.reader(stream))[3:]
        # Explicit source ranges form an independent oracle, not the parser's grouping.
        ranges = [(range(4, 7), range(7, 12)), (range(4, 7), range(12, 17)), (range(7, 12), range(12, 17))]
        checked = 0
        for i, (rows, cols) in enumerate(ranges, 1):
            with (self.folder / f"map_{i:02d}_counts.csv").open(encoding="utf-8-sig", newline="") as stream:
                counts = list(csv.reader(stream))[1:]
            with (self.folder / f"map_{i:02d}_keys.csv").open(encoding="utf-8-sig", newline="") as stream:
                keys = list(csv.reader(stream))[1:]
            for r, source_r in enumerate(rows):
                for c, source_c in enumerate(cols, 1):
                    expected = [p[2] for p in papers if p[source_r].strip() == p[source_c].strip() == "X"]
                    self.assertEqual(int(counts[r][c]), len(expected))
                    self.assertEqual(keys[r][c], "; ".join(expected))
                    checked += 1
        self.assertEqual(checked, 55)
        with ZipFile(self.folder / "overleaf.zip") as bundle:
            self.assertIn("main.tex", bundle.namelist())
            self.assertEqual(len(bundle.namelist()), 9)

    def test_sample_keeps_previously_dropped_attribute(self):
        config = json.loads((ROOT / "configs" / "sample.json").read_text())
        names, groups, papers, members, _ = read_map(ROOT / "examples" / "sample_lit_map.csv", config)
        self.assertEqual(len(papers), 17)
        self.assertEqual([len(g["columns"]) for g in groups], [7, 4, 5])
        self.assertEqual(names[groups[0]["columns"][-1]], "Accessability")
        self.assertGreater(len(members[7]), 0)

    def test_automatic_boundaries_and_duplicate_names_across_groups(self):
        source = self.fixture([
            ["Key", "First", "", "Second", "Third"],
            ["", "Same", "Zero", "Same", "Other"],
            ["p1", " x ", "", "", "X"], ["p2", "", "", "X", "X"],
        ])
        config = {"metadata_header_row": 1, "attribute_header_row": 2,
                  "group_header_row": 1, "data_start_row": 3, "key_column": "Key"}
        _, groups, _, members, _ = read_map(source, config)
        self.assertEqual([g["columns"] for g in groups], [[1, 2], [3], [4]])
        self.assertEqual(members[1] & members[3], set())
        self.assertEqual(members[2], set())
        generate(source, config, self.folder / "out")  # all-zero attribute must not crash

    def test_invalid_data_rejected_before_output(self):
        config = {"groups": [{"title": "A", "attributes": ["a"]}, {"title": "B", "attributes": ["b"]}]}
        cases = [
            ([["key", "a", "b"], ["p1", "?", "X"]], "unknown marker"),
            ([["key", "a", "b"], ["p1", "X", ""], ["p1", "", "X"]], "duplicate citation"),
            ([["key", "a", "b"], ["p1", "X"]], "expected 3 columns"),
            ([["key", "a", "b"], ["", "X", ""]], "missing or unsafe"),
        ]
        for rows, message in cases:
            with self.subTest(message=message):
                source = self.fixture(rows)
                with self.assertRaisesRegex(ValueError, message):
                    generate(source, config, self.folder / "invalid")
                self.assertFalse((self.folder / "invalid").exists())

    def test_user_bibliography_preserved_and_tex_escaped(self):
        config = {"groups": [{"title": "A", "attributes": ["a"]}, {"title": "B", "attributes": ["b"]}]}
        source = self.fixture([["key", "a", "b"], ["p1", "X", "X"]])
        bibliography = self.folder / "references.bib"
        bibliography.write_text("% verified user content", encoding="utf-8")
        generate(source, config, self.folder)
        self.assertEqual(bibliography.read_text(), "% verified user content")
        with ZipFile(self.folder / "overleaf.zip") as bundle:
            self.assertEqual(bundle.read("references.bib"), b"% verified user content")
        self.assertEqual(tex("A&B_50%"), r"A\&B\_50\%")


if __name__ == "__main__":
    unittest.main()
