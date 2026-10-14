"""Download DOI metadata and real BibTeX from Crossref's free, public API.

HTTPS GET only; no credentials, email, paid services or third-party redirects.
One request at a time, at least one second apart; responses cached verbatim.
"""
import argparse
import csv
import hashlib
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from csv_to_latex import ROOT, read_map


class CrossrefRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.netloc != "api.crossref.org":
            raise ValueError(f"Refusing redirect outside Crossref HTTPS: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self, cache):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.opener = urllib.request.build_opener(CrossrefRedirects())
        self.next_request = 0

    def get(self, doi, bibtex=False):
        suffix = ".bib" if bibtex else ".json"
        path = self.cache / (hashlib.sha256(doi.lower().encode()).hexdigest()[:20] + suffix)
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        if bibtex:
            url += "/transform/application/x-bibtex"
        if path.exists():
            return path.read_text(encoding="utf-8"), url, path
        for attempt in range(3):
            time.sleep(max(0, self.next_request - time.monotonic()))
            request = urllib.request.Request(url, headers={
                "User-Agent": "LiteratureMapping/1.0 (DOI bibliography retrieval)",
                "Accept": "application/x-bibtex" if bibtex else "application/json",
            })
            try:
                with self.opener.open(request, timeout=30) as response:
                    body = response.read(2_000_001)
                    if len(body) > 2_000_000:
                        raise ValueError("Unexpectedly large metadata response")
                    text = body.decode("utf-8")
                    if not text.strip() or text.lstrip().startswith("<"):
                        raise ValueError("Empty or HTML response instead of metadata")
                    # Honor advertised rate windows, with a conservative one-second floor.
                    limit = float(response.headers.get("x-rate-limit-limit", "1"))
                    interval = float(response.headers.get("x-rate-limit-interval", "1s").rstrip("s"))
                    self.next_request = time.monotonic() + max(1, interval / max(limit, 1))
                    path.write_bytes(body)
                    (path.with_suffix(suffix + ".provenance.json")).write_text(json.dumps({
                        "doi": doi, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "api_pool": response.headers.get("x-api-pool", "public (no credentials)"),
                    }, indent=2), encoding="utf-8")
                    return text, url, path
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                retry = exc.headers.get("Retry-After", "")
                delay = max(2 ** (attempt + 1), float(retry) if retry.isdigit() else 5)
                if delay > 60:
                    raise ValueError(f"Crossref requested a {delay}s pause; rerun later using cache") from exc
                self.next_request = time.monotonic() + delay
            except urllib.error.URLError:
                if attempt == 2:
                    raise
                self.next_request = time.monotonic() + 2 ** (attempt + 1)
        raise ValueError("Download failed")


def bib_fields(text):
    """Parse a single service-returned entry, respecting nested braces/quotes."""
    entry = re.match(r"\s*@(\w+)\s*\{\s*([^,\s]+)\s*,", text)
    if not entry or entry[1].lower() in {"preamble", "string", "comment"}:
        raise ValueError("Expected one BibTeX bibliographic entry")
    fields, pos = {}, entry.end()
    while True:
        while pos < len(text) and (text[pos].isspace() or text[pos] == ","):
            pos += 1
        if pos >= len(text):
            raise ValueError("Unclosed BibTeX entry")
        if text[pos] == "}":
            if text[pos + 1:].strip():
                raise ValueError("Unexpected content after BibTeX entry")
            return entry, fields
        match = re.match(r"([\w-]+)\s*=\s*", text[pos:])
        if not match:
            raise ValueError("Malformed BibTeX field")
        name = match[1].lower()
        pos += match.end()
        if pos >= len(text):
            raise ValueError("Missing BibTeX field value")
        start = pos
        if text[pos] in '{"':
            opening = text[pos]
            depth = 1
            pos += 1
            while pos < len(text) and depth:
                if text[pos] == "\\":
                    pos += 2
                    continue
                if opening == "{" and text[pos] == "{":
                    depth += 1
                if (opening == "{" and text[pos] == "}") or (opening == '"' and text[pos] == '"'):
                    depth -= 1
                pos += 1
            if depth:
                raise ValueError("Unclosed BibTeX field value")
            value = text[start + 1:pos - 1]
        else:
            while pos < len(text) and text[pos] not in ",}":
                pos += 1
            value = text[start:pos].strip()
        if name in fields:
            raise ValueError(f"Duplicate BibTeX field: {name}")
        fields[name] = value


def normal_title(title):
    title = html.unescape(re.sub(r"<[^>]+>", "", title))
    return "".join(c for c in unicodedata.normalize("NFKC", title).casefold() if c.isalnum())


def prepare_for_latex(bib):
    """Keep downloaded metadata, protect title case and expand month macros."""
    entry, fields = bib_fields(bib)
    months = {"jan": "January", "feb": "February", "mar": "March", "apr": "April",
              "may": "May", "jun": "June", "june": "June", "jul": "July", "july": "July",
              "aug": "August", "sep": "September", "sept": "September", "oct": "October",
              "nov": "November", "dec": "December"}
    lines = ["@" + entry[1] + "{" + entry[2] + ","]
    for name, value in fields.items():
        if name == "title":
            value = "{" + value + "}"  # prevent bibliography styles from lowercasing LLM/AI
        elif name == "month":
            value = months.get(value.casefold(), value)
        lines.append("  " + name + " = {" + value + "},")
    return "\n".join(lines + ["}"])


def validate(paper, metadata, bib):
    doi = paper["key"]
    if metadata.get("DOI", "").casefold() != doi.casefold():
        raise ValueError("JSON DOI does not match requested DOI")
    entry, fields = bib_fields(bib)
    if fields.get("doi", "").casefold() != doi.casefold():
        raise ValueError("BibTeX DOI does not match requested DOI")
    if re.search(r"\\(?:input|include|write|openout|read|catcode|csname|usepackage|immediate|special)\b", bib, re.I):
        raise ValueError("Unexpected executable TeX command in returned metadata")
    if "\ufffd" in bib:
        raise ValueError("Replacement character in BibTeX encoding")
    title = " ".join(metadata.get("title", []))
    subtitle = " ".join(metadata.get("subtitle", []))
    if subtitle and not normal_title(title).endswith(normal_title(subtitle)):
        title += ": " + subtitle
    original, retrieved = normal_title(paper["title"]), normal_title(title)
    title_status = ("same_normalized" if original == retrieved else
                    "csv_title_is_prefix" if original and retrieved.startswith(original) else "review_title_difference")
    missing = [field for field in ("title", "author", "year") if not fields.get(field)]
    if not (fields.get("journal") or fields.get("booktitle")):
        missing.append("journal_or_booktitle")
    record = {"doi": doi, "csv_title": paper["title"], "crossref_title": title,
              "title_status": title_status, "entry_type": entry[1], "year": fields.get("year", ""),
              "author_count": len(metadata.get("author", [])),
              "venue": fields.get("booktitle", fields.get("journal", "")),
              "missing_fields": missing, "doi_verified": True}
    # Preserve the service's entry and fields; change only the citation key.
    renamed = bib[:entry.start(2)] + doi + bib[entry.end(2):]
    return renamed.strip(), record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/final_map.json")
    parser.add_argument("--out", type=Path, default=ROOT / "output/final_map")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    _, _, papers, _, _ = read_map(args.csv, config)
    args.out.mkdir(parents=True, exist_ok=True)
    client = Client(args.out / "crossref_cache")
    records, entries, failures = [], [], []
    for i, paper in enumerate(papers, 1):
        doi = paper["key"]
        try:
            if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
                raise ValueError("Key is not a DOI")
            raw_json, json_url, json_path = client.get(doi)
            metadata = json.loads(raw_json)["message"]
            raw_bib, bib_url, bib_path = client.get(doi, bibtex=True)
            entry, record = validate(paper, metadata, raw_bib)
            record.update({"metadata_url": json_url, "bibtex_url": bib_url,
                           "raw_json": str(json_path), "raw_bibtex": str(bib_path)})
            records.append(record)
            entries.append(entry)
            print(f"[{i}/{len(papers)}] OK {doi}: {record['title_status']}", flush=True)
        except (OSError, ValueError, KeyError) as exc:
            failures.append({"doi": doi, "error": str(exc)})
            print(f"[{i}/{len(papers)}] FAILED {doi}: {exc}", flush=True)
    report = {"source": str(args.csv.resolve()), "api": "Crossref free public API; no credentials",
              "assembled_utc": datetime.now(timezone.utc).isoformat(),
              "expected": len(papers), "downloaded_and_doi_verified": len(records),
              "records": records, "failures": failures,
              "note": "DOI and fields checked; classification and original papers not independently reviewed."}
    (args.out / "crossref_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.out / "crossref_audit.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["doi", "csv_title", "crossref_title", "title_status", "entry_type", "year", "author_count", "venue", "missing_fields"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    if failures:
        raise SystemExit("Incomplete download: report saved; bibliography not replaced. Rerun uses cache.")
    (args.out / "references_crossref.bib").write_text(
        "% Downloaded from Crossref public API. Original responses in crossref_cache.\n"
        "% Only citation keys changed to match the input CSV DOI keys.\n\n" + "\n\n".join(entries) + "\n", encoding="utf-8")
    (args.out / "references_crossref_latex.bib").write_text(
        "% Real Crossref metadata, with DOI citation keys.\n"
        "% Formatting only: brace-delimited fields, protected title case, expanded month names.\n"
        "% Raw API BibTeX and JSON are preserved in crossref_cache.\n\n" +
        "\n\n".join(prepare_for_latex(entry) for entry in entries) + "\n", encoding="utf-8")
    print(f"Saved {len(entries)} real entries to {args.out / 'references_crossref.bib'}", flush=True)


if __name__ == "__main__":
    main()
