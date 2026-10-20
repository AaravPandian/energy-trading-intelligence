"""SQLite database builder and curated SQL examples."""
from pathlib import Path
import sqlite3
import pandas as pd
from .analytics import load_prices, calculate_metrics, ROOT

DB_PATH = ROOT / 'data' / 'energy_trading.sqlite'


def populate_database(conn: sqlite3.Connection) -> None:
    raw = load_prices()
    metrics = calculate_metrics(raw)
    long = raw.assign(month=raw['month'].dt.strftime('%Y-%m-%d'))
    long[['month', 'benchmark', 'price_usd_bbl', 'source_url']].to_sql(
        'spot_prices', conn, if_exists='replace', index=False)
    derived = metrics.assign(month=metrics['month'].dt.strftime('%Y-%m-%d'))
    derived[['month', 'benchmark', 'monthly_return', 'annualised_volatility']].to_sql(
        'risk_metrics', conn, if_exists='replace', index=False)
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_prices ON spot_prices(month, benchmark)')
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_risk ON risk_metrics(month, benchmark)')
    conn.execute('DROP VIEW IF EXISTS monthly_market')
    conn.execute('''CREATE VIEW monthly_market AS
      SELECT month,
        MAX(CASE WHEN benchmark='Brent' THEN price_usd_bbl END) AS brent_usd_bbl,
        MAX(CASE WHEN benchmark='WTI' THEN price_usd_bbl END) AS wti_usd_bbl,
        ROUND(MAX(CASE WHEN benchmark='Brent' THEN price_usd_bbl END) -
              MAX(CASE WHEN benchmark='WTI' THEN price_usd_bbl END), 2) AS spread_usd_bbl
      FROM spot_prices GROUP BY month''')
    conn.commit()


def build_database(path: Path = DB_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        populate_database(conn)
    return path


def run_sql(filename: str, conn: sqlite3.Connection) -> pd.DataFrame:
    if not filename.endswith('.sql') or '/' in filename or '\\' in filename:
        raise ValueError('Choose one of the provided SQL scripts')
    path = ROOT / 'sql' / filename
    if not path.is_file():
        raise FileNotFoundError(filename)
    return pd.read_sql_query(path.read_text(encoding='utf-8'), conn)
