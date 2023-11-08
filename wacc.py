import requests

class wacc:
    def getWacc(api_key, symbol, balance_sheet_data):
        # intraday_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}"
        company_overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
        # r = requests.get(intraday_url)
        # latest_price = float(list(list(r.json()["Time Series (5min)"].values())[0].values())[0])
        # shares_outstanding = int(requests.get(company_overview_url).json()["SharesOutstanding"])
        total_equity = requests.get(company_overview_url).json()["MarketCapitalization"]
        total_debt = balance_sheet_data[]
        