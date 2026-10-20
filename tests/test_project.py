import sqlite3
import math
import pandas as pd
import pytest
from src.analytics import load_prices, calculate_metrics, market_wide, risk_snapshot, recent_trend
from src.scenarios import evaluate_scenario, scenario_table
from src.recommendations import commercial_recommendations
from src.database import populate_database, run_sql


def test_snapshot_shape_and_period():
    d = load_prices()
    assert len(d) == 136
    assert d['month'].nunique() == 68
    assert d['month'].min() == pd.Timestamp('2021-01-01')
    assert d['month'].max() == pd.Timestamp('2026-08-01')
    assert set(d['benchmark']) == {'Brent', 'WTI'}


def test_source_prices_match_eia_observations():
    p = load_prices().pivot(index='month', columns='benchmark', values='price_usd_bbl')
    assert p.loc['2022-06-01', 'Brent'] == 122.71
    assert p.loc['2022-06-01', 'WTI'] == 114.84
    assert p.loc['2026-08-01', 'Brent'] == 91.08
    assert p.loc['2026-08-01', 'WTI'] == 83.90


def test_return_annualisation_and_first_valid_month():
    m = calculate_metrics(load_prices())
    brent = m[m['benchmark'] == 'Brent'].reset_index(drop=True)
    assert pd.isna(brent.loc[0, 'monthly_return'])
    assert brent.loc[1, 'monthly_return'] == pytest.approx(62.28/54.77 - 1)
    assert pd.isna(brent.loc[5, 'annualised_volatility'])
    assert not pd.isna(brent.loc[6, 'annualised_volatility'])
    expected = brent['monthly_return'].iloc[1:7].std(ddof=1) * math.sqrt(12)
    assert brent.loc[6, 'annualised_volatility'] == pytest.approx(expected)


def test_cross_benchmark_spread():
    w = market_wide(calculate_metrics(load_prices()))
    r = w.loc[w['month'].eq(pd.Timestamp('2026-08-01'))].iloc[0]
    assert r['spread_usd_bbl'] == pytest.approx(7.18)


def test_buyer_higher_price_is_unfavourable():
    r = evaluate_scenario(80, 1000, .10, .5, 'Buyer')
    assert r.base_cashflow == -80_000
    assert r.change_without_hedge == pytest.approx(-8_000)
    assert r.change_after_hedge == pytest.approx(-4_000)
    assert r.post_hedge_cashflow == pytest.approx(-84_000)


def test_seller_higher_price_is_favourable():
    r = evaluate_scenario(80, 1000, .10, 0, 'Seller')
    assert r.change_without_hedge == pytest.approx(8_000)
    assert r.change_after_hedge == pytest.approx(8_000)


def test_hedge_100_percent_fixes_price_in_proxy():
    r = evaluate_scenario(75, 5000, -.20, 1.0, 'Buyer')
    assert r.change_after_hedge == 0


def test_invalid_inputs():
    with pytest.raises(ValueError):
        evaluate_scenario(0, 1000, .1, .5, 'Buyer')
    with pytest.raises(ValueError):
        evaluate_scenario(80, 1000, .1, 1.5, 'Buyer')
    with pytest.raises(ValueError):
        evaluate_scenario(80, 1000, .1, .5, 'Trader')


def test_seven_scenario_shocks():
    t = scenario_table(80, 1000, 0.25, 'Buyer')
    assert len(t) == 7
    assert t.loc[t['Price shock (%)'].eq(0), 'Impact after hedge ($)'].iloc[0] == 0


def test_database_and_sql():
    with sqlite3.connect(':memory:') as conn:
        populate_database(conn)
        assert conn.execute('SELECT COUNT(*) FROM spot_prices').fetchone()[0] == 136
        assert conn.execute('SELECT COUNT(*) FROM risk_metrics').fetchone()[0] == 136
        latest = run_sql('05_latest_risk_snapshot.sql', conn)
        assert len(latest) == 2
        assert set(latest['month']) == {'2026-08'}
        yearly = run_sql('01_yearly_prices.sql', conn)
        assert yearly['months_in_sample'].tolist() == [12, 12, 12, 12, 12, 8]


def test_risk_snapshot_matches_latest():
    m = calculate_metrics(load_prices())
    snapshot = risk_snapshot(m, 'WTI')
    assert snapshot['latest_price'] == 83.90
    assert 0 <= snapshot['annualised_volatility'] < 2
    assert math.isfinite(recent_trend(m, 'WTI'))


def test_commercial_advice_nonempty():
    recs = commercial_recommendations(.4, .12, 7.1, 4.0, 'Buyer')
    assert len(recs) == 4
    assert any('premium' in r.lower() or 'spread' in r.lower() for r in recs)


def test_excel_workbook_is_complete_and_contains_calculation_formulas():
    """Validate the finished Excel file without requiring Excel or a spreadsheet package."""
    from pathlib import Path
    from xml.etree import ElementTree as ET
    import zipfile

    workbook = Path(__file__).resolve().parents[1] / 'excel' / 'Energy_Risk_Analysis.xlsx'
    assert workbook.is_file()
    with zipfile.ZipFile(workbook) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert {'[Content_Types].xml', 'xl/workbook.xml', 'xl/styles.xml',
                'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml',
                'xl/worksheets/sheet3.xml', 'xl/worksheets/sheet4.xml',
                'xl/worksheets/sheet5.xml'}.issubset(names)
        ns = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        labels = [s.attrib['name'] for s in book.findall('x:sheets/x:sheet',ns)]
        assert labels == ['Risk Summary', 'Assumptions', 'Monthly Prices',
                          'Scenario Grid', 'Sources & Notes']
        scenario = ET.fromstring(archive.read('xl/worksheets/sheet4.xml'))
        formulas = {c.attrib['r']: c.find('x:f',ns).text
                    for c in scenario.findall('.//x:sheetData/x:row/x:c',ns)
                    if c.find('x:f',ns) is not None}
        assert len(formulas) >= 20
        assert 'Risk Summary' in formulas['B4']
        assert 'Risk Summary' in formulas['D10']


def test_excel_workbook_is_reproducible(tmp_path,monkeypatch):
    from scripts import build_excel
    target = tmp_path / 'Energy_Risk_Analysis.xlsx'
    monkeypatch.setattr(build_excel, 'OUTPUT', target)
    assert build_excel.write_workbook() == target
    assert target.stat().st_size > 12_000
