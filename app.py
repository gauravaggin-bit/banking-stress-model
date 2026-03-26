import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="EY | Capital Stress Model", layout="wide")

# Custom EY Branded Title
st.markdown("<h1 style='color: #FFE600;'>EY | Structural Bank Capital Stress Test</h1>", unsafe_allow_html=True)
st.markdown("""
**Methodology:** This model utilizes a CCAR-aligned Structural Capital Depletion framework. 
Unlike aggregate probability scores, this dashboard calculates explicit, auditable dollar-value losses across four macroeconomic risk pillars to determine the stressed Common Equity Tier 1 (CET1) ratio.
""")

# --- BASELINE BANK BALANCE SHEET (MNC / G-SIB Proxy) ---
STARTING_CET1_CAPITAL = 250.0  
RWA = 2000.0                   
BASELINE_CET1_RATIO = (STARTING_CET1_CAPITAL / RWA) * 100

BOND_PORTFOLIO_SIZE = 600.0    
PORTFOLIO_DURATION = 5.5       

LOAN_BOOK_SIZE = 1300.0        
BASE_PD = 0.020                
LGD = 0.40                     

# --- SIDEBAR: DYNAMIC MACRO SHOCKS ---
st.sidebar.markdown("<h2 style='color: #FFE600;'>Macroeconomic Shocks</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Adjust the severity of the geopolitical fallout:")

oil_shock = st.sidebar.slider("Brent Crude Peak ($/bbl)", min_value=70, max_value=250, value=120, step=5)
yield_shock = st.sidebar.slider("Treasury Yield Curve Shock (bps)", min_value=0, max_value=400, value=150, step=10)
funding_spread = st.sidebar.slider("Wholesale Funding Spread Widening (bps)", min_value=0, max_value=300, value=75, step=5)
contagion_loss = st.sidebar.slider("Direct Sovereign/Counterparty Write-offs ($B)", min_value=0.0, max_value=30.0, value=2.5, step=0.5)

# --- THE MATHEMATICAL ENGINE ---
yield_shock_decimal = yield_shock / 10000
market_loss = BOND_PORTFOLIO_SIZE * PORTFOLIO_DURATION * yield_shock_decimal

pd_multiplier = 1 + ((oil_shock - 70) / 100) + (yield_shock / 200)
stressed_pd = BASE_PD * pd_multiplier
credit_loss = LOAN_BOOK_SIZE * stressed_pd * LGD

funding_loss = (funding_spread / 10) * 0.5

total_depletion = market_loss + credit_loss + funding_loss + contagion_loss
stressed_capital = STARTING_CET1_CAPITAL - total_depletion
stressed_cet1_ratio = (stressed_capital / RWA) * 100

distance_to_default = stressed_cet1_ratio - 4.5
if distance_to_default <= 0:
    prob_collapse = 99.9
else:
    prob_collapse = max(0, 100 - (distance_to_default * 20)) 

# --- UI: TOP LEVEL METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Baseline CET1 Ratio", f"{BASELINE_CET1_RATIO:.1f}%")
col2.metric("Stressed CET1 Ratio", f"{stressed_cet1_ratio:.1f}%", f"{stressed_cet1_ratio - BASELINE_CET1_RATIO:.1f}%", delta_color="inverse")
col3.metric("Total Capital Destroyed", f"${total_depletion:.1f}B")
col4.metric("Prob. of Regulatory Breach", f"{prob_collapse:.1f}%", delta_color="inverse" if prob_collapse > 20 else "normal")

st.markdown("---")

# --- UI: WATERFALL CHART (EY Dark Theme) ---
st.subheader("Capital Depletion Waterfall")

fig = go.Figure(go.Waterfall(
    name = "Capital Stress", orientation = "v",
    measure = ["absolute", "relative", "relative", "relative", "relative", "total"],
    x = ["Starting Capital", "Market Risk", "Credit Risk", "Funding Costs", "Contagion", "Stressed Capital"],
    textposition = "outside",
    text = [f"${STARTING_CET1_CAPITAL}B", f"-${market_loss:.1f}B", f"-${credit_loss:.1f}B", f"-${funding_loss:.1f}B", f"-${contagion_loss:.1f}B", f"${stressed_capital:.1f}B"],
    y = [STARTING_CET1_CAPITAL, -market_loss, -credit_loss, -funding_loss, -contagion_loss, stressed_capital],
    connector = {"line":{"color":"#555555"}},
    decreasing = {"marker":{"color":"#FF4136"}}, # Warning Red for losses
    totals = {"marker":{"color":"#FFE600"}},     # EY Yellow for totals
    increasing = {"marker":{"color":"#FFE600"}}  # EY Yellow for starting capital
))

fig.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    title = "Bridge from Baseline to Stressed Tier 1 Capital (USD Billions)",
    showlegend = False,
    height = 500,
    margin=dict(l=20, r=20, t=50, b=20),
    font=dict(color="#FFFFFF")
)
st.plotly_chart(fig, use_container_width=True)

# --- UI: TRANSPARENCY & AUDIT TRAIL ---
st.markdown("---")
st.subheader("Model Audit Trail")

with st.expander("Click to view underlying mathematical formulas and component values"):
    st.markdown(f"""
    **1. Market Risk (Bond Portfolio)**
    * **Formula:** `Portfolio Size (${BOND_PORTFOLIO_SIZE}B) * Modified Duration ({PORTFOLIO_DURATION}) * Yield Shock ({yield_shock} bps)`
    * **Result:** **${market_loss:.1f}B** reduction in equity.
    
    **2. Credit Risk (Loan Book)**
    * **Formula:** `Loan Book (${LOAN_BOOK_SIZE}B) * Stressed PD ({stressed_pd*100:.2f}%) * LGD ({LGD*100:.0f}%)`
    * **Result:** **${credit_loss:.1f}B** in credit write-offs.
    
    **3. Funding & Liquidity**
    * **Formula:** `${0.5}B cost for every 10 bps of spread widening ({funding_spread} bps)`
    * **Result:** **${funding_loss:.1f}B** loss.
    
    **4. Stressed Capital Ratio**
    * **Formula:** `(Starting Capital (${STARTING_CET1_CAPITAL}B) - Total Losses (${total_depletion:.1f}B)) / RWA (${RWA}B)`
    """)
