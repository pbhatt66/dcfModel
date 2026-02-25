from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest
from config import get_secret

def _get_alpaca_options_client():
    api_key = get_secret("ALPACA_API_KEY")
    api_secret = get_secret("ALPACA_SECRET_KEY")
    if not api_key or not api_secret:
        raise ValueError("Missing Alpaca API credentials")
    return OptionHistoricalDataClient(api_key, api_secret)

def _parse_occ_symbol(symbol: str):
    
    strike_part = symbol[-8:]
    cp = symbol[-9]
    date_part = symbol[-15:-9]
    root = symbol[:-15]

    expiration = pd.to_datetime(date_part, format="%y%m%d")
    strike = int(strike_part) / 1000.0
    opt_type = "call" if cp == "C" else "put"
    return root, expiration, strike, opt_type

def fetch_option_chain(ticker: str, limit: int = 1000) -> pd.DataFrame:
    client = _get_alpaca_options_client()
    req = OptionChainRequest(underlying_symbol=ticker, limit=limit)
    chain = client.get_option_chain(req)

    items = chain.values() if isinstance(chain, dict) else chain

    rows = []
    for c in items:
        sym = c.symbol
        _, exp, strike, opt_type = _parse_occ_symbol(sym)
        iv = c.implied_volatility
        rows.append({
            "symbol": sym,
            "expiration_date": exp,
            "strike": strike,
            "type": opt_type,
            "iv": float(iv) if iv is not None else None,
        })

    df = pd.DataFrame(rows).dropna(subset=["iv"])
    return df

def build_iv_surface(df: pd.DataFrame, options_type: str = "call") -> pd.DataFrame:
    df = df[df["type"] == options_type].copy()
    if df.empty:
        raise ValueError(f"No {options_type} options found in the data")
    
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], utc=True)
    today = pd.Timestamp.now(tz=timezone.utc).normalize()

    df["dte"] = (df["expiration_date"].dt.normalize() - today).dt.days
    
    surface = df.pivot_table(
        index="dte",
        columns="strike",
        values="iv",
        aggfunc="mean"
    ).sort_index()
    
    return surface

def build_plot(ticker, surface: pd.DataFrame, options_type: str = "call") -> go.Figure:
    fig = go.Figure(data=[go.Surface(
        z=surface.values,
        x=surface.columns,
        y=surface.index,
        colorscale="Viridis"
    )])
    fig.update_layout(
        title=f"{ticker} {options_type.capitalize()} Implied Volatility Surface",
        height=800,
        width=1200,
        margin=dict(l=20, r=20, b=20, t=50),
        scene=dict(
            xaxis_title="Strike Price",
            yaxis_title="Days to Expiration",
            zaxis_title="Implied Volatility"
        )
    )
    return fig
    

if __name__ == "__main__":
    ticker = "AAPL"
    df = fetch_option_chain(ticker)
    surface = build_iv_surface(df, options_type="call")
    fig = build_plot(ticker, surface, options_type="call")
    fig.show()