"""Offline build: python build.py [--tex-bin PATH] [--verify].

Requires Python 3 and a TeX Live/MiKTeX installation with PDFLaTeX and BibTeX.
--verify additionally requires PyMuPDF. No shell/network commands are used.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tex-bin',type=Path)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--refresh-figures',action='store_true',help='Re-export heatmaps; requires PyMuPDF and the standalone LaTeX class.')
    args=parser.parse_args()
    def exe(name):
        path=args.tex_bin/(name+'.exe' if sys.platform=='win32' else name) if args.tex_bin else shutil.which(name)
        if not path: raise SystemExit(f'{name} not found. Add TeX binaries to PATH or pass --tex-bin.')
        return str(path)
    subprocess.run([sys.executable,str(ROOT/'analyze.py')],cwd=ROOT,check=True)
    if args.refresh_figures:
        command=[sys.executable,str(ROOT/'export_heatmaps.py')]
        if args.tex_bin:command += ['--tex-bin',str(args.tex_bin)]
        subprocess.run(command,cwd=ROOT,check=True)
    figure_provenance=json.loads((ROOT/'figures/provenance.json').read_text())
    if figure_provenance['source_analysis_sha256']!=hashlib.sha256((ROOT/'generated/analysis.json').read_bytes()).hexdigest():
        raise SystemExit('Heatmaps are stale. Run build.py --refresh-figures with the same --tex-bin option.')
    subprocess.run([sys.executable,str(ROOT/'prepare_bib.py')],cwd=ROOT,check=True)
    logdir=ROOT/'qa';logdir.mkdir(exist_ok=True)
    commands=[[exe('pdflatex'),'-interaction=nonstopmode','-halt-on-error','-file-line-error','main.tex'],
              [exe('bibtex'),'main']]
    commands += [commands[0],commands[0]]
    for i,cmd in enumerate(commands,1):
        result=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (logdir/f'build-{i}.txt').write_bytes(result.stdout)
        if result.returncode:
            print(result.stdout.decode(errors='replace'))
            raise SystemExit(result.returncode)
    print('Built',ROOT/'main.pdf')
    if args.verify:subprocess.run([sys.executable,str(ROOT/'verify.py')],cwd=ROOT,check=True)


if __name__=='__main__':main()
