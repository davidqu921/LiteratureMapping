import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.fetch_bibtex import Client, CrossrefRedirects, bib_fields, validate, prepare_for_latex


class BibtexTests(unittest.TestCase):
    def setUp(self):
        self.paper = {"key": "10.1234/test", "title": "Short title"}
        self.metadata = {"DOI": "10.1234/test", "title": ["Short title: Full subtitle"], "author": [{}]}
        self.bib = '@article{old, title={{Short title}: Full subtitle}, author={Smith, A}, year=2026, journal={Example}, DOI={10.1234/test}}'

    def test_nested_fields_and_exact_key_replacement(self):
        rewritten, record = validate(self.paper, self.metadata, self.bib)
        self.assertEqual(rewritten, self.bib.replace("{old,", "{10.1234/test,", 1))
        self.assertEqual(record["title_status"], "csv_title_is_prefix")
        self.assertEqual(record["missing_fields"], [])
        self.assertEqual(bib_fields(rewritten)[1]["title"], "{Short title}: Full subtitle")
        separate_subtitle = {**self.metadata, "title": ["Short title"], "subtitle": ["Full subtitle"]}
        self.assertEqual(validate(self.paper, separate_subtitle, self.bib)[1]["crossref_title"],
                         "Short title: Full subtitle")

    def test_doi_mismatch_and_executable_tex_rejected(self):
        for invalid in [self.bib.replace("DOI={10.1234/test}", "DOI={10.1234/other}"),
                        self.bib.replace("Full subtitle", r"\input{private}"), self.bib + self.bib]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate(self.paper, self.metadata, invalid)

    def test_partial_entry_rejected_and_title_difference_flagged(self):
        with self.assertRaises(ValueError):
            bib_fields(self.bib[:-2])
        record = validate({**self.paper, "title": "Different paper"}, self.metadata, self.bib)[1]
        self.assertEqual(record["title_status"], "review_title_difference")

    def test_latex_months_and_capitalization_without_metadata_changes(self):
        original = self.bib[:-1] + ", month=Sept}"
        result = prepare_for_latex(original)
        before = bib_fields(original)[1]
        after = bib_fields(result)[1]
        self.assertEqual(after.pop("month"), "September")
        before.pop("month")
        self.assertEqual(after.pop("title"), "{" + before.pop("title") + "}")
        self.assertEqual(after, before)

    def test_cache_makes_no_request(self):
        import hashlib
        with tempfile.TemporaryDirectory() as folder:
            client = Client(Path(folder))
            name = hashlib.sha256(self.paper["key"].encode()).hexdigest()[:20] + ".bib"
            (Path(folder) / name).write_text(self.bib, encoding="utf-8")
            client.opener = Mock()
            self.assertEqual(client.get(self.paper["key"], bibtex=True)[0], self.bib)
            client.opener.open.assert_not_called()

    def test_cross_host_or_plain_http_redirect_rejected(self):
        for url in ["http://api.crossref.org/works/test", "https://example.com/"]:
            with self.assertRaises(ValueError):
                CrossrefRedirects().redirect_request(None, None, 302, "", {}, url)


if __name__ == "__main__":
    unittest.main()
