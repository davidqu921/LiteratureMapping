"""Fetch publicly accessible sources used in the manuscript audit; never bypass access controls."""
import hashlib
import argparse
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "author_kit_official.zip": "https://aaai.org/authorkit27/",
    "workshop.html": "https://intelligence-symbiosis.net/en/events/aaai-2027-workshop",
    "aaai_instructions.html": "https://aaai.org/conference/aaai/aaai-27/submission-instructions/",
    "taxonomy.pdf": "https://arxiv.org/pdf/2605.21778v1",
    "friendly.pdf": "https://arxiv.org/pdf/2502.10844v2",
    "advice.pdf": "https://arxiv.org/pdf/2512.08937v1",
    "saboteurs.pdf": "https://arxiv.org/pdf/2510.03667",
    "decisions_publisher.pdf": "https://dl.acm.org/doi/pdf/10.1145/3772318.3790934",
    "validation_publisher.pdf": "https://dl.acm.org/doi/pdf/10.1145/3772318.3791851",
    "polarization_publisher.pdf": "https://dl.acm.org/doi/pdf/10.1145/3772363.3798705",
    "friendly_publisher.pdf": "https://dl.acm.org/doi/pdf/10.1145/3772318.3791079",
    "advice_publisher.pdf": "https://dl.acm.org/doi/pdf/10.1145/3772318.3791233",
    "friendly_v3.pdf": "https://arxiv.org/pdf/2502.10844v3",
    "advice_v2.pdf": "https://arxiv.org/pdf/2512.08937v2",
    "hallucination_survey.pdf": "https://arxiv.org/pdf/2311.05232",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", choices=list(SOURCES))
    args = parser.parse_args()
    out = ROOT / "evidence" / "sources"
    out.mkdir(parents=True, exist_ok=True)
    log = ROOT / "evidence" / "retrieval_log.json"
    records = json.loads(log.read_text()) if log.exists() else []
    for name, url in SOURCES.items():
        if args.names and name not in args.names:
            continue
        records = [r for r in records if r['name'] != name]
        path = out / name
        provenance = out / (name + ".json")
        if path.exists() and provenance.exists():
            records.append(json.loads(provenance.read_text(encoding="utf-8")))
            print("CACHED", name, flush=True)
            continue
        row = {"name": name, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LiteratureMapping/1.0 research source verification"})
            with urllib.request.urlopen(req, timeout=35) as response:
                data = response.read(35_000_001)
                if len(data) > 35_000_000:
                    raise ValueError("Source exceeds size limit")
                if name.endswith(".pdf") and not data.startswith(b"%PDF"):
                    raise ValueError("Not a PDF response")
                row.update({"final_url": response.url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "status": "downloaded"})
                path.write_bytes(data)
                provenance.write_text(json.dumps(row, indent=2), encoding="utf-8")
                print("OK", name, len(data), flush=True)
        except Exception as exc:
            row.update({"status": "unavailable", "error": str(exc)})
            print("UNAVAILABLE", name, str(exc), flush=True)
        records.append(row)
        time.sleep(1)
    (ROOT / "evidence" / "retrieval_log.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
