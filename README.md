# DCF Valuation Tool

A Streamlit app for discounted cash flow valuation with sensitivity analysis, technical indicators, and an options implied volatility surface.

## Features
- DCF valuation (Alpha Vantage + Finnhub)
- Sensitivity analysis
- Technical analysis (Alpaca)
- Options IV surface (Alpaca)

## Requirements
- Python 3.11+
- API keys for:
  - Alpha Vantage
  - Finnhub
  - Alpaca

## Setup
```bash
pip install -r requirements.txt
```

## Run (Streamlit)
```bash
streamlit run streamlit_app.py
```

## API Keys
The app prompts users for keys in the sidebar and stores them in the session only (cleared when the tab closes).  
Do **not** commit `.streamlit/secrets.toml`.

## Notes
- Free Alpha Vantage keys are rate-limited.  
- Alpaca market data access depends on your subscription tier.
