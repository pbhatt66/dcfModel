import json
import pandas as pd

class wacc:
    riskFreeRate = 0.04
    expectedMarketReturn = 0.09
    beta = 1.2
    riskPremium = expectedMarketReturn - riskFreeRate
    
    
    def __init__(self, balance_sheet_data, income_statement_data):
        self.balance_sheet_data = balance_sheet_data
        self.income_statement_data = income_statement_data
        self.wacc = pd.DataFrame()
    
    def getDebt(self):
        total_debt = self.balance_sheet_data["currentLongTermDebt"].iloc[-1] + self.balance_sheet_data["longTermDebtNoncurrent"].iloc[-1]
        return total_debt
        
    def getWacc(self):
        # intraday_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}"
        # company_overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={self.symbol}&apikey={self.api_key}"
        # r = requests.get(intraday_url)
        # latest_price = float(list(list(r.json()["Time Series (5min)"].values())[0].values())[0])
        # shares_outstanding = int(requests.get(company_overview_url).json()["SharesOutstanding"])
        # total_equity = requests.get(company_overview_url).json()["MarketCapitalization"]
        with open("companyData.json") as json_file:
            company_data = json.load(json_file)
        total_equity = int(company_data["MarketCapitalization"])
        # total_debt = self.balance_sheet_data["currentLongTermDebt"].iloc[-1] + self.balance_sheet_data["longTermDebtNoncurrent"].iloc[-1]
        total_debt = self.getDebt()
        cost_of_debt = self.income_statement_data["interestExpense"].iloc[-1] / total_debt
        print(f"Cost of Debt: {cost_of_debt}")
        afterTax_cost_of_debt = cost_of_debt * (1 - 0.21)
        weight_of_debt = total_debt / (total_debt + total_equity)
        
        cost_of_equity = self.riskFreeRate + self.beta * self.riskPremium
        print(f"Cost of Equity: {cost_of_equity}")
        weight_of_equity = total_equity / (total_debt + total_equity)
        
        wacc = (weight_of_debt * afterTax_cost_of_debt) + (weight_of_equity * cost_of_equity)
        return wacc
        
        
        