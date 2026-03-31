import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="EY | Global Kinetic Stress Model", layout="wide", initial_sidebar_state="expanded")

# Custom EY Branded Title
st.markdown("<h1 style='color: #FFE600;'>EY | Basel III Kinetic-to-Financial Stress Model</h1>", unsafe_allow_html=True)
st.markdown("*Global Systemically Important Bank (G-SIB) Structural Stress Framework*")
st.markdown("---")

# --- SIDEBAR: GEOPOLITICAL & CAPITAL INPUTS ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/EY_logo_2019.svg/512px-EY_logo_2019.svg.png", width=100)
st.sidebar.markdown("<h2 style='color: #FFE600;'>Model Parameters</h2>", unsafe_allow_html=True)

# NEW: Starting Capital Slider
starting_capital = st.sidebar.slider("Starting CET1 Capital ($B)", min_value=10, max_value=500, value=250, step=10)

# Geopolitical Inputs
st.sidebar.markdown("---")
severity = st.sidebar.slider("Conflict Severity (1-10)", min_value=1, max_value=10, value=5, step=1)
duration_months = st.sidebar.slider("Conflict Duration (Months)", min_value=1, max_value=36, value=12, step=1)
duration_years = duration_months / 12.0

# --- BASELINE BANK BALANCE SHEET (Scaled to Capital) ---
# We maintain a realistic 12.5% Starting CET1 Ratio by scaling RWA to the selected Capital
RWA = starting_capital / 0.125                   
BASELINE_CET1_RATIO = 12.5

# Proportional Assets
BOND_PORTFOLIO_SIZE = starting_capital * 2.4   
PORTFOLIO_DURATION = 5.5       
LOAN_BOOK_SIZE = starting_capital * 5.2        
BASE_PD = 0.020                
LGD = 0.40                     

# --- THE KINETIC-TO-MACRO TRANSLATION ENGINE ---
implied_oil = 75 + (severity * 10) * (1 + 0.4 * duration_years)
implied_yield_shock = (severity * 15) + (duration_years * 50)
implied_funding_spread = (severity * 10) + (duration_years * 15)
contagion_loss = (severity ** 1.4) * (starting_capital / 100) # Scaled to bank size

# --- THE FINANCIAL CAPITAL ENGINE ---
yield_shock_decimal = implied_yield_shock / 10000
market_loss = BOND_PORTFOLIO_SIZE * PORTFOLIO_DURATION * yield_shock_decimal

pd_multiplier = 1 + (((implied_oil - 75) / 100) + (implied_yield_shock / 200)) * (1 + duration_years)
stressed_pd = BASE_PD * pd_multiplier
credit_loss = LOAN_BOOK_SIZE * stressed_pd * LGD

funding_loss = (implied_funding_spread / 10) * (starting_capital / 500)

total_depletion = market_loss + credit_loss + funding_loss + contagion_loss
stressed_capital = starting_capital - total_depletion
stressed_cet1_ratio = (stressed_capital / RWA) * 100

# BASEEL III BUFFER LOGIC
# Min CET1 (4.5%) + CCB (2.5%) + Avg G-SIB Surcharge (2.0%) = 9.0% Total Requirement
required_cet1 = 9.0
buffer_headroom = stressed_cet1_ratio - required_cet1
prob_breach = 99.9 if buffer_headroom <= 0 else max(0, 100 - (buffer_headroom * 25))

# --- CREATE TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dynamic Dashboard", 
    "🧮 Parameter Definitions", 
    "🏛️ Methodology (Basel III)", 
    "💡 Client Use Cases"
])

# ==========================================
# TAB 1: DYNAMIC DASHBOARD
# ==========================================
with tab1:
    st.markdown("<h3 style='color: #AAAAAA;'>Implied Macroeconomic Reality</h3>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Implied Brent Crude Peak", f"${implied_oil:.0f} / bbl")
    sc2.metric("Implied Yield Curve Shock", f"+{implied_yield_shock:.0f} bps")
    sc3.metric("Implied Funding Spread", f"+{implied_funding_spread:.0f} bps")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Baseline CET1 Ratio", f"{BASELINE_CET1_RATIO:.1f}%")
    col2.metric("Stressed CET1 Ratio", f"{stressed_cet1_ratio:.1f}%", f"{stressed_cet1_ratio - BASELINE_CET1_RATIO:.1f}%", delta_color="inverse")
    col3.metric("Capital Depleted", f"${total_depletion:.1f}B")
    col4.metric("Basel III Buffer Breach Prob.", f"{prob_breach:.1f}%", delta_color="inverse" if prob_breach > 20 else "normal")

    st.markdown("---")
    st.subheader("Basel III Capital Depletion Waterfall")

    fig = go.Figure(go.Waterfall(
        name = "Capital Stress", orientation = "v",
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"],
        x = ["Starting Capital", "Market Risk", "Credit Risk", "Funding Costs", "Contagion", "Stressed Capital"],
        textposition = "outside",
        text = [f"${starting_capital}B", f"-${market_loss:.1f}B", f"-${credit_loss:.1f}B", f"-${funding_loss:.1f}B", f"-${contagion_loss:.1f}B", f"${stressed_capital:.1f}B"],
        y = [starting_capital, -market_loss, -credit_loss, -funding_loss, -contagion_loss, stressed_capital],
        connector = {"line":{"color":"#555555"}},
        decreasing = {"marker":{"color":"#FF4136"}}, 
        totals = {"marker":{"color":"#FFE600"}},     
        increasing = {"marker":{"color":"#FFE600"}}  
    ))

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title = f"G-SIB Capital Bridge: ${starting_capital}B Starting Base",
        showlegend = False,
        height = 500,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#FFFFFF")
    )
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: PARAMETER DEFINITIONS
# ==========================================
with tab2:
    st.subheader("Defining the Stress Vectors")
    st.markdown(f"""
    Gaurav, this model uses your defined conflict parameters to drive capital erosion through the following mechanisms:
    
    #### 1. The Geopolitical Inputs
    * **Severity (1-10):** Represents kinetic intensity. This directly influences the magnitude of the oil shock and the 'contagion' haircut applied to regional interbank exposures.
    * **Duration (Months):** Represents the timeline of the conflict. In the Basel framework, duration is a critical multiplier for credit risk, as corporations can hedge short shocks but fail during protracted crises.
    
    #### 2. The Financial Transmission Channels
    * **Market Risk:** Reflects the mark-to-market loss on the bank's **${BOND_PORTFOLIO_SIZE:.0f}B** fixed-income portfolio.
    * **Credit Risk:** Reflects Expected Loss (EL) on the **${LOAN_BOOK_SIZE:.0f}B** loan book. Stressed Probability of Default (PD) is currently **{stressed_pd*100:.2f}%**.
    * **Contagion:** Reflects the immediate write-off of assets tied to the conflict zone.
    """)

# ==========================================
# TAB 3: METHODOLOGY (Basel III)
# ==========================================
with tab3:
    st.subheader("Basel III vs. CCAR: Why we use the Global Standard")
    st.markdown("""
    While the Federal Reserve's CCAR is robust for US banks, the **Basel III framework (BIS)** is the global gold standard for MNC banking valuations. 
    
    #### The Basel III Capital Stack
    Under Basel III, a bank’s valuation is most sensitive to the **Total CET1 Requirement**, which consists of:
    1.  **Minimum Tier 1 Capital:** 4.5% (Non-negotiable floor).
    2.  **Capital Conservation Buffer (CCB):** 2.5% (Designed to absorb losses during stress).
    3.  **G-SIB Surcharge:** ~2.0% (Extra capital required for systemic global banks).
    
    **Total Global Safety Target: 9.0% CET1 Ratio.**
    
    #### Calculation Logic
    * **RWA Scaling:** The model automatically scales Risk-Weighted Assets to the starting capital base to maintain a 12.5% baseline ratio, mirroring a healthy G-SIB.
    * **Erosion:** Losses are subtracted from the capital numerator. When the ratio drops below 9.0%, the bank enters the 'Buffer Breach' zone, where dividend payments and executive bonuses are legally restricted, often leading to a collapse in equity valuation.
    """)

# ==========================================
# TAB 4: CLIENT USE CASES
# ==========================================
with tab4:
    st.subheader("Client Advisory Questions")
    st.markdown("""
    Use these prompts to guide a client session using the dashboard:
    
    > **"If we reduce our starting capital base through a share buyback program, how does our resilience to a 12-month Middle East conflict change?"**
    > * **Action:** Reduce the 'Starting Capital' slider and compare the 'Breach Prob.' to the previous level.
    
    > **"Does a high-intensity 3-month skirmish threaten our Basel III buffers more than a low-intensity 3-year proxy war?"**
    > * **Action:** Compare (Severity 9, Duration 3) vs. (Severity 4, Duration 36).
    
    > **"At what oil price peak does our loan book credit loss exceed our bond portfolio market loss?"**
    > * **Action:** Increase severity and observe the waterfall chart until the 'Credit Risk' bar becomes larger than 'Market Risk'.
    """)
