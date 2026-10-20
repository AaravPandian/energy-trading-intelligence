"""Build the editable Energy Risk workbook using Python's standard-library OOXML writer.

Run: python -m scripts.build_excel
No Excel installation or additional spreadsheet package is required.
All reference-price series are from the bundled historical EIA CSV.
On opening the file, Excel recalculates editable assumptions and scenario formulas.
"""
from __future__ import annotations

import csv
import math
import statistics
import zipfile
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'excel' / 'Energy_Risk_Analysis.xlsx'
DATA = ROOT / 'data' / 'eia_monthly_spot_prices.csv'
EIA_BRENT = 'https://www.eia.gov/dnav/pet/hist/rbrtem.htm'
EIA_WTI = 'https://www.eia.gov/dnav/pet/hist/rwtcm.htm'

# Named styles in xl/styles.xml. Each cell uses a standard Excel style index.
NORMAL = 0
TITLE = 1
BAND = 2
HEADER = 3
INPUT = 4
DATE = 5
CURRENCY = 6
PERCENT = 7
PRICE = 8
NOTE = 9
FORMULA = 10
MONEY_INPUT = 11
PERCENT_INPUT = 12
PRICE_INPUT = 13
GOOD = 14
TEXT_INPUT = 15


def serial(d: date) -> int:
    """Excel's 1900 date system, for dates after 1900-03-01."""
    return (d - date(1899, 12, 30)).days


def colnumber(col: str) -> int:
    n = 0
    for c in col:
        n = n * 26 + ord(c.upper()) - 64
    return n


def refcoords(ref: str) -> tuple[int, int]:
    letters = ''.join(x for x in ref if x.isalpha())
    digits = ''.join(x for x in ref if x.isdigit())
    return int(digits), colnumber(letters)


class Sheet:
    def __init__(self, name: str, widths: list[float], frozen: int = 0):
        self.name = name
        self.widths = widths
        self.frozen = frozen
        self.cells = {}
        self.merges = []
        self.filters = None

    def put(self, ref: str, value, style: int = NORMAL, formula: str | None = None):
        # Formula caches are separate from the actual Excel formulas.
        self.cells[ref] = (value, style, formula)

    def merge(self, start: str, end: str):
        self.merges.append(f'{start}:{end}')

    def bar(self, row: int, label: str, end_col: str = 'F', title: bool = False):
        self.merge(f'A{row}', f'{end_col}{row}')
        self.put(f'A{row}', label, TITLE if title else BAND)
        for ix in range(2, colnumber(end_col) + 1):
            self.put(f'{chr(ix+64)}{row}', None, TITLE if title else BAND)

    def xml(self) -> bytes:
        ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        s = [f'<?xml version="1.0" encoding="utf-8"?><worksheet xmlns="{ns}">']
        maxrow = max(refcoords(r)[0] for r in self.cells)
        maxcol = max(refcoords(r)[1] for r in self.cells)
        s.append(f'<dimension ref="A1:{_col(maxcol)}{maxrow}"/>')
        s.append('<sheetViews><sheetView workbookViewId="0" showGridLines="0">')
        if self.frozen:
            s.append(f'<pane ySplit="{self.frozen}" topLeftCell="A{self.frozen+1}" activePane="bottomLeft" state="frozen"/>')
        s.append('</sheetView></sheetViews>')
        s.append('<sheetFormatPr defaultRowHeight="17"/>')
        s.append('<cols>')
        for i, w in enumerate(self.widths, start=1):
            s.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
        s.append('</cols><sheetData>')
        byrow = defaultdict(list)
        for ref, (value, style, formula) in self.cells.items():
            row, col = refcoords(ref)
            byrow[row].append((col, ref, value, style, formula))
        for row in sorted(byrow):
            height = ' ht="38" customHeight="1"' if row == 1 else (' ht="28" customHeight="1"' if any(x[3] in (BAND, HEADER) for x in byrow[row]) else '')
            s.append(f'<row r="{row}"{height}>')
            for _, ref, value, style, formula in sorted(byrow[row]):
                r = escape(ref)
                attrs = f' r="{r}" s="{style}"'
                if formula is not None:
                    cell_type = ' t="str"' if isinstance(value, str) else ''
                    cached = '' if value is None else escape(str(value))
                    s.append(f'<c{attrs}{cell_type}><f>{escape(formula)}</f><v>{cached}</v></c>')
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    s.append(f'<c{attrs}><v>{value}</v></c>')
                elif value is not None:
                    s.append(f'<c{attrs} t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>')
                else:
                    s.append(f'<c{attrs}/>')
            s.append('</row>')
        s.append('</sheetData>')
        if self.merges:
            s.append(f'<mergeCells count="{len(self.merges)}">')
            for m in self.merges:
                s.append(f'<mergeCell ref="{m}"/>')
            s.append('</mergeCells>')
        if self.filters:
            s.append(f'<autoFilter ref="{self.filters}"/>')
        s.append('<pageMargins left="0.35" right="0.35" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>')
        s.append('</worksheet>')
        return ''.join(s).encode('utf-8')


def _col(n: int) -> str:
    result = ''
    while n:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def styles_xml() -> str:
    # Styling is deliberately sparse: navy headings, teal sections, yellow editable
    # inputs, blue user-entered values, and green formula text.
    formats = [(164, '$#,##0;[Red]($#,##0);-'), (165,'0.0%;[Red](0.0%);-'),
               (166,'mmm yyyy'), (167,'#,##0.00;[Red](#,##0.00);-'),
               (168,'$#,##0.00;[Red]($#,##0.00);-'), (169, '#,##0')]
    nfmt = ''.join(f'<numFmt numFmtId="{n}" formatCode="{escape(f)}"/>' for n, f in formats)
    fonts = [
        '<font><sz val="11"/><name val="Aptos"/><color rgb="FF172D40"/></font>',
        '<font><sz val="17"/><name val="Aptos Display"/><b/><color rgb="FFFFFFFF"/></font>',
        '<font><sz val="11"/><name val="Aptos"/><b/><color rgb="FFFFFFFF"/></font>',
        '<font><sz val="11"/><name val="Aptos"/><color rgb="FF2055A3"/></font>',
        '<font><sz val="11"/><name val="Aptos"/><color rgb="FF008060"/></font>',
        '<font><sz val="10"/><name val="Aptos"/><color rgb="FF64748B"/></font>',
    ]
    fills = [
        '<fill><patternFill patternType="none"/></fill>',
        '<fill><patternFill patternType="gray125"/></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FF123047"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FF0F766E"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFFFF4B8"/><bgColor indexed="64"/></patternFill></fill>',
        '<fill><patternFill patternType="solid"><fgColor rgb="FFE9F4F0"/><bgColor indexed="64"/></patternFill></fill>',
    ]
    # fontId, fillId, numFmtId, alignment
    definition = [(0,0,0,'left'),(1,2,0,'left'),(2,3,0,'left'),(2,2,0,'left'),
                  (3,4,0,'left'),(0,0,166,'left'),(0,0,164,'right'),
                  (0,0,165,'right'),(0,0,167,'right'),(5,0,0,'left'),
                  (4,0,167,'right'),(3,4,169,'right'),(3,4,165,'right'),
                  (3,4,167,'right'),(4,5,164,'right'),(3,4,0,'left')]
    xfs = ''.join(
        f'<xf numFmtId="{num}" fontId="{font}" fillId="{fill}" borderId="0" xfId="0"'
        f' applyAlignment="1" applyNumberFormat="1"><alignment horizontal="{align}"'
        f' vertical="center" wrapText="1"/></xf>'
        for font, fill, num, align in definition
    )
    return ('<?xml version="1.0" encoding="utf-8"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<numFmts count="{len(formats)}">{nfmt}</numFmts>'
            f'<fonts count="{len(fonts)}">{"".join(fonts)}</fonts>'
            f'<fills count="{len(fills)}">{"".join(fills)}</fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            f'<cellXfs count="{len(definition)}">{xfs}</cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>')


def month_prices():
    prices = defaultdict(dict)
    with DATA.open(newline='', encoding='utf-8') as fh:
        for record in csv.DictReader(fh):
            day = date.fromisoformat(record['month'])
            prices[day][record['benchmark']] = float(record['price_usd_bbl'])
    months = sorted(prices)
    assert all(set(prices[date_]) == {'Brent','WTI'} for date_ in months)
    return months, prices


def write_workbook():
    months, prices = month_prices()
    end = len(months) + 1
    brent = [prices[d]['Brent'] for d in months]
    wti = [prices[d]['WTI'] for d in months]
    bret = [None] + [brent[i] / brent[i-1] - 1 for i in range(1,len(months))]
    wret = [None] + [wti[i] / wti[i-1] - 1 for i in range(1,len(months))]
    bvol = [None if i < 6 else statistics.stdev(bret[i-5:i+1]) * math.sqrt(12) for i in range(len(months))]
    wvol = [None if i < 6 else statistics.stdev(wret[i-5:i+1]) * math.sqrt(12) for i in range(len(months))]

    summary = Sheet('Risk Summary', [38,27,16,59,3,14,14,14,14,14,14,14,14], 3)
    assume = Sheet('Assumptions', [35,22,64,15,15,15], 3)
    history = Sheet('Monthly Prices', [18,18,18,20,20,25,22,22,54,54], 1)
    scenario = Sheet('Scenario Grid', [22,26,28,28,32,12,12,12], 3)
    sources = Sheet('Sources & Notes', [34,79,65,15,15,15], 3)
    sheets = [summary, assume, history, scenario, sources]

    # Assumptions: each editable parameter has its own address, and other sheets link to it.
    assume.bar(1,'ASSUMPTIONS  |  Blue text on yellow = editable',title=True)
    for j,v in enumerate(['Parameter','Editable value','Explanation'],1): assume.put(f'{_col(j)}3',v,HEADER)
    inputs = [
        ('Benchmark','Brent','Choose Brent or WTI monthly-average benchmark',TEXT_INPUT),
        ('Exposed volume (barrels)',10000,'Illustrative future physical purchase or sale volume',MONEY_INPUT),
        ('Price shock',.15,'Hypothetical percentage change in oil benchmark',PERCENT_INPUT),
        ('Fixed-price share',.50,'Simple perfect fixed-price coverage proxy, NOT a derivative',PERCENT_INPUT),
        ('Periods per year',12,'Monthly annualisation convention uses SQRT(12)',MONEY_INPUT),
        ('Rolling window (months)',6,'The fixed historical chart uses six MONTHLY changes',MONEY_INPUT),
        ('Position','Buyer','Buyer incurs cost; seller receives cash flow',TEXT_INPUT),
        ('Risk-rule threshold',.30,'Illustrative annualised-volatility review threshold',PERCENT_INPUT),
    ]
    for row, (setting,val,description,sty) in enumerate(inputs,start=5):
        assume.put(f'A{row}',setting)
        assume.put(f'B{row}',val,sty)
        assume.put(f'C{row}',description,NOTE)
    assume.bar(14,'READ BEFORE USING',end_col='F')
    for row, text in enumerate([
        'A beginner educational project, not a pricing system or investment recommendation.',
        'Source prices are U.S. EIA MONTHLY averages; they are not live/executable market prices.',
        'Fixed-price share assumes perfect coverage, ignoring basis, premiums, fees and margin.',
        'Changing rolling-window input B10 does NOT change the historical six-month spreadsheet formulas.',
        '2026 data are Jan–Aug only; do not compare a partial 2026 with full-year totals.',
    ],start=15): assume.put(f'A{row}',text,NOTE)

    # Price history: source observations stored as numeric cells, derived columns as Excel formulas.
    headers = ['Month','Brent ($/bbl)','WTI ($/bbl)','Brent MoM change','WTI MoM change',
               'Brent - WTI ($/bbl)','Brent 6m ann. vol','WTI 6m ann. vol','Brent EIA source URL','WTI EIA source URL']
    for j,label in enumerate(headers,1): history.put(f'{_col(j)}1',label,HEADER)
    history.filters = f'A1:J{end}'
    for i, date_ in enumerate(months):
        row = i+2
        history.put(f'A{row}',serial(date_),DATE)
        history.put(f'B{row}',brent[i],PRICE)
        history.put(f'C{row}',wti[i],PRICE)
        if i:
            history.put(f'D{row}',bret[i],PERCENT,f'B{row}/B{row-1}-1')
            history.put(f'E{row}',wret[i],PERCENT,f'C{row}/C{row-1}-1')
        history.put(f'F{row}',brent[i]-wti[i],PRICE,f'B{row}-C{row}')
        if i >= 6:
            history.put(f'G{row}',bvol[i],PERCENT,f'STDEV(D{row-5}:D{row})*SQRT(Assumptions!$B$9)')
            history.put(f'H{row}',wvol[i],PERCENT,f'STDEV(E{row-5}:E{row})*SQRT(Assumptions!$B$9)')
        history.put(f'I{row}',EIA_BRENT,NOTE)
        history.put(f'J{row}',EIA_WTI,NOTE)

    # Summary: formulas cached to display a valid initial output even in non-calculating previews.
    summary.bar(1,'ENERGY TRADING  |  RISK INTELLIGENCE',end_col='M',title=True)
    for j,value in enumerate(['Historical market indicators','Value','Unit','Interpretation'],1): summary.put(f'{_col(j)}3',value,HEADER)
    metrics = [
        ('As of',serial(months[-1]),'Month','Last observation in frozen EIA dataset',f"'Monthly Prices'!A{end}",DATE),
        ('Brent average',brent[-1],'USD/bbl','EIA Europe Brent FOB spot monthly average',f"'Monthly Prices'!B{end}",PRICE),
        ('WTI average',wti[-1],'USD/bbl','EIA Cushing WTI FOB spot monthly average',f"'Monthly Prices'!C{end}",PRICE),
        ('Brent minus WTI',brent[-1]-wti[-1],'USD/bbl','Benchmark premium, NOT an arbitrage profit',f"'Monthly Prices'!F{end}",PRICE),
        ('Brent month-on-month',bret[-1],'%','Change in monthly averages vs previous month',f"'Monthly Prices'!D{end}",PERCENT),
        ('WTI month-on-month',wret[-1],'%','Change in monthly averages vs previous month',f"'Monthly Prices'!E{end}",PERCENT),
        ('Brent annualised 6m vol',bvol[-1],'%','Six monthly changes sample deviation x sqrt(12)',f"'Monthly Prices'!G{end}",PERCENT),
        ('WTI annualised 6m vol',wvol[-1],'%','Six monthly changes sample deviation x sqrt(12)',f"'Monthly Prices'!H{end}",PERCENT),
    ]
    for row,(label,value,unit,explain,formula,style) in enumerate(metrics,5):
        summary.put(f'A{row}',label)
        summary.put(f'B{row}',value,style,formula)
        summary.put(f'C{row}',unit)
        summary.put(f'D{row}',explain,NOTE)
    summary.bar(14,'COMMERCIAL SCENARIO  |  Edit yellow cells on Assumptions',end_col='D')
    amount=10000
    shock=.15
    fixed=.5
    price=brent[-1]
    base=-price*amount
    shocked_price=price*(1+shock)
    shocked=-shocked_price*amount
    change=shocked-base
    after=change*(1-fixed)
    summary_values = [
        (15,'Benchmark','Brent','Assumptions!B5',NORMAL),
        (16,'Current reference price',price,'IF(B15="Brent",B6,B7)',PRICE),
        (17,'Position','Buyer','Assumptions!B11',NORMAL),
        (18,'Price shock',shock,'Assumptions!B7',PERCENT),
        (19,'Fixed-price share',fixed,'Assumptions!B8',PERCENT),
        (20,'Exposure in barrels',amount,'Assumptions!B6',MONEY_INPUT),
        (22,'Base signed cash flow ($)',base,'IF(B17="Buyer",-1,1)*B16*B20',CURRENCY),
        (23,'Shocked reference price ($/bbl)',shocked_price,'B16*(1+B18)',PRICE),
        (24,'Shocked signed cash flow ($)',shocked,'IF(B17="Buyer",-1,1)*B23*B20',CURRENCY),
        (25,'Change before coverage proxy ($)',change,'B24-B22',CURRENCY),
        (26,'Change after coverage proxy ($)',after,'B25*(1-B19)',GOOD),
        (27,'Cash flow after coverage proxy ($)',base+after,'B22+B26',CURRENCY),
        (29,'Rule-based risk review','ELEVATED: review exposure controls' if bvol[-1]>=.30 else 'ROUTINE: monitor exposures',
         'IF(IF(B15="Brent",B11,B12)>=Assumptions!B12,"ELEVATED: review exposure controls","ROUTINE: monitor exposures")',NORMAL)
    ]
    for row, label, value, formula, style in summary_values:
        summary.put(f'A{row}',label)
        summary.put(f'B{row}',value,style,formula)
    summary.put('A31','Historical cut',NOTE)
    summary.put('B31','August 2026',NOTE)
    summary.put('A32','Sources',NOTE)
    summary.put('B32','U.S. Energy Information Administration',NOTE)
    summary.put('A33','Important',NOTE)
    summary.put('B33','Illustrative cost/revenue exposure, not actual hedge effectiveness',NOTE)

    # Shock ladder, all linked back to Assumptions and Risk Summary.
    scenario.bar(1,'SCENARIO GRID  |  Buyer / Seller price-shock sensitivity',end_col='H',title=True)
    for j,label in enumerate(['Price shock','Shocked ($/bbl)','Impact before proxy ($)','Impact after proxy ($)','Interpretation'],1):
        scenario.put(f'{_col(j)}3',label,HEADER)
    for row, sh in enumerate([-.20,-.10,-.05,0,.05,.10,.20],4):
        raw=-price*amount*sh
        hedged=raw*(1-fixed)
        scenario.put(f'A{row}',sh,PERCENT_INPUT)
        scenario.put(f'B{row}',price*(1+sh),PRICE,f"'Risk Summary'!$B$16*(1+A{row})")
        scenario.put(f'C{row}',raw,CURRENCY,f'IF(\'Risk Summary\'!$B$17="Buyer",-1,1)*\'Risk Summary\'!$B$20*\'Risk Summary\'!$B$16*A{row}')
        scenario.put(f'D{row}',hedged,GOOD,f"C{row}*(1-'Risk Summary'!$B$19)")
        scenario.put(f'E{row}', 'Favourable' if hedged>0 else ('Unfavourable' if hedged<0 else 'No change'),NORMAL,
                     f'IF(D{row}>0,"Favourable",IF(D{row}<0,"Unfavourable","No change"))')
    scenario.put('A13','Interpretation',BAND)
    scenario.put('B13','Positive impact = favourable signed cash-flow change; negative = unfavourable.',NOTE)
    scenario.put('A14','Note',BAND)
    scenario.put('B14','Fixed-price share is a simplistic proxy, not a valuation of a futures or options hedge.',NOTE)

    sources.bar(1,'METHODOLOGY  |  Sources & caveats',end_col='F',title=True)
    for j,value in enumerate(['Dataset','Official EIA source','Description'],1): sources.put(f'{_col(j)}3',value,HEADER)
    sources.put('A4','Brent monthly spot average')
    sources.put('B4',EIA_BRENT,NOTE)
    sources.put('C4','Europe Brent Spot Price FOB, USD/bbl')
    sources.put('A5','WTI monthly spot average')
    sources.put('B5',EIA_WTI,NOTE)
    sources.put('C5','Cushing, Oklahoma WTI Spot Price FOB, USD/bbl')
    sources.bar(7,'DEFINITIONS / IMPORTANT LIMITS')
    notes = [
        ('Historical snapshot','January 2021 – August 2026; 68 complete months per benchmark'),
        ('Source accessed','20 October 2026; frozen offline educational snapshot'),
        ('Monthly price','EIA average price across a month; not a first-day close or quoted futures price'),
        ('Monthly change','Current monthly average / previous monthly average - 1'),
        ('Spread','Brent monthly average minus WTI monthly average'),
        ('Rolling volatility','Sample standard deviation of six monthly changes times sqrt(12)'),
        ('Coverage proxy','Pre-fixed share is insensitive to price shock, by assumption'),
        ('Buyer impact','Signed change in cash flow is negative when reference price rises'),
        ('Seller impact','Signed change in cash flow is positive when reference price rises'),
        ('Excluded','Futures curves, funding, transport, FX, basis, margin, credit, storage, taxes'),
        ('Incomplete year','2026 includes Jan to Aug, not 12 months'),
        ('Decision status','These are educational conditional prompts, NOT trading signals'),
    ]
    for row, (label, val) in enumerate(notes,9):
        sources.put(f'A{row}',label)
        sources.put(f'B{row}',val,NOTE)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as package:
        def add(location: str, content: str | bytes):
            xml = content.encode('utf-8') if isinstance(content,str) else content
            ET.fromstring(xml)  # Catch malformed XML before shipping.
            package.writestr(location, xml)
        wb_ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
        rel_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        p_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
        sheet_xml = ''.join(f'<sheet name="{escape(s.name).replace("&amp;", "&amp;")}" sheetId="{n}" r:id="rId{n}"/>'
                            for n,s in enumerate(sheets,1))
        add('xl/workbook.xml', f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<workbook xmlns="{wb_ns}" xmlns:r="{rel_ns}">'
            f'<sheets>{sheet_xml}</sheets><calcPr calcId="191029" calcMode="auto" fullCalcOnLoad="1"/></workbook>')
        rels = ''.join(f'<Relationship Id="rId{n}" Type="{rel_ns}/worksheet" Target="worksheets/sheet{n}.xml"/>'
                       for n in range(1, len(sheets)+1))
        rels += f'<Relationship Id="rId{len(sheets)+1}" Type="{rel_ns}/styles" Target="styles.xml"/>'
        add('xl/_rels/workbook.xml.rels',f'<?xml version="1.0" encoding="utf-8"?><Relationships xmlns="{p_ns}">{rels}</Relationships>')
        add('xl/styles.xml',styles_xml())
        for n, sheet in enumerate(sheets,1):
            add(f'xl/worksheets/sheet{n}.xml',sheet.xml())
        overrides = ''.join(f'<Override PartName="/xl/worksheets/sheet{n}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                            for n in range(1,len(sheets)+1))
        add('[Content_Types].xml','<?xml version="1.0" encoding="utf-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + overrides + '</Types>')
        add('_rels/.rels','<?xml version="1.0" encoding="utf-8"?>'
            f'<Relationships xmlns="{p_ns}">'
            f'<Relationship Id="rId1" Type="{rel_ns}/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
    return OUTPUT


if __name__ == '__main__':
    print('Created:',write_workbook())
