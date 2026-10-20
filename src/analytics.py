"""Load and analyse monthly Brent/WTI EIA price observations."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / 'data' / 'eia_monthly_spot_prices.csv'


def load_prices(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read supplied official historical monthly averages in long-table form."""
    df = pd.read_csv(path, parse_dates=['month'])
    required = {'month', 'benchmark', 'price_usd_bbl', 'source_url'}
    if not required.issubset(df.columns):
        raise ValueError(f'Missing CSV fields: {required - set(df.columns)}')
    if df.duplicated(['month', 'benchmark']).any():
        raise ValueError('Duplicate month/benchmark pairs in source CSV')
    if df['price_usd_bbl'].isna().any() or (df['price_usd_bbl'] <= 0).any():
        raise ValueError('This project snapshot expects non-missing positive prices')
    if set(df['benchmark']) != {'Brent', 'WTI'}:
        raise ValueError('Expected Brent and WTI benchmarks')
    df = df.sort_values(['benchmark', 'month']).reset_index(drop=True)
    expected = pd.date_range(df['month'].min(), df['month'].max(), freq='MS')
    for benchmark in ('Brent', 'WTI'):
        actual = pd.DatetimeIndex(df.loc[df['benchmark'].eq(benchmark), 'month'])
        if not actual.equals(expected):
            raise ValueError(f'Missing or unexpected months for {benchmark}')
    return df


def calculate_metrics(raw: pd.DataFrame, window: int = 6) -> pd.DataFrame:
    """Compute monthly returns and rolling annualised volatility (sqrt(12))."""
    if window < 2:
        raise ValueError('Rolling volatility window must be >= 2 months')
    prices = raw.sort_values(['benchmark', 'month']).copy()
    by_benchmark = prices.groupby('benchmark', sort=False)['price_usd_bbl']
    prices['monthly_return'] = by_benchmark.pct_change(fill_method=None)
    # Explicit grouping prevents accidentally mixing Brent and WTI returns.
    prices['annualised_volatility'] = (
        prices.groupby('benchmark', sort=False)['monthly_return']
        .transform(lambda x: x.rolling(window=window, min_periods=window).std(ddof=1) * np.sqrt(12))
    )
    return prices


def market_wide(metrics: pd.DataFrame) -> pd.DataFrame:
    """Pivot data to one row per month for cross-benchmark comparisons."""
    p = metrics.pivot(index='month', columns='benchmark', values='price_usd_bbl')
    result = p.rename(columns={'Brent': 'brent_usd_bbl', 'WTI': 'wti_usd_bbl'}).reset_index()
    result['spread_usd_bbl'] = result['brent_usd_bbl'] - result['wti_usd_bbl']
    return result


def risk_snapshot(metrics: pd.DataFrame, benchmark: str) -> dict:
    """Compute descriptive historical risk statistics for one benchmark."""
    d = metrics.loc[metrics['benchmark'].eq(benchmark)].sort_values('month')
    if d.empty:
        raise ValueError(f'Unknown benchmark: {benchmark}')
    last = d.iloc[-1]
    returns = d['monthly_return'].dropna()
    worst = returns.min() if not returns.empty else float('nan')
    return {
        'benchmark': benchmark,
        'month': last['month'],
        'latest_price': float(last['price_usd_bbl']),
        'latest_return': float(last['monthly_return']),
        'annualised_volatility': float(last['annualised_volatility']),
        'historical_5pct_return': float(returns.quantile(.05)),
        'worst_monthly_return': float(worst),
        'observation_count': len(d),
    }


def recent_trend(metrics: pd.DataFrame, benchmark: str, months: int = 3) -> float:
    """Return cumulative change over N monthly observation intervals."""
    d = metrics.loc[metrics['benchmark'].eq(benchmark)].sort_values('month')
    if len(d) <= months:
        return float('nan')
    return float(d['price_usd_bbl'].iloc[-1] / d['price_usd_bbl'].iloc[-months - 1] - 1)
