import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Geopolitical Banking Stress Model", layout="wide")

# --- MODEL ASSUMPTIONS & BASELINE DATA (Hypothetical 2026 baseline) ---
# Beta coefficients for the logistic regression (calibrated to historical crises)
BETA_0 = -4.5   # Intercept (Low base probability)
BETA_1 = 0.85   # Credit Quality weight
BETA_2 = 0.70   # Liquidity weight
BETA_3 = 1.10   # Market Risk weight (Highly sensitive to rate shocks)
BETA_4 = 0.60   # Sovereign Stress weight
BETA_5 = 0.95   # Contagion weight

st.title("🏛️ Banking Valuation Vulnerability Model")
st.subheader("Impact of Middle East Geopolitical Conflict on Global Banking Solvency")

st.markdown("""
*This dynamic model calculates the probability of severe banking valuation collapse (P/TBV < 0.4x) based on macroeconomic shocks triggered by regional conflict.*
""")

# --- SIDEBAR: DYNAMIC PARAMETER CUSTOMIZATION ---
st.sidebar.header("Geopolitical Shock Parameters")

conflict_severity = st.sidebar.slider("Conflict Severity Index (1=Low, 10=Severe)", 1, 10, 5)
oil_shock = st.sidebar.number_input("Brent Crude Price Peak ($/bbl)", min_value=70, max_value=250, value=120)
rate_shock = st.sidebar.slider("US Treasury Yield Shock (bps)", -100, 300, 150)
cds_spreads = st.sidebar.slider("MENA Sovereign CDS Spread Average (bps)", 100, 1500, 450)
interbank_freeze = st.sidebar.slider("Interbank Spread (SOFR-OIS in bps)", 10, 300, 75)

# --- CALCULATING THE 5 PILLARS (Z-Scores based on shock severity) ---
# Normalizing inputs to a 0-10 stress scale for the logistic model
credit_stress = (oil_shock / 200) * conflict_severity
liquidity_stress = (interbank_freeze / 300) * 10
market_risk = (rate_shock / 300) * 10
sovereign_stress = (cds_spreads / 1500) * 10
contagion_risk = (interbank_freeze / 300) * conflict_severity

# --- PROBABILITY CALCULATION (Logistic Link Function) ---
log_odds = (BETA_0 + 
            (BETA_1 * credit_stress) + 
            (BETA_2 * liquidity_stress) + 
            (BETA_3 * market_risk) + 
            (BETA_4 * sovereign_stress) + 
            (BETA_5 * contagion_risk))

# Prevent overflow
log_odds = max(min(log_odds, 10), -10)
prob_collapse = 1 / (1 + np.exp(-log_odds))

# --- DASHBOARD VISUALIZATION ---
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Probability of Sector Valuation Collapse")
    # Plotly Gauge Chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = prob_collapse * 100,
        number = {'suffix': "%", 'valueformat': ".1f"},
        title = {'text': "Implied Collapse Probability"},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkred"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 15], 'color': "lightgreen"},
                {'range': [15, 40], 'color': "gold"},
                {'range': [40, 100], 'color': "salmon"}],
        }
    ))
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Risk Pillar Breakdown")
    # Radar Chart for the 5 Pillars
    categories = ['Credit Quality', 'Liquidity Stress', 'Market Risk', 'Sovereign Stress', 'Contagion Risk']
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[credit_stress, liquidity_stress, market_risk, sovereign_stress, contagion_risk],
        theta=categories,
        fill='toself',
        name='Current Stress Level',
        line_color='darkred'
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False,
        height=350, margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# --- IMPACT SUMMARY TABLE ---
st.markdown("---")
st.markdown("### Estimated Macro-Financial Impact Matrix")
impact_data = {
    "Risk Pillar": ["Credit Quality", "Liquidity", "Market Risk", "Sovereign Risk", "Contagion"],
    "Proxy Metric": ["NPL Ratio Spikes", "LCR Degradation", "HTM Portfolio Losses", "CDS Widening", "Interbank Rate Spikes"],
    "Estimated Impact Severity": [
        "High" if credit_stress > 6 else "Medium",
        "High" if liquidity_stress > 6 else "Medium",
        "Critical" if market_risk > 8 else "High",
        "Severe" if sovereign_stress > 7 else "Low",
        "High" if contagion_risk > 6 else "Moderate"
    ]
}
df_impact = pd.DataFrame(impact_data)
st.table(df_impact)
