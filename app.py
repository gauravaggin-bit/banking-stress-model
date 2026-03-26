import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="EY | Kinetic Stress Model", layout="wide", initial_sidebar_state="expanded")

# Custom EY Branded Title
st.markdown("<h1 style='color: #FFE600;'>EY | Middle East Conflict X Banking Stress Model</h1>", unsafe_allow_html=True)
st.markdown("*A Structural Capital Depletion Framework for Global Systemically Important Banks (G-SIBs)*")
st.markdown("---")

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
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/EY_logo_2019.svg/512px-EY_logo_2019.svg.png", width=100)
st.sidebar.markdown("<h2 style='color: #FFE600;'>Geopolitical Scenario</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Define the parameters of the conflict. These variables apply globally across all tabs.")

severity = st.sidebar.slider("Conflict Severity (1 = Skirmish, 10 = Total Regional War)", min_value=1, max_value=10, value=5, step=1)
duration_months = st.sidebar.slider("Conflict Duration (Months)", min_value=1, max_value=36, value=12, step=1)

duration_years = duration_months / 12.0

# --- THE KINETIC-TO-MACRO TRANSLATION ENGINE ---
implied_oil = 75 + (severity * 10) * (1 + 0.4 * duration_years)
implied_yield_shock = (severity * 15) + (duration_years * 50)
implied_funding_spread = (severity * 10) + (duration_years * 15)
contagion_loss = (severity ** 1.4) * 0.6  

# --- THE FINANCIAL CAPITAL ENGINE ---
yield_shock_decimal = implied_yield_shock / 10000
market_loss = BOND_PORTFOLIO_SIZE * PORTFOLIO_DURATION * yield_shock_decimal

pd_multiplier = 1 + (((implied_oil - 75) / 100) + (implied_yield_shock / 200)) * (1 + duration_years)
stressed_pd = BASE_PD * pd_multiplier
credit_loss = LOAN_BOOK_SIZE * stressed_pd * LGD

funding_loss = (implied_funding_spread / 10) * 0.5

total_depletion = market_loss + credit_loss + funding_loss + contagion_loss
stressed_capital = STARTING_CET1_CAPITAL - total_depletion
stressed_cet1_ratio = (stressed_capital / RWA) * 100

distance_to_default = stressed_cet1_ratio - 4.5
prob_collapse = 99.9 if distance_to_default <= 0 else max(0, 100 - (distance_to_default * 20))

# --- CREATE TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dynamic Dashboard", 
    "🧮 Parameter Definitions", 
    "🏛️ Methodology", 
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
    col3.metric("Total Capital Destroyed", f"${total_depletion:.1f}B")
    col4.metric("Prob. of Regulatory Breach", f"{prob_collapse:.1f}%", delta_color="inverse" if prob_collapse > 20 else "normal")

    st.markdown("---")
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

# ==========================================
# TAB 2: PARAMETER DEFINITIONS
# ==========================================
with tab2:
    st.subheader("How Parameters Drive Capital Destruction")
    st.markdown("""
    This model utilizes a kinetic-to-financial translation matrix. The user defines the geopolitical reality, and the engine calculates the balance sheet impact.
    
    #### 1. The Geopolitical Inputs
    * **Severity (1-10):** Represents the kinetic intensity of the conflict. A higher severity creates immediate panic, drives initial crude oil spikes, and exponentially increases direct sovereign contagion (e.g., regional defaults).
    * **Duration (Months):** Acts as a non-linear amplifier. A 2-month shock is survivable for corporate borrowers. A 36-month shock permanently alters supply chains, anchors inflation, and forces central banks to hold rates "higher for longer."
    
    #### 2. The Financial Transmission Channels
    * **Market Risk (The Duration Trap):** Conflict drives inflation expectations, which spikes bond yields. Because banks hold massive portfolios of fixed-income assets (HTM/AFS), rising yields mathematically crush the value of these bonds. *Risk escalates with both Severity and Duration.*
    * **Credit Risk (Corporate/Retail Defaults):** High oil prices compress corporate profit margins. Simultaneously, higher interest rates make debt servicing extremely expensive. This combination multiplies the Probability of Default (PD) across the bank's $1.3 Trillion loan book. *Risk is heavily compounded by Duration.*
    * **Funding & Liquidity:** Geopolitical fear causes wholesale funding markets to freeze. Banks are forced to pay a higher premium (SOFR-OIS spread) to borrow from each other, compressing their Net Interest Margin (NIM).
    * **Contagion / Sovereign Risk:** Direct exposure to institutions or sovereign debt in the conflict zone. Modeled as a direct, unrecoverable capital write-off that scales exponentially with the Severity index.
    """)

# ==========================================
# TAB 3: METHODOLOGY
# ==========================================
with tab3:
    st.subheader("Structural Capital Depletion Framework")
    st.markdown("""
    This tool departs from arbitrary scoring models and aligns with the **Comprehensive Capital Analysis and Review (CCAR)** methodology used by the US Federal Reserve. 
    Every percentage point of risk generated by the model can be traced back to a specific dollar amount lost on the balance sheet.
    
    #### Core Mathematical Engine
    The probability of valuation collapse is structurally tied to how close the Stressed CET1 gets to the regulatory "Death Zone" (typically 4.5% + G-SIB surcharges).
    
    **1. Kinetic-to-Macro Translation**
    The engine converts the sliders into financial realities:
    * `Oil Price = Base + (Severity * 10) * (1 + 0.4 * Duration)`
    * `Yield Shock = (Severity * 15) + (Duration_Years * 50)`
    
    **2. Balance Sheet Depletion Math**
    * **Market Loss ($B)** = `Bond Portfolio Size * Modified Duration * (Yield Shock / 10000)`
    * **Stressed Probability of Default (PD)** = `Base PD * [1 + (Oil Shock Premium) + (Yield Shock Premium)] * (1 + Duration_Years)`
    * **Credit Loss ($B)** = `Loan Book Size * Stressed PD * Loss Given Default (LGD)`
    
    **3. The Capital Floor**
    * **Stressed CET1 %** = `[(Starting Capital - Total Depletion) / Risk-Weighted Assets] * 100`
    """)

# ==========================================
# TAB 4: CLIENT USE CASES
# ==========================================
with tab4:
    st.subheader("Banking Client Advisory: Strategic Questions")
    st.markdown("""
    This dynamic tool is designed to help bank executives, risk committees, and investment managers war-game severe geopolitical scenarios.
    
    **Test the model by adjusting the sidebar sliders to answer the following client questions:**
    
    > **Scenario A: The "Short & Sharp" Shock**
    > * **Question:** "If a severe regional war breaks out (Severity = 9) but is contained and resolved within 3 months, where is our primary vulnerability?"
    > * **How to model:** Set Severity to 9, Duration to 3.
    > * **Insight:** The dashboard will reveal that **Market Risk** (bond portfolio losses due to immediate rate spikes) is the primary threat, while Credit Risk remains relatively subdued because corporations can survive a 3-month margin squeeze.
    
    > **Scenario B: The Entrenched Proxy War**
    > * **Question:** "If a moderate conflict (Severity = 5) drags on for 3 years, disrupting global shipping and energy markets, will our CET1 capital buffer hold?"
    > * **How to model:** Set Severity to 5, Duration to 36.
    > * **Insight:** The dashboard will show a massive shift. The extended duration forces a prolonged "higher for longer" rate environment and entrenched inflation. You will see **Credit Risk** explode, wiping out tens of billions in capital as borrower defaults compound over time.
    
    > **Scenario C: Regulatory Breach**
    > * **Question:** "At what exact combination of conflict severity and duration does our bank breach the 4.5% regulatory minimum, triggering a potential receivership event?"
    > * **How to model:** Slide both metrics up until the "Prob. of Regulatory Breach" hits 99%. 
    > * **Insight:** Helps the risk committee define the absolute limits of their capital adequacy and informs hedging strategies.
    """)
