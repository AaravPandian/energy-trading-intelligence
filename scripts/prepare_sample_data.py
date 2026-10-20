"""Write the frozen EIA monthly Brent/WTI price snapshot supplied with the project.

These numbers were transcribed from EIA's published monthly spot-price history
on 2026-10-20, with the latest complete month in this snapshot August 2026.
This file is a reproducible reference table, NOT simulated prices.
"""
from pathlib import Path
import csv

MONTHLY = {
    2021: {
        'brent': [54.77,62.28,65.41,64.81,68.53,73.16,75.17,70.75,74.49,83.54,81.05,74.17],
        'wti':   [52.00,59.04,62.33,61.72,65.17,71.38,72.49,67.73,71.65,81.48,79.15,71.71],
    },
    2022: {
        'brent': [86.51,97.13,117.25,104.58,113.34,122.71,111.93,100.45,89.76,93.33,91.42,80.92],
        'wti':   [83.22,91.64,108.50,101.78,109.55,114.84,101.62,93.67,84.26,87.55,84.37,76.44],
    },
    2023: {
        'brent': [82.50,82.59,78.43,84.64,75.47,74.84,80.11,86.15,93.72,90.60,82.94,77.63],
        'wti':   [78.12,76.83,73.28,79.45,71.58,70.25,76.07,81.39,89.43,85.64,77.69,71.90],
    },
    2024: {
        'brent': [80.12,83.48,85.41,89.94,81.75,82.25,85.15,80.36,74.02,75.63,74.35,73.86],
        'wti':   [74.15,77.25,81.28,85.35,80.02,79.77,81.80,76.68,70.24,71.99,69.95,70.12],
    },
    2025: {
        'brent': [79.27,75.44,72.73,68.13,64.45,71.44,71.04,67.87,67.99,64.54,63.80,62.54],
        'wti':   [75.74,71.53,68.24,63.54,62.17,68.17,68.39,64.86,63.96,60.89,60.06,57.97],
    },
    2026: {
        'brent': [66.60,70.89,103.13,117.29,107.14,85.40,83.76,91.08],
        'wti':   [60.04,64.51,91.38,100.32,102.13,84.81,80.46,83.90],
    }
}

SOURCES = {
    'Brent': 'https://www.eia.gov/dnav/pet/hist/rbrtem.htm',
    'WTI': 'https://www.eia.gov/dnav/pet/hist/rwtcm.htm',
}

def write_snapshot(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['month', 'benchmark', 'price_usd_bbl', 'source_url'])
        for year, payload in sorted(MONTHLY.items()):
            assert len(payload['brent']) == len(payload['wti'])
            for index in range(len(payload['brent'])):
                month = f'{year}-{index+1:02d}-01'
                for bench, key in [('Brent', 'brent'), ('WTI', 'wti')]:
                    writer.writerow([month, bench, f'{payload[key][index]:.2f}', SOURCES[bench]])
    return sum(len(v['brent']) * 2 for v in MONTHLY.values())

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'data' / 'eia_monthly_spot_prices.csv'
    print(f'Wrote {write_snapshot(target)} records to {target}')
