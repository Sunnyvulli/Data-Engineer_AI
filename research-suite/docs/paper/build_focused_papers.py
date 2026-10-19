"""Render focused Markdown drafts and verify table values against saved results."""
from pathlib import Path
from html import escape
import json
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def verify_tables():
    text = (HERE / 'PHISHING_MANUSCRIPT.md').read_text()
    result = json.loads((ROOT / 'results/validation/visual-phishing.json').read_text())
    names = {'url': 'URL', 'image': 'Image', 'fusion': 'Equal fusion'}
    for row in result['experiments']:
        expected = f"| {row['seed']} | {names[row['policy']]} | {row['average_precision']:.6f} | {row['recall']:.6f} | {row['false_positive_rate']:.6f} |"
        assert expected in text, expected
    text = (HERE / 'ASTRONOMY_MANUSCRIPT.md').read_text()
    result = json.loads((ROOT / 'results/followup/recurrent-comparison.json').read_text())
    for split, title in [('source', 'Source test'), ('independent', 'Simulated remainder')]:
        for row in result[f'{split}_results']:
            m = row['metrics'] if split == 'independent' else row
            b = row['budget'] if split == 'independent' else row
            name = 'GRU adaptation' if row['model'] == 'rapid_inspired_gru' else 'Frozen forest'
            expected = f"| {title} | {name} | {m['n']} | {m['positives']} | {m['average_precision']:.6f} | {b['selected']} | {b['rare_found']} |"
            assert expected in text, expected


def render(stem):
    styles = getSampleStyleSheet()
    styles['BodyText'].fontName = 'Times-Roman'
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 13
    styles['BodyText'].spaceAfter = 6
    styles['Title'].fontSize = 19
    styles['Title'].leading = 23
    styles['Heading2'].keepWithNext = True
    styles['BodyText'].allowWidows = 0
    styles['BodyText'].allowOrphans = 0
    styles.add(ParagraphStyle(name='Cell', fontName='Helvetica', fontSize=8, leading=10))
    story = []
    lines = (HERE / (stem+'.md')).read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                parts = [p.strip() for p in lines[i].strip('|').split('|')]
                if not all(re.fullmatch('[-: ]+', p) for p in parts):
                    rows.append([Paragraph(escape(p), styles['Cell']) for p in parts])
                i += 1
            widths = [45, 95, 85, 85, 85] if len(rows[0]) == 5 else [85, 90, 50, 50, 70, 65, 65]
            table = Table(rows, colWidths=[492*w/sum(widths) for w in widths], repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND', (0,0),(-1,0),colors.HexColor('#e7edf4')), ('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6), ('LINEBELOW',(0,0),(-1,-1),.25,colors.HexColor('#cbd5e1'))]))
            story.extend([table, Spacer(1,10)])
            continue
        if line.startswith('# '):
            story.append(Paragraph(escape(line[2:]), styles['Title']))
        elif line.startswith('## '):
            story.append(Paragraph(escape(line[3:]), styles['Heading2']))
        elif line.strip():
            story.append(Paragraph(escape(line), styles['BodyText']))
        i += 1
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(60,30,'Research draft for author review | 19 October 2026')
        canvas.drawRightString(552,30,str(doc.page))
    SimpleDocTemplate(str(HERE/(stem+'.pdf')), pagesize=(612,792), leftMargin=60, rightMargin=60, topMargin=48, bottomMargin=48, author='Hanumantha Rao Vulli', title=lines[0][2:]).build(story,onFirstPage=footer,onLaterPages=footer)


if __name__ == '__main__':
    verify_tables()
    for stem in ['PHISHING_MANUSCRIPT', 'ASTRONOMY_MANUSCRIPT']:
        render(stem)
        print('Rendered', stem)
