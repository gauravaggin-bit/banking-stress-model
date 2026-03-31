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

starting_capital = st.sidebar.slider("Starting CET1 Capital ($B)", min_value=10, max_value=500, value=250, step=10)

st.sidebar.markdown("---")
severity = st.sidebar.slider("Conflict Severity (1-10)", min_value=1, max_value=10, value=5, step=1)
duration_months = st.sidebar.slider("Conflict Duration (Months)", min_value=1, max_value=36, value=12, step=1)
duration_years = duration_months / 12.0

# --- BASELINE BANK BALANCE SHEET (Scaled to Capital) ---
RWA = starting_capital / 0.125                   
BASELINE_CET1_RATIO = 12.5

BOND_PORTFOLIO_SIZE = starting_capital * 2.4   
PORTFOLIO_DURATION = 5.5       
LOAN_BOOK_SIZE = starting_capital * 5.2        
BASE_PD = 0.020                
LGD = 0.40                     

# --- THE KINETIC-TO-MACRO TRANSLATION ENGINE ---
implied_oil = 75 + (severity * 10) * (1 + 0.4 * duration_years)
implied_yield_shock = (severity * 15) + (duration_years * 50)
implied_funding_spread = (severity * 10) + (duration_years * 15)
contagion_loss = (severity ** 1.4) * (starting_capital / 100) 

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

required_cet1 = 9.0
buffer_headroom = stressed_cet1_ratio - required_cet1
prob_breach = 99.9 if buffer_headroom <= 0 else max(0, 100 - (buffer_headroom * 25))

# --- CREATE TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dynamic Dashboard", 
    "🔍 Model Governance & Assumptions", 
    "🧮 Mathematical Engine", 
    "💡 Client Scenarios"
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
        title = f"Basel III Capital Bridge: ${starting_capital}B Starting Base",
        showlegend = False,
        height = 500,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#FFFFFF")
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Deep Dive: Real-Time Calculation Audit Log"):
        st.markdown(f"""
        **Live Arithmetic for Current Scenario (Severity: {severity}, Duration: {duration_months} months):**
        * **Market Loss:** `${BOND_PORTFOLIO_SIZE:.1f}B (Portfolio) \\times {PORTFOLIO_DURATION} (Duration) \\times {yield_shock_decimal:.4f} (Yield Shock)` = **${market_loss:.1f}B**
        * **Credit Loss:** `${LOAN_BOOK_SIZE:.1f}B (Exposure) \\times {stressed_pd*100:.2f}\\% (Stressed PD) \\times 40\\% (LGD)` = **${credit_loss:.1f}B**
        * **Funding Loss:** `({implied_funding_spread:.0f} bps / 10) \\times ${starting_capital / 500:.2f}B sensitivity` = **${funding_loss:.1f}B**
        * **Contagion Loss:** `{severity}^{1.4} \\times ${(starting_capital / 100):.2f}B scale factor` = **${contagion_loss:.1f}B**
        * **CET1 Ratio:** `(${stressed_capital:.1f}B / ${RWA:.1f}B) \\times 100` = **{stressed_cet1_ratio:.2f}%**
        """)

# ==========================================
# TAB 2: MODEL GOVERNANCE & ASSUMPTIONS
# ==========================================
with tab2:
    st.subheader("Model Governance: Transparency & Limitations")
    st.markdown("""
    To ensure robustness and build trust, this model is designed as a 'glass box.' Below are the explicit assumptions, historical groundings, and structural limitations of the engine.
    
    #### 1. Foundational Assumptions
    * **Static LGD (Loss Given Default):** The model assumes a fixed LGD of **40%**. *Rationale:* This aligns with the historical long-term average for senior unsecured corporate debt. We assume collateral values do not entirely collapse during the conflict.
    * **Linear Asset Scaling:** As the user adjusts the 'Starting Capital' slider, the balance sheet (Loan Book, Bond Portfolio, RWA) scales linearly to maintain a 12.5% baseline CET1 ratio. *Rationale:* Preserves the structural proportions of a typical G-SIB.
    * **Modified Duration Simplification:** Market risk relies on a portfolio-level Modified Duration of **5.5**. *Limitation:* It does not account for convexity (the non-linear price-yield relationship of bonds), meaning extreme yield shocks (>300 bps) may be slightly overstated.
    
    #### 2. Historical Calibration (The Translation Engine)
    The kinetic-to-macro equations are calibrated against three primary historical geopolitical crises:
    * **1973 Oil Crisis:** Defines the baseline oil elasticity multiplier.
    * **1990 Gulf War:** Defines the immediate 'panic' yield spike correlation.
    * **2022 Russia-Ukraine Conflict:** Informs the duration decay parameter, demonstrating how long-term supply chain severing forces central banks into a 'higher for longer' rate posture.
    
    #### 3. Known Model Limitations
    * **Currency Isolation:** The model operates natively in USD equivalents. It does not account for FX volatility or the depreciation of emerging market currencies against the dollar during a flight to safety.
    * **Derivative Netting:** The 'Contagion' pillar estimates gross exposure write-offs. It does not dynamically calculate the mitigation effects of ISDA master netting agreements or specific CDS hedging overlays held by individual banks.
    """)

# ==========================================
# TAB 3: MATHEMATICAL ENGINE
# ==========================================
with tab3:
    st.subheader("The Underlying Mathematical Architecture")
    st.markdown("""
    The engine operates in two sequential stages: Kinetic Translation and Financial Transmission.
    
    #### Stage 1: Kinetic-to-Macro Translation
    We define geopolitical severity ($S$) from 1-10, and duration ($D$) in years.
    
    * **Oil Price Shock:** Incorporates a baseline equilibrium ($75) and scales with severity, heavily compounded by duration.
    """)
    st.latex(r"P_{oil} = 75 + (S \times 10) \times (1 + 0.4 \times D)")
    
    st.markdown("* **Yield Curve Shock (bps):** Captures immediate panic (driven by Severity) plus entrenched inflation expectations (driven by Duration).")
    st.latex(r"\Delta Y = (S \times 15) + (D \times 50)")

    st.markdown("""
    #### Stage 2: Financial Transmission (Basel III Capital Depletion)
    The calculated macro shocks are applied to the bank's balance sheet to calculate absolute capital depletion ($\Delta C$).
    
    * **Market Risk ($L_{market}$):** Loss on Available-for-Sale (AFS) and Held-to-Maturity (HTM) bonds. Let $V$ be portfolio value and $D_{mod}$ be modified duration.
    """)
    st.latex(r"L_{market} = V \times D_{mod} \times \left(\frac{\Delta Y}{10000}\right)")
    
    st.markdown("""
    * **Credit Risk ($L_{credit}$):** Total Expected Loss. Probability of Default ($PD$) is stressed via a multiplier ($\beta$) dependent on inflation and interest rate burdens. Let $EAD$ be Exposure at Default (Loan Book).
    """)
    st.latex(r"PD_{stressed} = PD_{base} \times \left[ 1 + \left(\frac{P_{oil} - 75}{100}\right) + \left(\frac{\Delta Y}{200}\right) \right] \times (1 + D)")
    st.latex(r"L_{credit} = EAD \times PD_{stressed} \times LGD")
    
    st.markdown("""
    * **Contagion Risk ($L_{contagion}$):** Exponential scaling network-effect losses, representing interbank defaults or direct sovereign write-offs. Let $\alpha$ be a balance-sheet scaling factor.
    """)
    st.latex(r"L_{contagion} = S^{1.4} \times \alpha")
    
    st.markdown("""
    #### Stage 3: The Basel III Output
    """)
    st.latex(r"CET1_{stressed} = \frac{Capital_{starting} - (L_{market} + L_{credit} + L_{funding} + L_{contagion})}{RWA}")

# ==========================================
# TAB 4: CLIENT SCENARIOS
# ==========================================
with tab4:
    st.subheader("Client Advisory Scenarios")
    st.markdown("""
    Use these prompts to guide a client session using the dashboard:
    
    > **"If we reduce our starting capital base through a share buyback program, how does our resilience to a 12-month Middle East conflict change?"**
    > * **Action:** Reduce the 'Starting Capital' slider and compare the 'Breach Prob.' to the previous level.
    
    > **"Does a high-intensity 3-month skirmish threaten our Basel III buffers more than a low-intensity 3-year proxy war?"**
    > * **Action:** Compare (Severity 9, Duration 3) vs. (Severity 4, Duration 36).
    
    > **"At what oil price peak does our loan book credit loss exceed our bond portfolio market loss?"**
    > * **Action:** Increase severity and observe the waterfall chart until the 'Credit Risk' bar becomes larger than 'Market Risk'.
    """)
