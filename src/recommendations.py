"""Rule-based operational commentary, not trade execution advice."""


def commercial_recommendations(volatility: float, three_month_change: float,
                               spread: float, median_spread: float, side: str) -> list[str]:
    messages = []
    if volatility >= .30:
        messages.append('Elevated historical monthly-price volatility: consider shorter quote validity, frequent budget refreshes and review of approved risk limits.')
    else:
        messages.append('Recent historical price variability is below the illustrative 30% threshold; continue routine exposure monitoring.')

    if side == 'Buyer':
        if three_month_change >= .10:
            messages.append('Benchmark prices have risen over three months: revisit purchasing budgets and discuss staged procurement or fixed-price terms with suppliers.')
        elif three_month_change <= -.10:
            messages.append('Benchmark prices have declined over three months: review opportunities to lock in planned procurement, subject to business needs.')
        else:
            messages.append('Three-month prices are relatively stable under a ±10% rule: compare supplier offers against the benchmark before agreeing terms.')
    else:
        if three_month_change <= -.10:
            messages.append('Recent lower prices may pressure sales receipts: revisit contract pricing and counterparty exposure.')
        else:
            messages.append('Review sales contract price-reset clauses and how realised receipts track the benchmark.')

    if spread > median_spread + 2:
        messages.append('Brent–WTI premium is above its historical sample median by over $2/bbl: review benchmark selection and regional basis exposure.')
    elif spread < median_spread - 2:
        messages.append('Brent–WTI premium is below its historical sample median by over $2/bbl: verify pricing benchmark suitability and basis assumptions.')
    else:
        messages.append('Brent–WTI spread is within $2/bbl of its historical sample median: maintain routine basis monitoring.')
    messages.append('Any actual hedge requires treasury approval, tradable forward quotes, counterparty and liquidity assessment; this dashboard does not recommend securities trades.')
    return messages
