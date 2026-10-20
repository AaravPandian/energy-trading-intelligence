"""Transparent, deterministic commercial cash-flow what-if analysis.

This is not a hedging backtest or risk model. Hedge percentage is a simple
fixed-price proxy, not a model of actual futures or derivatives settlements.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioResult:
    base_cashflow: float
    shocked_cashflow: float
    change_without_hedge: float
    change_after_hedge: float
    hedged_notional_at_base: float
    post_hedge_cashflow: float


def evaluate_scenario(price: float, barrels: int, shock_pct: float,
                      hedge_share: float, side: str) -> ScenarioResult:
    """Shock as decimal (+0.10 means +10%), hedge share in [0,1].

    Cash flow positive for seller revenue, negative for buyer cost.
    Changes reflect commercial benefit (+) or burden (-) under the shock.
    """
    if price <= 0 or barrels <= 0:
        raise ValueError('Price and barrels must be positive')
    if not (-0.95 <= shock_pct <= 3):
        raise ValueError('Shock outside the supported illustration range')
    if not (0 <= hedge_share <= 1):
        raise ValueError('Hedge share must be between 0 and 1')
    if side not in {'Buyer', 'Seller'}:
        raise ValueError('side must be Buyer or Seller')
    sign = -1 if side == 'Buyer' else 1
    base = sign * price * barrels
    shocked = sign * price * (1 + shock_pct) * barrels
    delta = shocked - base
    after = delta * (1 - hedge_share)
    return ScenarioResult(
        base_cashflow=base,
        shocked_cashflow=shocked,
        change_without_hedge=delta,
        change_after_hedge=after,
        hedged_notional_at_base=price * barrels * hedge_share,
        post_hedge_cashflow=base + after,
    )


def scenario_table(price: float, barrels: int, hedge_share: float, side: str):
    """Show symmetric what-if shocks around the snapshot price."""
    import pandas as pd
    rows = []
    for shock in [-.20, -.10, -.05, 0, .05, .10, .20]:
        r = evaluate_scenario(price, barrels, shock, hedge_share, side)
        rows.append({'Price shock (%)': int(shock * 100),
                     'Scenario price ($/bbl)': round(price * (1 + shock), 2),
                     'Impact before hedge ($)': round(r.change_without_hedge, 2),
                     'Impact after hedge ($)': round(r.change_after_hedge, 2)})
    return pd.DataFrame(rows)
