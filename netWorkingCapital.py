import pandas as pd

class netWorkingCapital:
    def __init__(self, balance_sheet_data, income_statement_data):
        self.balance_sheet_data = balance_sheet_data
        self.income_statement_data = income_statement_data
        self.netWorkingCapital = pd.DataFrame()
    
    def generateNetWorkingCapital(self):
        selectedColumnsBS = self.balance_sheet_data[[
            "fiscalDateEnding",
            "currentNetReceivables",
            "inventory", 
            "currentAccountsPayable"
        ]]
        self.netWorkingCapital = pd.concat([selectedColumnsBS], axis=1)
        self.netWorkingCapital["currentAssets"] = self.netWorkingCapital["currentNetReceivables"] + self.netWorkingCapital["inventory"]
        self.netWorkingCapital["currentLiabilities"] = self.netWorkingCapital["currentAccountsPayable"]
        self.netWorkingCapital["netWorkingCapital"] = self.netWorkingCapital["currentAssets"] - self.netWorkingCapital["currentLiabilities"]
        
        latest_year = self.netWorkingCapital["fiscalDateEnding"].iloc[-1]
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.netWorkingCapital = pd.concat([self.netWorkingCapital, next_years], ignore_index=True)
    
    def generateAssumptions(self):
        self.netWorkingCapital["DSO"] = self.netWorkingCapital["currentNetReceivables"] / (self.income_statement_data["totalRevenue"] / 365)
        self.netWorkingCapital["DIO"] = self.netWorkingCapital["inventory"] / (self.income_statement_data["costofGoodsAndServicesSold"] / 365)
        self.netWorkingCapital["DPO"] = self.netWorkingCapital["currentAccountsPayable"] / (self.income_statement_data["costofGoodsAndServicesSold"] / 365)
        
    def returnNetWorkingCapital(self):
        self.generateNetWorkingCapital()
        self.generateAssumptions()
        return self.netWorkingCapital