import os
import pandas as pd
import numpy as np
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import get_secret

def _get_alpaca_creds():
    api_key = get_secret("ALPACA_API_KEY") or os.getenv("ALPACA_API_KEY")
    api_secret = get_secret("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET_KEY")
    return api_key, api_secret

class TechnicalAnalysis:
    def __init__(self, ticker):
        self.ticker = ticker
        api_key, api_secret = _get_alpaca_creds()
        self.client = StockHistoricalDataClient(api_key, api_secret)
        self.data = pd.DataFrame()
        
    def fetch_historical_data(self, years: int = 3):
        end_dt   = pd.Timestamp.now()
        start_dt = end_dt - pd.DateOffset(years=years)
        
        req = StockBarsRequest(
            symbol_or_symbols=[self.ticker],
            timeframe=TimeFrame.Day,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
            limit=None,
            feed="iex"
        )
        barset = self.client.get_stock_bars(req)
        bars = barset.df.sort_index()
        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.droplevel(0)
        
        self.data = bars
        return bars
    
    def calculate_indicators(self):
        df = self.data.copy()
        
        # Moving Averages
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['close'].rolling(window=20).std()
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['close'].rolling(window=20).std()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        self.data = df
        return df
        
    def plot_indicators(self):
        df = self.data.copy()
        
        bb_low_signal = df["close"] <= df["BB_Lower"]
        rsi_oversold = df["RSI"] < 30
        macd_bullish = (df["MACD"] < df["MACD_Signal"])

        buy_signal = bb_low_signal & rsi_oversold & macd_bullish
        exit_signal =( df["close"] >= df["BB_Middle"]) & (df["close"].shift(1) < df["BB_Middle"].shift(1))
        
        buy_dates = df.index[buy_signal]
        exit_dates = []
        for b in buy_dates:
            future = exit_signal[exit_signal.index > b]
            if not future.empty:
                exit_dates.append(future.index[0])

        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.2, 0.3],
            subplot_titles=(
                f"{self.ticker} Price + SMA & Bollinger Bands",
                "RSI (14)",
                "MACD (12,26,9)"
            ),
        )

        fig.add_trace(
            go.Candlestick(
                x=df.index, open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name='Price'
            ),
            row=1, col=1
        )
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50',    line=dict(width=1)),    row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200',  line=dict(width=1)),    row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper', line=dict(width=1)),    row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'],name='BB Middle',line=dict(width=1)),    row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower', line=dict(width=1)),    row=1, col=1)

        # buy and exit signals
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=df.loc[buy_dates, 'low'] * 0.98,
                mode='markers',
                marker_symbol='triangle-up',
                marker_color='green',
                marker_size=14,
                name='Buy Signal'
            ), row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=exit_dates,
                y=df.loc[exit_dates, 'high'] * 1.02,
                mode='markers',
                marker_symbol='triangle-down',
                marker_color='red',
                marker_size=14,
                name='Exit Signal'
            ), row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(width=1)),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD'],        name='MACD',        line=dict(width=1)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal',      line=dict(width=1)),
            row=3, col=1
        )

        hist = df['MACD'] - df['MACD_Signal']
        fig.add_trace(
            go.Bar(x=df.index, y=hist, name='Histogram', marker_line_width=0),
            row=3, col=1
        )

        fig.update_layout(
            template="plotly_dark",
            height=900,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=60, r=20, t=80, b=40),
            xaxis_rangeslider_visible=False,
            title=f"{self.ticker} Technical Indicators",
        )

        for row in (1, 2, 3):
            fig.update_xaxes(
                row=row, col=1,
                type="date",
                tickformat="%b %Y",
                tickangle=-45,
                showgrid=True,
                gridcolor="gray",
            )

        fig.update_yaxes(title_text="Price", row=1, col=1, showgrid=True)
        fig.update_yaxes(
            title_text="RSI", row=2, col=1,
            range=[0, 100],
            showgrid=True
        )

        fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="white", opacity=0.3)
        fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="white", opacity=0.3)

        fig.update_yaxes(title_text="MACD", row=3, col=1, showgrid=True)

        return fig
        
        