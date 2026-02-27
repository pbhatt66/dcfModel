import io
import os
import streamlit as st
import altair as alt
import pandas as pd
import uuid
from pathlib import Path
import matplotlib as mpl
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
import numpy as np
import plotly.graph_objects as go
from options_vol_surface import fetch_option_chain, build_iv_surface, build_plot
from dcf import DCFAnalyzer
from sensitivityAnalysis import SensitivityAnalysis
from technicalAnalysis import TechnicalAnalysis
from config import get_secret

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

DATA_ROOT = Path("data") / f"session_{st.session_state.session_id}"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
    
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "run_dcf_clicked" not in st.session_state:
    st.session_state.run_dcf_clicked = False
if "iv_surface_payload" not in st.session_state:
    st.session_state.iv_surface_payload = None
if "iv_option_type" not in st.session_state:
    st.session_state.iv_option_type = "call"
if "iv_max_contracts" not in st.session_state:
    st.session_state.iv_max_contracts = 800

def to_excel(dcf: DCFAnalyzer, sensitivity_df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dcf.income_statement.to_excel(writer, sheet_name='Income Statement', index=False)
        dcf.balance_sheet.to_excel(writer, sheet_name='Balance Sheet', index=False)
        dcf.cash_flow.to_excel(writer, sheet_name='Cash Flow Statement', index=False)
        
        pd.DataFrame(dcf.free_cash_flow.assumptions).to_excel(writer, sheet_name='Assumptions', index=False)
        
        dcf.fixed_asset_schedule.to_excel(writer, sheet_name='Fixed Asset Schedule', index=False)
        dcf.nwc.returnNetWorkingCapital().to_excel(writer, sheet_name='Net Working Capital', index=False)
        
        dcf.free_cash_flow.unleveredFreeCashFlow.to_excel(writer, sheet_name='FCF projections', index=False)
        
        tv = dcf.tv_calculator
        tv.projectedCashFlowPV.to_excel(writer, sheet_name='PV of FCF', index=False)
        
        summary = pd.DataFrame({
            "Metric": [
                "Current Share Price", "Implied Share Price", "Upside/Downside",
                "WACC", "Enterprise Value", "Equity Value", "Terminal Value"
            ],
            "Value": [
                dcf.dcf_results.current_share_price,
                dcf.dcf_results.implied_share_price,
                f"{dcf.dcf_results.upside_downside:.1%}",
                f"{dcf.dcf_results.wacc:.2%}",
                dcf.dcf_results.enterprise_value,
                dcf.dcf_results.equity_value,
                dcf.dcf_results.terminal_value
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)

        # 6) sensitivity
        sensitivity_df.to_excel(writer, sheet_name="Sensitivity", index=True)

    output.seek(0)  # Reset the BytesIO object to the beginning
    return output.getvalue()

st.set_page_config(page_title="Stock Valuation", layout="wide")
st.title("🔍 Stock Valuation Dashboard")
if not st.session_state.run_dcf_clicked:
    st.markdown(
        """
        ### Before You Run
        Use this app to estimate a stock's value from a simplified DCF workflow and supporting analytics.

        **What this dashboard includes**
        - DCF valuation summary
        - Free cash flow projections and PV breakdown
        - Sensitivity analysis (WACC vs. terminal growth)
        - Technical analysis charting
        - Options implied volatility surface
        - Excel export of core model outputs

        **API keys required**
        - **Alpha Vantage**: company overview + financial statements
        - **Finnhub**: current share price quote used in upside/downside
        - **Alpaca**: options chain data for IV surface tab

        **Rate limit notes**
        - Free API tiers can throttle requests or return incomplete responses
        - Alpha Vantage free tier is especially strict; repeated reruns can trigger limits
        - If data fails to load, wait and rerun later, or use higher-tier API access

        **Model assumptions / caveats**
        - Revenue and line items are projected using simple linear assumptions
        - Terminal value uses a constant-growth perpetuity model
        - Outputs are directional and educational, not investment advice
        """
    )

ticker = st.sidebar.text_input("Ticker").upper()

if "alpha_key" not in st.session_state:
    st.session_state.alpha_key = ""
if "finnhub_key" not in st.session_state:
    st.session_state.finnhub_key = ""
if "alpaca_key" not in st.session_state:
    st.session_state.alpaca_key = ""
if "alpaca_secret" not in st.session_state:
    st.session_state.alpaca_secret = ""

st.sidebar.markdown("**Alpha Vantage API Key** *(get it [here](https://www.alphavantage.co/support/#api-key))*")
st.session_state.alpha_key = st.sidebar.text_input(
    "Alpha Vantage API Key",
    type="password",
    value=st.session_state.alpha_key,
    label_visibility="collapsed"
)

st.sidebar.markdown("**Finnhub API Key** *(get it [here](https://finnhub.io/dashboard))*")
st.session_state.finnhub_key = st.sidebar.text_input(
    "Finnhub API Key",
    type="password",
    value=st.session_state.finnhub_key,
    label_visibility="collapsed"
)

st.sidebar.markdown("**Alpaca API key** *(get it [here](https://app.alpaca.markets/signup))*")
st.session_state.alpaca_key = st.sidebar.text_input(
    "Alpaca API Key",
    type="password",
    value=st.session_state.alpaca_key,
    label_visibility="collapsed"
)

st.sidebar.markdown("**Alpaca Secret Key**")
st.session_state.alpaca_secret = st.sidebar.text_input(
    "Alpaca Secret Key",
    type="password",
    value=st.session_state.alpaca_secret,
    label_visibility="collapsed"
)

alpha_key = st.session_state.alpha_key
finnhub_key = st.session_state.finnhub_key
alpaca_key = st.session_state.alpaca_key
alpaca_secret = st.session_state.alpaca_secret

if alpha_key:
    os.environ["ALPHAVANTAGE_API_KEY"] = alpha_key
if finnhub_key:
    os.environ["FINNHUB_API_KEY"] = finnhub_key
if alpaca_key:
    os.environ["ALPACA_API_KEY"] = alpaca_key
if alpaca_secret:
    os.environ["ALPACA_SECRET_KEY"] = alpaca_secret

run_dcf_button = st.sidebar.button("Run DCF")


if run_dcf_button:
    st.session_state.run_dcf_clicked = True
    if not alpha_key or not finnhub_key:
        st.error("Please enter Alpha Vantage and Finnhub API keys.")
    else:
        try:
            with st.spinner("Running…"):
                try:
                    dcf = DCFAnalyzer(ticker, alpha_key, finnhub_key, data_dir=str(DATA_ROOT))
                    ok = dcf.run_full_analysis()
                except Exception as e:
                    st.error(f"Error running DCF analysis: {e}")
                    ok = False
            if not ok:
                st.error("DCF failed – check terminal logs.")
            else:
                st.session_state.dcf = dcf
                try:
                    st.session_state.res = dcf.dcf_results
                except Exception as e:
                    st.error(f"Error loading DCF results: {e}")
                    st.session_state.res = None
                try:
                    st.session_state.sens_df = SensitivityAnalysis(dcf).wacc_terminal_growth_rate_sensitivity()
                except Exception as e:
                    st.error(f"Error running sensitivity analysis: {e}")
                    st.session_state.sens_df = None
                st.session_state.analysis_done = True
        except Exception as e:
            msg = str(e).lower()
            if "alphavantage" in msg and ("rate limit" in msg or "thank you for using alpha vantage" in msg):
                st.error("API limit was reached. Please wait and try again, or use a premium key.")
            else:
                st.error(f"Unexpected error: {e}")
        
if st.session_state.analysis_done:
    dcf = st.session_state.dcf
    res = st.session_state.res
    sens_df = st.session_state.sens_df
    if "terminal_growth_rate" not in st.session_state and dcf:
        try:
            st.session_state.terminal_growth_rate = dcf.tv_calculator.growth_rate
        except Exception:
            st.session_state.terminal_growth_rate = 0.03
    
    tabs = st.tabs([
        "📊 Overview",
        "📈 Projections",
        "🧮 Technical Analysis",
        "❔ What-If Analysis",
        "📐 Options Volatility Surface"
    ])
    
    # 1) Overview tab
    with tabs[0]:
        st.header("Key Metrics")
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 2, 2], gap="small")
        c1.metric("Current Price", f"${res.current_share_price:.2f}")
        c2.metric("Implied Price", f"${res.implied_share_price:,.2f}", delta=f"{res.upside_downside:.1%}")
        c3.metric("WACC", f"{res.wacc:.2%}")
        c4.metric("Enterprise Value", f"${res.enterprise_value:,.0f}")
        c5.metric("Equity Value", f"${res.equity_value:,.0f}")
        
        st.divider()
        
        try:
            excel_bytes = to_excel(dcf, sens_df)
            st.download_button(
                "📥 Download Full DCF Model",
                data=excel_bytes,
                file_name=f"{ticker}_DCF_Model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.warning(f"Excel export unavailable: {e}")

    # 2) Projections tab
    with tabs[1]:
        try:
            st.subheader("Projected Free Cash Flow")
            fcf = dcf.free_cash_flow.unleveredFreeCashFlow.copy()
            fcf["fiscalDateEnding"] = fcf["fiscalDateEnding"].astype(int).astype(str)
            fcf_pivot = fcf.set_index("fiscalDateEnding").T
            fcf_pivot.index.name = None
            st.dataframe(fcf_pivot)

            st.subheader("PV of Future Cash Flows")
            pv = dcf.tv_calculator.projectedCashFlowPV.copy()
            pv["fiscalDateEnding"] = pv["fiscalDateEnding"].astype(int).astype(str)
            pv_pivot = pv.set_index("fiscalDateEnding").T
            pv_pivot.index.name = None
            st.dataframe(pv_pivot)
            
            # 3) Revenue vs. Price chart
            fcf = dcf.free_cash_flow.unleveredFreeCashFlow.copy()
            rev_df = fcf[["fiscalDateEnding", "totalRevenue"]].copy()
            rev_df["fiscalDateEnding"] = pd.to_datetime(
                rev_df["fiscalDateEnding"].astype(int).astype(str), format="%Y"
            )
            rev_df["year"] = rev_df["fiscalDateEnding"].dt.year
            hist_df = rev_df.iloc[:4]
            proj_df = rev_df.iloc[3:]

            
            hist_line = (
                alt.Chart(hist_df)
                .mark_line(color="blue", strokeWidth=2)
                .encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("totalRevenue:Q", title="Total Revenue"),   
                )
            )
            proj_line = (
                alt.Chart(proj_df)
                .mark_line(color="orange", strokeDash=[5, 5], strokeWidth=2)
                .encode(
                    x=alt.X("year:O"),
                    y=alt.Y("totalRevenue:Q"),
                )
            )
            combo = (
                alt.layer(hist_line, proj_line)
                .properties(
                    title=f"Revenue Projections for {ticker}",
                    width=800,
                    height=400
                )
            )
            
            st.subheader("📈 Historical vs Projected Revenue")
            st.altair_chart(combo, use_container_width=True)
            
            pe_proj = SensitivityAnalysis(dcf).forward_pe_eps_projection(
                growth_rate_range=np.arange(0.05, 0.21, 0.01),
            )
            st.subheader("5-Year Forward P/E (col.) vs. EPS Growth (row)")
            st.dataframe(pe_proj.style.format("${:,.2f}"), use_container_width=True)
        except Exception as e:
            st.warning(f"Projection data unavailable: {e}")
        
    # Technical Analysis tab
    with tabs[2]:
        ta = TechnicalAnalysis(ticker=ticker)
        df = ta.fetch_historical_data()
        if df is None or df.empty:
            st.error("Failed to fetch historical data for technical analysis.")
        else:
            df = ta.calculate_indicators()
            fig = ta.plot_indicators()
            st.plotly_chart(fig, use_container_width=True)
        
    
    # 3) What-If Analysis tab
    with tabs[3]:
        try:
            # sensitivity
            sens = SensitivityAnalysis(dcf)
            sens_df = sens.wacc_terminal_growth_rate_sensitivity()
            base_price = res.implied_share_price
            vmin = sens_df.values.min()
            vmax = sens_df.values.max()
            
            cmap = LinearSegmentedColormap.from_list(
                "red_white_green",
                ["red","white","green"]
            
            )
            norm = TwoSlopeNorm(vmin=vmin, vcenter=base_price, vmax=vmax)
            
            def style_by_distance(val):
                if np.isclose(val, base_price):
                    return "background-color: white; color: black;"
                rgba = cmap(norm(val))
                return f"background-color: {mpl.colors.to_hex(rgba)}; color: black;"
            
            styled = (
                sens_df.style
                .applymap(style_by_distance)
                .format(lambda v: f"${v:,.2f}")
            )
            
            st.subheader("Sensitivity: WACC (col.) vs Terminal Growth (row)")
            st.write(styled)
            
            tv_calc = dcf.tv_calculator
            default_tv = tv_calc.growth_rate
            
            growth_slider = st.slider(
                "Terminal Growth Rate",
                min_value=0.01,
                max_value=st.session_state.res.wacc - 0.01,
                step=0.001,
                format="%.3f",
                key="terminal_growth_rate",
            )
            
            tv_calc.growth_rate = growth_slider
            tv_out = tv_calc.calculateTerminalValue()
            st.subheader("🔧 Adjust Terminal Growth")
            st.metric("Growth Rate", f"{growth_slider:.2%}")
            st.metric("New Implied Price", f"${tv_out['implied_share_price']:.2f}")
        except Exception as e:
            st.warning(f"Sensitivity analysis unavailable: {e}")
        
    # 4) IV Surface tab
    with tabs[4]:
        st.subheader("Options Implied Volatility Surface (Alpaca)")
        with st.form("iv_surface_form"):
            option_type = st.selectbox(
                "Option Type",
                ["call", "put"],
                key="iv_option_type",
            )
            max_contracts = st.slider(
                "Max contracts",
                200,
                2000,
                key="iv_max_contracts",
                step=100,
            )
            load_iv_surface = st.form_submit_button("Load IV Surface")

        if load_iv_surface:
            try:
                df = fetch_option_chain(ticker, limit=max_contracts)
                surface = build_iv_surface(df, options_type=option_type)
                if surface is None or surface.empty:
                    st.warning("No IV data found.")
                    st.session_state.iv_surface_payload = None
                else:
                    st.session_state.iv_surface_payload = {
                        "ticker": ticker,
                        "option_type": option_type,
                        "surface": surface,
                    }
            except Exception as e:
                st.error(f"Failed to load IV surface: {e}")
                st.session_state.iv_surface_payload = None

        iv_payload = st.session_state.iv_surface_payload
        if iv_payload:
            fig = build_plot(
                iv_payload["ticker"],
                iv_payload["surface"],
                options_type=iv_payload["option_type"],
            )
            st.plotly_chart(fig, use_container_width=True)
