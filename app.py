"""Streamlit dashboard: run `streamlit run app.py` from repository root."""
import io
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import load_prices, calculate_metrics, market_wide, risk_snapshot, recent_trend
from src.scenarios import evaluate_scenario, scenario_table
from src.recommendations import commercial_recommendations
from src.database import populate_database, run_sql

st.set_page_config(page_title='Energy Trading Intelligence', page_icon='🛢️', layout='wide')

@st.cache_data(show_spinner=False)
def get_data():
    raw = load_prices()
    metrics = calculate_metrics(raw)
    wide = market_wide(metrics)
    return metrics, wide


def dollars(value: float) -> str:
    return f'${value:,.0f}' if value >= 0 else f'-${abs(value):,.0f}'


def file_download(df: pd.DataFrame, name: str, label: str) -> None:
    st.download_button(label, df.to_csv(index=False).encode('utf-8'), file_name=name,
                       mime='text/csv', use_container_width=True)


metrics, wide = get_data()
last_month = wide['month'].max()
first_month = wide['month'].min()

st.title('🛢️ Energy Trading Intelligence & Risk')
st.caption('Brent & WTI | Official EIA monthly spot-price averages | Historical snapshot: '
           f'{first_month:%b %Y}–{last_month:%b %Y} | USD/barrel | No live feed')

st.sidebar.header('Market settings')
benchmark = st.sidebar.radio('Benchmark to analyse', ['Brent', 'WTI'])
date_range = st.sidebar.slider('Historical chart window', min_value=first_month.to_pydatetime(),
                               max_value=last_month.to_pydatetime(),
                               value=(max(first_month, last_month - pd.DateOffset(months=35)).to_pydatetime(),
                                      last_month.to_pydatetime()), format='MMM YYYY')
start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
filtered_wide = wide[(wide['month'] >= start) & (wide['month'] <= end)]
filtered_metrics = metrics[(metrics['month'] >= start) & (metrics['month'] <= end)]
bench_all = metrics[metrics['benchmark'].eq(benchmark)].sort_values('month')
bench_period = filtered_metrics[filtered_metrics['benchmark'].eq(benchmark)]
latest = risk_snapshot(metrics, benchmark)
selected_col = 'brent_usd_bbl' if benchmark == 'Brent' else 'wti_usd_bbl'

st.sidebar.divider()
st.sidebar.info('This is an educational commercial-risk model, not a real trading or hedging system. '
                'Spot monthly averages are not futures settlement prices.')

tab_market, tab_risk, tab_scenario, tab_sql, tab_method = st.tabs(
    ['Market monitor', 'Volatility & risk', 'Scenario lab', 'SQL explorer', 'Method & sources'])

with tab_market:
    latest_spread = float(wide.iloc[-1]['spread_usd_bbl'])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f'{benchmark} spot average', f"${latest['latest_price']:.2f}/bbl",
              f"{latest['latest_return']:+.1%} vs prior month")
    c2.metric('Latest Brent–WTI premium', f'${latest_spread:.2f}/bbl')
    c3.metric('Annualised 6-month vol', f"{latest['annualised_volatility']:.1%}")
    c4.metric('Snapshot through', last_month.strftime('%b %Y'))

    st.subheader('Oil benchmark prices')
    melted = filtered_wide.melt(id_vars='month', value_vars=['brent_usd_bbl','wti_usd_bbl'],
                               var_name='benchmark', value_name='USD per barrel')
    melted['benchmark'] = melted['benchmark'].map({'brent_usd_bbl':'Brent', 'wti_usd_bbl':'WTI'})
    fig = px.line(melted, x='month', y='USD per barrel', color='benchmark', markers=True,
                  color_discrete_map={'Brent':'#0F766E','WTI':'#F59E0B'},
                  labels={'month':'Month'}, template='plotly_white')
    fig.update_layout(legend_title_text='', height=420, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns([1.5,1])
    with left:
        st.subheader('Brent premium versus WTI')
        fig_spread = px.bar(filtered_wide, x='month', y='spread_usd_bbl',
                            labels={'month':'Month', 'spread_usd_bbl':'Brent − WTI ($/bbl)'},
                            color_discrete_sequence=['#0F766E'], template='plotly_white')
        fig_spread.add_hline(y=0, line_dash='dash', line_color='#666666')
        fig_spread.update_layout(height=320)
        st.plotly_chart(fig_spread, use_container_width=True)
    with right:
        st.subheader('Commercial watchlist')
        advice = commercial_recommendations(
            latest['annualised_volatility'], recent_trend(metrics, benchmark, 3),
            latest_spread, float(wide['spread_usd_bbl'].median()), 'Buyer')
        for note in advice[:3]:
            st.write('• ' + note)
        st.caption('Illustrative conditional rules, not automated trading recommendations.')

with tab_risk:
    st.subheader(f'{benchmark}: monthly volatility and downside history')
    vol, change, spreads = st.columns(3)
    vol.metric('Latest 6-month annualised volatility', f"{latest['annualised_volatility']:.2%}")
    change.metric('Worst monthly average-price change', f"{latest['worst_monthly_return']:.2%}")
    spreads.metric('Historical 5th-percentile monthly change', f"{latest['historical_5pct_return']:.2%}")

    a, b = st.columns(2)
    with a:
        risk_fig = px.line(bench_period, x='month', y='annualised_volatility',
                           labels={'month':'Month','annualised_volatility':'Annualised rolling volatility'},
                           color_discrete_sequence=['#0F766E'], template='plotly_white')
        risk_fig.update_yaxes(tickformat='.0%')
        risk_fig.update_layout(height=370, title='6-month rolling annualised volatility')
        st.plotly_chart(risk_fig, use_container_width=True)
    with b:
        returns_df = bench_period.dropna(subset=['monthly_return']).copy()
        returns_df['Monthly change (%)'] = returns_df['monthly_return'] * 100
        ret_fig = px.bar(returns_df, x='month', y='Monthly change (%)',
                         color='Monthly change (%)', color_continuous_scale='RdYlGn',
                         color_continuous_midpoint=0, template='plotly_white')
        ret_fig.update_layout(height=370, title='Changes in monthly average price', coloraxis_showscale=False)
        st.plotly_chart(ret_fig, use_container_width=True)

    st.markdown('**How to interpret risk:** Annualised volatility is sample standard deviation '
                'of six monthly price changes multiplied by √12. It describes historical '
                'variability, not the probability of a future loss. The historical 5th percentile '
                'is a descriptive tail observation, not a validated value-at-risk forecast.')

with tab_scenario:
    st.subheader('Commercial price-shock simulator')
    st.write('What happens to the value of a planned crude purchase or sale if prices change? '
             'The hedge percentage is a simplified fixed-price **illustration** only.')
    p1, p2 = st.columns(2)
    with p1:
        side = st.radio('Commercial position', ['Buyer', 'Seller'], horizontal=True,
                        help='Buyer pays for oil; Seller receives revenue from oil.')
        barrels = st.number_input('Exposed volume (barrels)', min_value=100, max_value=1_000_000,
                                  value=10_000, step=1_000)
    with p2:
        shock = st.slider('Hypothetical oil-price change (%)', -40, 40, 15, 5)
        hedge = st.slider('Illustrative fixed-price share (%)', 0, 100, 50, 10)
    result = evaluate_scenario(latest['latest_price'], int(barrels), shock / 100, hedge / 100, side)
    q1, q2, q3, q4 = st.columns(4)
    q1.metric('Current monthly price', f"${latest['latest_price']:.2f}/bbl")
    q2.metric('Shocked price', f"${latest['latest_price']*(1+shock/100):.2f}/bbl")
    q3.metric('Unhedged commercial impact', dollars(result.change_without_hedge))
    q4.metric('After fixed-price proxy', dollars(result.change_after_hedge))
    st.caption('Impacts are changes in commercial net cash flow: positive = favourable, '
               'negative = unfavourable. Baseline is unchanged; ignores premiums, margin, basis, '
               'slippage, taxes, timing and trading costs.')

    table = scenario_table(latest['latest_price'], int(barrels), hedge / 100, side)
    long = table.melt(id_vars='Price shock (%)',
                      value_vars=['Impact before hedge ($)', 'Impact after hedge ($)'],
                      var_name='Exposure', value_name='Cash-flow impact ($)')
    fig = px.bar(long, x='Price shock (%)', y='Cash-flow impact ($)', color='Exposure', barmode='group',
                  template='plotly_white', color_discrete_sequence=['#F59E0B','#0F766E'])
    fig.update_layout(height=380, legend_title_text='')
    st.plotly_chart(fig, use_container_width=True)
    file_download(table, 'commercial_scenarios.csv', 'Download scenario table (CSV)')
    st.markdown('**Practical review points**')
    for msg in commercial_recommendations(
            latest['annualised_volatility'], recent_trend(metrics, benchmark),
            float(wide.iloc[-1]['spread_usd_bbl']), float(wide['spread_usd_bbl'].median()), side):
        st.write('• ' + msg)

with tab_sql:
    st.subheader('Explore the SQLite questions')
    files = sorted(Path(__file__).resolve().parent.joinpath('sql').glob('*.sql'))
    options = [f.name for f in files]
    selected = st.selectbox('Pick a prepared business question', options)
    code = (Path(__file__).resolve().parent / 'sql' / selected).read_text()
    st.code(code, language='sql')
    with sqlite3.connect(':memory:') as conn:
        populate_database(conn)
        sql_result = run_sql(selected, conn)
    st.dataframe(sql_result, use_container_width=True, hide_index=True)
    file_download(sql_result, selected.replace('.sql', '.csv'), 'Download SQL result (CSV)')
    st.caption('A real SQLite in-memory database is created from the local EIA CSV on page load. '
               'Queries are predefined for safety and beginner readability.')

with tab_method:
    st.subheader('Data, assumptions & limitations')
    st.markdown('''
**Price source:** U.S. Energy Information Administration (EIA), monthly spot-price averages.
- [Europe Brent Spot Price FOB ($/barrel)](https://www.eia.gov/dnav/pet/hist/rbrtem.htm)
- [Cushing, OK WTI Spot Price FOB ($/barrel)](https://www.eia.gov/dnav/pet/hist/rwtcm.htm)

**As-of policy:** This repository includes an offline historical snapshot through **August 2026**,
transcribed from the EIA monthly tables on 20 October 2026. No live API connection or forecast is implied.

**Frequency:** One observation per month per benchmark. Prices are monthly **averages**,
not end-month closing prices or futures prices. Monthly returns compare consecutive *monthly averages*.
The first month has no prior return; the first six monthly changes are needed for a 6-month
rolling sample standard deviation. Annualisation uses the square root of 12.

**Exclusions:** Physical quality differentials, transport costs, FX, storage, delivery timing,
contract terms, transaction costs, futures curves, options Greeks and executable liquidity.
Historical dispersion can differ dramatically from future outcomes.

**Purpose:** Data engineering and commercial decision-support demonstration; not investment advice,
trading signals, or validated hedging/risk-management advice.
''')
    file_download(metrics.assign(month=metrics['month'].dt.strftime('%Y-%m-%d')),
                  'energy_metrics.csv', 'Download calculated metrics (CSV)')
    file_download(wide.assign(month=wide['month'].dt.strftime('%Y-%m-%d')),
                  'brent_wti_spread.csv', 'Download spread history (CSV)')
