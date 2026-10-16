"""Read XLSX cached values without executing formulas; audit the supplied workflow.

Usage: python audit_workbook.py [path/to/workbook.xlsx]
No assumption is made that current A/B cells are pre-adjudication decisions.
"""
import collections
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_workbook(path):
    with zipfile.ZipFile(path) as z:
        shared = ["".join(t.text or "" for t in s.findall(".//m:t", NS))
                  for s in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = {}
        book = ET.fromstring(z.read('xl/workbook.xml'))
        for sheet in book.find('m:sheets', NS):
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = rels[rid]
            target = target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows = []
            for row in ET.fromstring(z.read(target)).findall('.//m:sheetData/m:row', NS):
                cells = {'_row': int(row.attrib['r'])}
                for c in row:
                    value = c.find('m:v', NS)
                    val = '' if value is None else value.text or ''
                    if c.attrib.get('t') == 's': val = shared[int(val)]
                    elif c.attrib.get('t') == 'inlineStr':
                        val = ''.join(c.find('m:is', NS).itertext())
                    if val.strip(): cells[re.sub(r'\d', '', c.attrib['r'])] = val.strip()
                if len(cells) > 1: rows.append(cells)
            sheets[sheet.attrib['name']] = rows
        return sheets


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent/'data'/'lit-map 2026s sycophancy.xlsx'
    sheets = read_workbook(source)
    csvrows = list(csv.reader((ROOT/'data/final_map.csv').open(encoding='utf-8-sig')))
    mismatches = []
    sheetfinal = {r['_row']: r for r in sheets['FINAL MAP']}
    for rownum, row in enumerate(csvrows, 1):
        for i, val in enumerate(row):
            col = chr(65+i)
            if val.strip() != sheetfinal.get(rownum, {}).get(col, ''):
                mismatches.append(f'{col}{rownum}')
    if mismatches: raise ValueError(f'CSV/workbook FINAL MAP mismatches: {mismatches}')
    allrows = sheets['All Papers'][1:]
    keycounts = collections.Counter(r['B'].lower() for r in allrows)
    finalkeys = {r[2].lower() for r in csvrows[3:]}
    mapping = sheets['Mapping Discrepancies'][3:]
    kept = {r['B'].lower():r for r in mapping if r.get('G') == 'X'}
    if set(kept) != finalkeys: raise ValueError('Final DOI set differs from retained mapping records')
    for row in csvrows[3:]:
        earlier = kept[row[2].lower()]
        for i in range(4,17):
            col = chr(74+i-4)  # final E:Q corresponds to earlier J:V
            if row[i].strip() != earlier.get(col, ''):
                raise ValueError(f'Mapping/FINAL mismatch: {row[2]} {col}')
    screens = {}
    for name in ('INCEXC A','INCEXC B'):
        rows = sheets[name][1:]
        screens[name] = {'rows':len(rows), 'unique_keys':len({r['B'].lower() for r in rows}),
                         'distinct_rater_names':len({r.get('D') for r in rows}),
                         'decisions': dict(collections.Counter(r.get('E','') for r in rows)),
                         'exclusion_reasons':dict(collections.Counter(r.get('F','') for r in rows if r.get('E') == 'Exclude'))}
    a,b = sheets['INCEXC A'][1:],sheets['INCEXC B'][1:]
    if [r['B'].lower() for r in a] != [r['B'].lower() for r in b]: raise ValueError('Screening rows not aligned')
    disagreements = [{'doi':ra['B'], 'row':ra['_row'], 'A':ra.get('E'), 'B':rb.get('E'),
                      'in_final':ra['B'].lower() in finalkeys}
                     for ra,rb in zip(a,b) if ra.get('E') != rb.get('E')]
    mapping_a = {r['B'].lower():r for r in sheets['Mapping A'][3:]}
    mapping_b = {r['B'].lower():r for r in sheets['Mapping B'][3:]}
    differences = []
    for key in finalkeys:
        ra, rb = mapping_a[key], mapping_b[key]
        for i in range(5,20):
            col=chr(65+i)
            if ra.get(col,'') != rb.get(col,''):
                differences.append({'doi':key,'field':sheets['Mapping A'][1].get(col,col),
                                    'A':ra.get(col,''),'B':rb.get(col,'')})
    no_retainedevaluator = [r for r in csvrows[3:] if not any(v.strip() for v in r[4:7])]
    omitted_explanation = [{'doi':r[2], 'Human - general':kept[r[2].lower()].get('H',''),
                            'Human - Student':kept[r[2].lower()].get('I','')}
                           for r in no_retainedevaluator]
    screenunion = {r['B'].lower() for r in a+b if r.get('E')=='Include'}
    mappingkeys = {r['B'].lower() for r in mapping}
    summary = {'source':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
               'final_csv_all_cells_match':True, 'mapping_retained_13_fields_all_match':True,
               'all_papers_rows':len(allrows),'all_papers_unique_keys':len(keycounts),
               'duplicated_pool_keys':{k:v for k,v in keycounts.items() if v>1},
               'screening':screens, 'current_screening_disagreements':disagreements,
               'screening_caution':'Current workbook values; timing and independence of original decisions unverified. Not a reliability estimate.',
               'mapping_records':len(mapping),'mapping_retained':len(kept),
               'mapping_marked_delete':[{'doi':r['B'],'row':r['_row'],'title':r['C']} for r in mapping if r.get('G')=='DELETE'],
               'mapping_not_in_screening_include_union':sorted(mappingkeys-screenunion),
               'screening_include_union_not_in_mapping':sorted(screenunion-mappingkeys),
               'current_mapping_A_B_differences_for_final':differences,
               'final_unmarked_evaluator_earlier_general_student':omitted_explanation,
               'query_validation_rows':len(sheets['Query Validation'])-1,
               'query_validation_yes':[r for r in sheets['Query Validation'][1:] if r.get('C')=='Yes'],
               'unrecoverable':['executed search strings','search dates','database search protocol',
                                'pre-adjudication independence','rationale for all 3 mapping deletions',
                                'reason for dropping general/student evaluator columns']}
    out=ROOT/'generated/workbook_audit.json'
    out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
