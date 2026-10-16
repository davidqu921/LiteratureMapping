"""Make an ASCII BibTeX copy safe for classic BibTeX's author-initial processing.

Bibliographic facts and DOI keys are unchanged. Non-ASCII initials must be
braced TeX accents; otherwise BibTeX can split a UTF-8 character mid-byte.
"""
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def texchar(c):
    simple={'\u2013':'--','\u2014':'---','\u2019':"'",'\u2018':"'",
            '\u201c':'``','\u201d':"''",'\u0131':r'{\i}',
            '\u0142':r'{\l}','\u00a0':' ', '\u00df':r'{\ss}', '\u00f8':r'{\o}'}
    if ord(c)<128:return c
    if c in simple:return simple[c]
    n=unicodedata.normalize('NFD',c)
    accents={'\u0308':'"','\u0301':"'",'\u0300':'`','\u030c':'v',
             '\u0327':'c','\u0303':'~','\u0302':'^','\u0306':'u','\u030a':'r'}
    if len(n)==2 and n[1] in accents:return '{\\'+accents[n[1]]+'{'+n[0]+'}}'
    raise ValueError(f'Unsupported Unicode character: {ascii(c)}')


if __name__=='__main__':
    p=ROOT/'references.bib'
    text=p.read_text(encoding='utf-8')
    p.write_text(''.join(texchar(c) for c in text),encoding='ascii')
    print('BibTeX accents normalized; metadata unchanged.')
