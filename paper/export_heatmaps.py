"""Re-export the existing three count heatmaps as publication-quality vector PDFs.

Same 55 intersections and purple=count/N shading as output/final_map.
Uses embedded Type 1 text at 10 pt instead of the original PDF's Type 3 fonts.
Run after analyze.py: python export_heatmaps.py [--tex-bin PATH].
No network access. Requires PDFLaTeX; PyMuPDF verifies the exported graphics.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent
PANELS = [
    ('evaluator_behaviors', 1, range(0, 3), range(3, 8), 'Evaluator'),
    ('evaluator_outcomes', 2, range(0, 3), range(8, 13), 'Evaluator'),
    ('behavior_outcomes', 3, range(3, 8), range(8, 13), 'Sycophantic behavior'),
]
DISPLAY = {
    'Human - Specialist': 'Human: specialist', 'Human - Authors': 'Human: authors',
    'AI - prompted': 'AI: prompted', 'Hallucination Agreement': 'Hallucination agreement',
    'Bias Agreement': 'Bias agreement', 'Obsequiousness': 'Obsequiousness',
    'Stance Change': 'Stance change',
    'Failure to challenge/trying to get along': 'Failure to challenge / getting along',
    'User performance': 'User task performance',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tex-bin', type=Path)
    args = parser.parse_args()
    tex = str(args.tex_bin/('pdflatex.exe' if sys.platform=='win32' else 'pdflatex')) if args.tex_bin else shutil.which('pdflatex')
    if not tex: raise SystemExit('PDFLaTeX not found; pass --tex-bin.')
    stats = json.loads((ROOT/'generated/analysis.json').read_text(encoding='utf-8'))
    counts = stats['main']['counts']; labels = list(counts); n = stats['main']['N']
    figures = ROOT/'figures'; figures.mkdir(exist_ok=True)
    work = ROOT/'qa/heatmap_build'; work.mkdir(parents=True, exist_ok=True)
    evidence = []
    for name, number, left, right, heading in PANELS:
        a = [labels[i] for i in left]; b = [labels[i] for i in right]
        values = [[stats['main']['pair_counts'][f'{x} | {y}'] for y in b] for x in a]
        old = ROOT.parent/'output/final_map'/f'map_{number:02d}_heatmap.tex'
        if old.exists():
            previous = [int(x) for x in re.findall(r'\\cellcolor\{[^}]*\}(\d+)', old.read_text(encoding='utf-8'))]
            if previous != [v for row in values for v in row]:
                raise ValueError(f'Original map {number} differs; resolve before exporting.')
        table_rows = []
        for label, row in zip(a, values):
            rendered = [f'\\cellcolor{{purple!{round(100*v/n)}}}{v}' for v in row]
            table_rows.append(DISPLAY.get(label,label)+f" ($n={counts[label]['n']}$) & "+' & '.join(rendered)+r' \\ \hline')
        header = ' & '.join(r'\hspace{0pt}\textbf{'+DISPLAY.get(label,label)+'}' for label in b)
        source = r'''\documentclass[10pt,border=0.5pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{newtxtext}
\usepackage[table]{xcolor}
\usepackage{tabularx,array}
\hyphenation{hal-lu-ci-na-tion ob-se-qui-ous-ness per-for-mance}
\begin{document}
\begin{minipage}{502pt}
\renewcommand{\arraystretch}{1.45}
\begin{tabularx}{\linewidth}{|>{\raggedright\arraybackslash}p{0.29\linewidth}|*{5}{>{\centering\arraybackslash}X|}}
\hline
''' + r'\textbf{'+heading+'} & '+header+r' \\ \hline'+'\n'+'\n'.join(table_rows)+r'''
\end{tabularx}
\end{minipage}
\end{document}
'''
        (figures/f'{name}.tex').write_text(source,encoding='utf-8')
        command = [tex,'-interaction=nonstopmode','-halt-on-error',f'-output-directory={work}',str(figures/f'{name}.tex')]
        result = subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (work/f'{name}-build.txt').write_bytes(result.stdout)
        if result.returncode:raise RuntimeError(result.stdout.decode(errors='replace'))
        log = (work/f'{name}.log').read_text(errors='replace')
        if 'Overfull' in log:raise ValueError(f'Overflow in {name}')
        target = figures/f'{name}.pdf'
        shutil.copyfile(work/f'{name}.pdf',target)
        with pymupdf.open(target) as doc:
            page = doc[0]
            if page.get_images() or any(f[2]=='Type3' for f in page.get_fonts()):
                raise ValueError('Graphic must be vector with embedded outline fonts.')
            actual = [int(w[4]) for w in page.get_text('words') if re.fullmatch(r'\d+',w[4])]
            if actual != [v for row in values for v in row]:
                raise ValueError('PDF cell values differ from statistics')
            page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(str(work/f'{name}.png'))
            evidence.append({'name':name,'original_map':number,'values':values,
                             'font_types':sorted({f[2] for f in page.get_fonts()}),
                             'raster_images':len(page.get_images()),'pdf_cell_values_verified':True,
                             'page_size_pt':[page.rect.width,page.rect.height],
                             'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    original = ROOT.parent/'output/final_map/main_heatmaps.pdf'
    original_fonts = None
    if original.exists():
        with pymupdf.open(original) as old_pdf:
            original_fonts = sorted({f[2] for p in old_pdf for f in p.get_fonts()})
    report = {'source_analysis_sha256':hashlib.sha256((ROOT/'generated/analysis.json').read_bytes()).hexdigest(),
              'original_pdf_sha256':hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None,
              'original_pdf_font_types':original_fonts, 'cell_count':55,
              'change':'Re-typeset existing count heatmaps with Type 1 text; no recoding. Add row totals and clarify user task performance label.',
              'panels':evidence}
    (figures/'provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Exported three vector PDFs; all 55 cell values verified.')


if __name__=='__main__':main()
