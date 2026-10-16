import json
import tempfile
import unittest
from pathlib import Path

from scripts.analyze_map import analyze
from scripts.csv_to_latex import ROOT


class FindingsTests(unittest.TestCase):
    def test_publication_partition_and_small_category_claims(self):
        with tempfile.TemporaryDirectory() as folder:
            result = analyze(ROOT / "data/lit-map 2026s sycophancy - FINAL MAP.csv",
                             json.loads((ROOT / "configs/final_map.json").read_text()), Path(folder))
        partition = result["outcome_partition"]
        self.assertEqual([x["n"] for x in partition.values()], [14, 11, 1, 5])
        seen = set()
        for value in partition.values():
            self.assertFalse(seen.intersection(value["dois"]))
            seen.update(value["dois"])
        self.assertEqual(len(seen), 31)
        self.assertEqual(partition["both_human_and_system"]["dois"], ["10.1145/3772318.3791233"])
        self.assertEqual(result["none_and_other_conflicts"]["n"], 0)
        self.assertEqual(result["human_outcome_union"]["n"], 15)
        self.assertEqual(result["categories"]["Outcomes"]["User performance"]["n"], 4)
        definitions = result["definition_outcomes"]
        self.assertEqual(definitions["Hallucination Agreement"]["system"]["n"], 4)
        self.assertEqual(definitions["Hallucination Agreement"]["human_union"]["n"], 0)
        self.assertEqual(definitions["Obsequiousness"]["system"]["n"], 0)


if __name__ == "__main__":
    unittest.main()
