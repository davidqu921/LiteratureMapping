"""Check compiled manuscript, bibliography, old heatmaps, and template; render pages.

Requires PyMuPDF. Original repository outputs are checked when available;
the standalone Overleaf source package does not need those derived outputs.
"""
import hashlib
import json
import re
import zipfile
from pathlib import Path
import pymupdf

ROOT=Path(__file__).resolve().parent


def main():
    qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    analysis=json.loads((ROOT/'generated/analysis.json').read_text(encoding='utf-8'))
    source=ROOT/'main.tex'
    text=source.read_text(encoding='utf-8')
    log=(ROOT/'main.log').read_text(encoding='utf-8',errors='replace')
    blg=(ROOT/'main.blg').read_text(encoding='utf-8',errors='replace')
    errors=[]
    if re.search(r'undefined|Overfull|LaTeX Error|Fatal error',log,re.I): errors.append('LaTeX warning/error requiring review')
    if re.search(r'Warning--|error message',blg,re.I): errors.append('BibTeX warning/error')
    forbidden=[r'\small',r'\footnotesize',r'\scriptsize',r'\tiny',r'\resizebox',r'\scalebox',r'\vspace',r'\baselinestretch',r'\textwidth',r'\textheight']
    if any(s in text for s in forbidden):errors.append('Manual font/layout alteration')
    keys=set(k for match in re.findall(r'\\cite\w*(?:\[[^\]]*\])?\{([^}]+)\}',text) for k in match.split(','))
    bibkeys=set(re.findall(r'@\w+\{([^,]+),',(ROOT/'references.bib').read_text()))
    if keys-bibkeys: errors.append('Missing BibTeX keys')
    bbl=(ROOT/'main.bbl').read_text(encoding='utf-8')
    if bbl.count('\\bibitem')!=len(keys):errors.append('Cited references and bibliography differ')
    # Compare the independent recalculation to all cells of the original derived maps.
    comparisons=[]
    labels=list(analysis['main']['counts'])
    for number,left,right in [(1,labels[:3],labels[3:8]),(2,labels[:3],labels[8:]),(3,labels[3:8],labels[8:])]:
        p=ROOT.parent/'output/final_map'/f'map_{number:02d}_heatmap.tex'
        if not p.exists():continue
        old=[int(x) for x in re.findall(r'\\cellcolor\{[^}]*\}(\d+)',p.read_text(encoding='utf-8'))]
        new=[analysis['main']['pair_counts'][f'{a} | {b}'] for a in left for b in right]
        if old!=new:errors.append(f'Original map {number} differs')
        comparisons.append({'map':number,'cells':len(old),'match':old==new})
    # Generated tables must be identical to the ones actually compiled.
    for name in ['outcomes','matrix']:
        table=(ROOT/'generated'/f'{name}.tex').read_text().strip()
        if table not in text:errors.append(f'Stale {name} table')
    figure_provenance=json.loads((ROOT/'figures/provenance.json').read_text())
    if figure_provenance['source_analysis_sha256']!=hashlib.sha256((ROOT/'generated/analysis.json').read_bytes()).hexdigest():
        errors.append('Heatmap analysis fingerprint differs')
    figure_checks=[]
    for panel in figure_provenance['panels']:
        fpath=ROOT/'figures'/f"{panel['name']}.pdf"
        if hashlib.sha256(fpath.read_bytes()).hexdigest()!=panel['sha256']:
            errors.append(f"Heatmap file changed: {panel['name']}")
        with pymupdf.open(fpath) as graphic:
            nums=[int(w[4]) for w in graphic[0].get_text('words') if re.fullmatch(r'\d+',w[4])]
            labels=list(analysis['main']['counts'])
            left,right={1:(labels[:3],labels[3:8]),2:(labels[:3],labels[8:]),3:(labels[3:8],labels[8:])}[panel['original_map']]
            expected=[analysis['main']['pair_counts'][f'{a} | {b}'] for a in left for b in right]
            match=nums==expected
            fonts=sorted({f[2] for p in graphic for f in p.get_fonts()})
            if not match or 'Type3' in fonts or graphic[0].get_images():
                errors.append(f"Heatmap data/vector check failed: {panel['name']}")
            figure_checks.append({'panel':panel['name'],'cells':len(nums),'match':match,'font_types':fonts,'raster_images':len(graphic[0].get_images())})
    d=pymupdf.open(ROOT/'main.pdf')
    pages=[];reference_pages=[];fonts=[]
    for i,p in enumerate(d,1):
        txt=p.get_text()
        if p.search_for('References'):reference_pages.append(i)
        p.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(str(qa/f'page-{i}.png'))
        spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
        outside=[s['text'] for s in spans if s['bbox'][0]<53 or s['bbox'][2]>559 or s['bbox'][1]<35 or s['bbox'][3]>740]
        if outside:errors.append(f'Content outside expected page area on page {i}: {outside}')
        pages.append({'page':i,'width_pt':p.rect.width,'height_pt':p.rect.height,
                      'word_count':len(txt.split()),'outside_area':outside})
        if p.rect.width!=612 or p.rect.height!=792:errors.append('Not US Letter')
        fonts+=p.get_fonts()
    body_last_page=min(reference_pages) if reference_pages else len(d)
    if body_last_page>4:errors.append('Body exceeds four pages')
    fonttypes=sorted({f[2] for f in fonts})
    if 'Type3' in fonttypes:errors.append('Type 3 fonts present')
    official=ROOT/'evidence/sources/author_kit_official.zip'
    template={}
    if official.exists():
        with zipfile.ZipFile(official) as z:
            for filename in ['aaai2027.sty','aaai2027.bst']:
                names=[s for s in z.namelist() if s.endswith('/'+filename) or s==filename]
                same=any(z.read(s)==(ROOT/filename).read_bytes() for s in names)
                template[filename]={'matches_official_download':same,'sha256':hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()}
                if not same:errors.append(f'{filename} differs from official kit')
    report={'pdf_sha256':hashlib.sha256((ROOT/'main.pdf').read_bytes()).hexdigest(),
            'total_pages':len(d),'body_last_page':body_last_page,'references_start_page':reference_pages,
            'pages':pages,'font_types':fonttypes,'cited_references':len(keys),'bib_database_records':len(bibkeys),
            'heatmap_comparisons':comparisons,'vector_figure_checks':figure_checks,'official_template':template,
            'errors':errors,'status':'PASS' if not errors else 'FAIL',
            'visual_review':'Rendered PNGs require manual visual inspection; automated checks alone are insufficient.'}
    (qa/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (qa/'main.txt').write_text('\n\n'.join(f'=== PAGE {i+1} ===\n'+p.get_text() for i,p in enumerate(d)),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
