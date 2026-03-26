import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="EY | Kinetic Stress Model", layout="wide")

# Custom EY Branded Title
st.markdown("<h1 style='color: #FFE600;'>EY | Geopolitical Kinetic-to-Financial Stress Model</h1>", unsafe_allow_html=True)
st.markdown("""
**Methodology:** This engine translates geopolitical conflict parameters (Severity and Duration) into correlated macroeconomic shocks. 
It then applies those shocks to a G-SIB balance sheet using a Structural Capital Depletion framework to calculate the Stressed CET1 ratio.
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

# --- SIDEBAR: GEOPOLITICAL INPUTS ---
st.sidebar.markdown("<h2 style='color: #FFE600;'>Geopolitical Scenario</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Define the parameters of the Middle East conflict:")

severity = st.sidebar.slider("Conflict Severity (1 = Skirmish, 10 = Total Regional War)", min_value=1, max_value=10, value=5, step=1)
duration_months = st.sidebar.slider("Conflict Duration (Months)", min_value=1, max_value=36, value=12, step=1)

duration_years = duration_months / 12.0

# --- THE KINETIC-TO-MACRO TRANSLATION ENGINE ---
# These formulas dictate how war parameters create financial realities
implied_oil = 75 + (severity * 10) * (1 + 0.4 * duration_years)
implied_yield_shock = (severity * 15) + (duration_years * 50)
implied_funding_spread = (severity * 10) + (duration_years * 15)
contagion_loss = (severity ** 1.4) * 0.6  # Exponential scaling for severity

# --- THE FINANCIAL CAPITAL ENGINE ---
# 1. Market Risk
yield_shock_decimal = implied_yield_shock / 10000
market_loss = BOND_PORTFOLIO_SIZE * PORTFOLIO_DURATION * yield_shock_decimal

# 2. Credit Risk (Duration heavily compounds defaults)
pd_multiplier = 1 + (((implied_oil - 75) / 100) + (implied_yield_shock / 200)) * (1 + duration_years)
stressed_pd = BASE_PD * pd_multiplier
credit_loss = LOAN_BOOK_SIZE * stressed_pd * LGD

# 3. Funding Loss
funding_loss = (implied_funding_spread / 10) * 0.5

# 4. Total Depletion
total_depletion = market_loss + credit_loss + funding_loss + contagion_loss
stressed_capital = STARTING_CET1_CAPITAL - total_depletion
stressed_cet1_ratio = (stressed_capital / RWA) * 100

distance_to_default = stressed_cet1_ratio - 4.5
prob_collapse = 99.9 if distance_to_default <= 0 else max(0, 100 - (distance_to_default * 20))

# --- UI: IMPLIED MACRO SCENARIO ---
st.markdown("<h3 style='color: #AAAAAA;'>Implied Macroeconomic Reality</h3>", unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns(3)
sc1.metric("Implied Brent Crude Peak", f"${implied_oil:.0f} / bbl")
sc2.metric("Implied Yield Curve Shock", f"+{implied_yield_shock:.0f} bps")
sc3.metric("Implied Funding Spread", f"+{implied_funding_spread:.0f} bps")

st.markdown("---")

# --- UI: TOP LEVEL CAPITAL METRICS ---
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
    decreasing = {"marker":{"color":"#FF4136"}}, 
    totals = {"marker":{"color":"#FFE600"}},     
    increasing = {"marker":{"color":"#FFE600"}}  
))

fig.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    title = f"Capital Bridge: Severity {severity} | Duration {duration_months} Months",
    showlegend = False,
    height = 500,
    margin=dict(l=20, r=20, t=50, b=20),
    font=dict(color="#FFFFFF")
)
st.plotly_chart(fig, use_container_width=True)

# --- UI: TRANSPARENCY & AUDIT TRAIL ---
st.markdown("---")
with st.expander("Model Audit Trail: Kinetic & Mathematical Translations"):
    st.markdown(f"""
    **Kinetic-to-Macro Equations:**
    * **Oil:** `75 + (Severity * 10) * (1 + 0.4 * Duration_Years)`
    * **Yield:** `(Severity * 15) + (Duration_Years * 50)`
    
    **Financial Depletion:**
    * **Market Risk:** `Portfolio (${BOND_PORTFOLIO_SIZE}B) * Duration ({PORTFOLIO_DURATION}) * Yield Shock` = **${market_loss:.1f}B**
    * **Credit Risk:** Duration heavily compounds defaults. `Loan Book (${LOAN_BOOK_SIZE}B) * Stressed PD ({stressed_pd*100:.2f}%) * LGD ({LGD*100:.0f}%)` = **${credit_loss:.1f}B**
    """)
