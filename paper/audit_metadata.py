"""Audit the 31 DOI records against the project's real cached Crossref responses.

This is offline and free. It does not query Scholar, scrape publishers, or
replace manual codes. Writes a citation/version manifest and provenance report.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
AUDITED={
    '10.1145/3772318.3791365':('saboteurs.pdf','https://arxiv.org/abs/2510.03667v2','primary empirical'),
    '10.1145/3772318.3791079':('friendly_v3.pdf','https://arxiv.org/abs/2502.10844v3','primary empirical'),
    '10.1145/3772318.3791233':('advice_v2.pdf','https://arxiv.org/abs/2512.08937v2','primary empirical'),
    '10.1145/3703155':('hallucination_survey.pdf','https://arxiv.org/abs/2311.05232','review'),
    '10.1145/3776734.3794532':('','','review (title and publisher metadata; full text unavailable)'),
}


def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())


def main():
    cache=ROOT.parent/'output/final_map/crossref_cache'
    metadata={}
    for path in cache.glob('*.json'):
        if '.provenance.' in path.name:continue
        raw=json.loads(path.read_text(encoding='utf-8')); item=raw.get('message',raw)
        metadata[item['DOI'].lower()]=(path,item)
    rows=list(csv.reader((ROOT/'data/final_map.csv').open(encoding='utf-8-sig')))[3:]
    manifest=[]
    for row in rows:
        path,item=metadata[row[2].lower()]
        title=item['title'][0]
        relationship='exact normalized match' if norm(title)==norm(row[1]) else 'supplied title is truncated prefix' if norm(title).startswith(norm(row[1])) else 'REVIEW REQUIRED'
        if not item.get('author') or not item.get('published') or not item.get('container-title'):raise ValueError('Incomplete metadata: '+row[2])
        if relationship=='REVIEW REQUIRED':raise ValueError('Title mismatch: '+row[2])
        source,url,kind=AUDITED.get(row[2].lower(),('','','not classified by full-text audit'))
        manifest.append({'doi':row[2],'supplied_title':row[1],'crossref_title':title,
                         'title_relation':relationship,'crossref_year':item['published']['date-parts'][0][0],
                         'publication_type_audit':kind,'full_text_file':source,'author_version_url':url,
                         'raw_crossref_json':str(path.relative_to(ROOT.parent)).replace('\\','/'),
                         'crossref_json_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    out=ROOT/'generated/corpus_manifest.csv'
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
    summary={'records':len(manifest),'unique_normalized_dois':len({r['doi'].lower() for r in manifest}),
             'unique_crossref_titles':len({norm(r['crossref_title']) for r in manifest}),
             'exact_title_matches':sum(r['title_relation']=='exact normalized match' for r in manifest),
             'truncated_prefix_titles':sum(r['title_relation']=='supplied title is truncated prefix' for r in manifest),
             'empirical_full_text_audit_n':3,'caution':'Author versions are linked by title/authors and identifiers; publisher PDFs were unavailable for the three primary studies. Full-text verification was targeted, not corpus-wide.'}
    (ROOT/'generated/metadata_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
