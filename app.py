import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Structural Capital Stress Test", layout="wide")

st.title("🏦 Structural Bank Capital Stress Test Model")
st.markdown("""
**Methodology:** This model utilizes a CCAR-aligned Structural Capital Depletion framework. 
Unlike aggregate probability scores, this dashboard calculates explicit, auditable dollar-value losses across four macroeconomic risk pillars to determine the stressed Common Equity Tier 1 (CET1) ratio.
""")

# --- BASELINE BANK BALANCE SHEET (MNC / G-SIB Proxy) ---
STARTING_CET1_CAPITAL = 250.0  # $ Billions (Scaled up to top-tier MNC)
RWA = 2000.0                   # Risk-Weighted Assets in $ Billions
BASELINE_CET1_RATIO = (STARTING_CET1_CAPITAL / RWA) * 100

BOND_PORTFOLIO_SIZE = 600.0    # $ Billions (AFS + HTM)
PORTFOLIO_DURATION = 5.5       # Modified Duration

LOAN_BOOK_SIZE = 1300.0        # $ Billions
BASE_PD = 0.020                # Base Probability of Default (2.0%)
LGD = 0.40                     # Loss Given Default (40%)

# --- SIDEBAR: DYNAMIC MACRO SHOCKS ---
st.sidebar.header("Macroeconomic Shocks")
st.sidebar.markdown("Adjust the severity of the geopolitical fallout:")

oil_shock = st.sidebar.slider("Brent Crude Peak ($/bbl)", min_value=70, max_value=250, value=120, step=5)
yield_shock = st.sidebar.slider("Treasury Yield Curve Shock (bps)", min_value=0, max_value=400, value=150, step=10)
funding_spread = st.sidebar.slider("Wholesale Funding Spread Widening (bps)", min_value=0, max_value=300, value=75, step=5)
contagion_loss = st.sidebar.slider("Direct Sovereign/Counterparty Write-offs ($B)", min_value=0.0, max_value=30.0, value=2.5, step=0.5)

# --- THE MATHEMATICAL ENGINE (Auditable Calculations) ---

# 1. Market Risk Loss (Duration Math)
# Formula: Value * Duration * (Yield Shock in decimal)
yield_shock_decimal = yield_shock / 10000
market_loss = BOND_PORTFOLIO_SIZE * PORTFOLIO_DURATION * yield_shock_decimal

# 2. Credit Risk Loss (Expected Loss Math)
# Stressed PD scales with oil prices (inflation/margin crush) and rate shocks (debt servicing costs)
pd_multiplier = 1 + ((oil_shock - 70) / 100) + (yield_shock / 200)
stressed_pd = BASE_PD * pd_multiplier
credit_loss = LOAN_BOOK_SIZE * stressed_pd * LGD

# 3. Funding & Liquidity Cost
# Simplified sensitivity: Every 10 bps of spread widening costs $0.5B in Net Interest Income
funding_loss = (funding_spread / 10) * 0.5

# 4. Total Capital Depletion
total_depletion = market_loss + credit_loss + funding_loss + contagion_loss
stressed_capital = STARTING_CET1_CAPITAL - total_depletion
stressed_cet1_ratio = (stressed_capital / RWA) * 100

# Probability of Breach (Logistic decay mapping CET1 proximity to the 4.5% regulatory minimum)
# If CET1 falls to 4.5%, probability approaches 99%. If it stays above 9%, probability is negligible.
distance_to_default = stressed_cet1_ratio - 4.5
if distance_to_default <= 0:
    prob_collapse = 99.9
else:
    prob_collapse = max(0, 100 - (distance_to_default * 20)) # Linear scaling for simplicity in UI

# --- UI: TOP LEVEL METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Baseline CET1 Ratio", f"{BASELINE_CET1_RATIO:.1f}%")
col2.metric("Stressed CET1 Ratio", f"{stressed_cet1_ratio:.1f}%", f"{stressed_cet1_ratio - BASELINE_CET1_RATIO:.1f}%", delta_color="inverse")
col3.metric("Total Capital Destroyed", f"${total_depletion:.1f}B")
col4.metric("Prob. of Regulatory Breach", f"{prob_collapse:.1f}%", delta_color="inverse" if prob_collapse > 20 else "normal")

st.markdown("---")

# --- UI: WATERFALL CHART (Visualizing the Depletion) ---
st.subheader("Capital Depletion Waterfall")

fig = go.Figure(go.Waterfall(
    name = "Capital Stress", orientation = "v",
    measure = ["absolute", "relative", "relative", "relative", "relative", "total"],
    x = ["Starting Capital", "Market Risk (Bonds)", "Credit Risk (Loans)", "Funding Costs", "Contagion", "Stressed Capital"],
    textposition = "outside",
    text = [f"${STARTING_CET1_CAPITAL}B", f"-${market_loss:.1f}B", f"-${credit_loss:.1f}B", f"-${funding_loss:.1f}B", f"-${contagion_loss:.1f}B", f"${stressed_capital:.1f}B"],
    y = [STARTING_CET1_CAPITAL, -market_loss, -credit_loss, -funding_loss, -contagion_loss, stressed_capital],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    decreasing = {"marker":{"color":"#ef553b"}},
    totals = {"marker":{"color":"#00cc96"}}
))

fig.update_layout(
    title = "Bridge from Baseline to Stressed Tier 1 Capital (USD Billions)",
    showlegend = False,
    height = 500,
    margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# --- UI: TRANSPARENCY & AUDIT TRAIL ---
st.markdown("---")
st.subheader("Model Audit Trail: How the numbers are calculated")

with st.expander("Click to view underlying mathematical formulas and component values"):
    st.markdown(f"""
    **1. Market Risk (Bond Portfolio)**
    * **Logic:** Calculates mark-to-market losses on fixed-income securities due to rate hikes.
    * **Formula:** `Portfolio Size ($500B) * Modified Duration (5.5) * Yield Shock ({yield_shock} bps)`
    * **Result:** **${market_loss:.1f}B** reduction in equity.
    
    **2. Credit Risk (Loan Book)**
    * **Logic:** Calculates Expected Loss (EL) expansion as borrower margins compress from oil prices and rate hikes.
    * **Formula:** `Loan Book ($1000B) * Stressed PD ({stressed_pd*100:.2f}%) * LGD (40%)`
    * *(Note: Base PD is 2.0%. The shock multiplier is currently {pd_multiplier:.2f}x)*
    * **Result:** **${credit_loss:.1f}B** in credit write-offs.
    
    **3. Funding & Liquidity**
    * **Logic:** Estimates Net Interest Margin compression from interbank borrowing spreads.
    * **Formula:** `${0.5}B cost for every 10 bps of spread widening ({funding_spread} bps)`
    * **Result:** **${funding_loss:.1f}B** loss.
    
    **4. Stressed Capital Ratio**
    * **Formula:** `(Starting Capital (${STARTING_CET1_CAPITAL}B) - Total Losses (${total_depletion:.1f}B)) / RWA (${RWA}B)`
    """)
