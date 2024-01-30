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
            "otherCurrentAssets",
            "currentAccountsPayable",
            "otherCurrentLiabilities",
        ]]
        self.netWorkingCapital = pd.concat([selectedColumnsBS], axis=1)
        self.netWorkingCapital["currentAssets"] = self.netWorkingCapital["currentNetReceivables"] + self.netWorkingCapital["inventory"] + self.netWorkingCapital["otherCurrentAssets"]
        self.netWorkingCapital["currentLiabilities"] = self.netWorkingCapital["currentAccountsPayable"] + self.netWorkingCapital["otherCurrentLiabilities"]
        self.netWorkingCapital["netWorkingCapital"] = self.netWorkingCapital["currentAssets"] - self.netWorkingCapital["currentLiabilities"]
        
        latest_year = self.netWorkingCapital["fiscalDateEnding"].iloc[-1]
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.netWorkingCapital = pd.concat([self.netWorkingCapital, next_years], ignore_index=True)
    
    def generateAssumptions(self):
        self.netWorkingCapital["DSO"] = self.netWorkingCapital["currentNetReceivables"] / (self.income_statement_data["totalRevenue"] / 365)
        self.netWorkingCapital["DIO"] = self.netWorkingCapital["inventory"] / (self.income_statement_data["costofGoodsAndServicesSold"] / 365)
        self.netWorkingCapital["DPO"] = self.netWorkingCapital["currentAccountsPayable"] / (self.income_statement_data["costofGoodsAndServicesSold"] / 365)
        self.netWorkingCapital["otherCurrentAssetsAsPercentageOfRevenue"] = self.netWorkingCapital["otherCurrentAssets"] / self.income_statement_data["totalRevenue"]
        self.netWorkingCapital["otherCurrentLiabilitiesAsPercentageOfRevenue"] = self.netWorkingCapital["otherCurrentLiabilities"] / self.income_statement_data["totalRevenue"]
        
        # Use the averages of the DSO, DIO, and DPO to get the target DSO, DIO, and DPO for the next 5 years
        targetDSO = self.netWorkingCapital["DSO"].mean()
        targetDIO = self.netWorkingCapital["DIO"].mean()
        targetDPO = self.netWorkingCapital["DPO"].mean()
        targetOtherCurrentAssetsAsPercentageOfRevenue = self.netWorkingCapital["otherCurrentAssetsAsPercentageOfRevenue"].mean()
        targetOtherCurrentLiabilitiesAsPercentageOfRevenue = self.netWorkingCapital["otherCurrentLiabilitiesAsPercentageOfRevenue"].mean()
        # set the DSO, DIO, and DPO of the next 5 years to be the respective averages
        self.netWorkingCapital.loc[self.netWorkingCapital.index[-5:], "DSO"] = targetDSO
        self.netWorkingCapital.loc[self.netWorkingCapital.index[-5:], "DIO"] = targetDIO
        self.netWorkingCapital.loc[self.netWorkingCapital.index[-5:], "DPO"] = targetDPO
        self.netWorkingCapital.loc[self.netWorkingCapital.index[-5:], "otherCurrentAssetsAsPercentageOfRevenue"] = targetOtherCurrentAssetsAsPercentageOfRevenue
        self.netWorkingCapital.loc[self.netWorkingCapital.index[-5:], "otherCurrentLiabilitiesAsPercentageOfRevenue"] = targetOtherCurrentLiabilitiesAsPercentageOfRevenue
        
        latest_year = self.netWorkingCapital["fiscalDateEnding"].iloc[3]
        # print(latest_year)
        revenue_growth_rate = [0.1, 0.1, 0.1, 0.1, 0.1]
        cogs_as_percentage_of_revenue = [0.55, 0.55, 0.55, 0.55, 0.55]
        future_revenues = [0] * 5
        future_revenues[0] = self.income_statement_data["totalRevenue"].iloc[-1] * (1 + revenue_growth_rate[0])
        cogs = [0] * 5
        cogs[0] = future_revenues[0] * cogs_as_percentage_of_revenue[0]
        for i in range(1, 5):
            future_revenues[i] = future_revenues[i - 1] * (1 + revenue_growth_rate[i])
            cogs[i] = future_revenues[i] * cogs_as_percentage_of_revenue[i]
        # set future receivables, inventory, and payables to be based on the target DSO, DIO, and DPO
        for year in range(latest_year + 1, latest_year + 6):
            # self.netWorkingCapital["currentNetReceivables"][year] = (future_revenues[year - latest_year - 1] / 365) * targetDSO
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentNetReceivables"] = (future_revenues[year - latest_year - 1] / 365) * targetDSO
            # self.netWorkingCapital["inventory"][year] = (cogs[year - latest_year - 1] / 365) * targetDIO
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "inventory"] = (cogs[year - latest_year - 1] / 365) * targetDIO
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "otherCurrentAssets"] = future_revenues[year - latest_year - 1] * targetOtherCurrentAssetsAsPercentageOfRevenue
            # self.netWorkingCapital["currentAccountsPayable"][year] = (cogs[year - latest_year - 1] / 365) * targetDPO
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentAccountsPayable"] = (cogs[year - latest_year - 1] / 365) * targetDPO
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "otherCurrentLiabilities"] = future_revenues[year - latest_year - 1] * targetOtherCurrentLiabilitiesAsPercentageOfRevenue
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentAssets"] = self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentNetReceivables"]\
                + self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "inventory"]\
                + self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "otherCurrentAssets"]
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentLiabilities"] = self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentAccountsPayable"]\
                + self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "otherCurrentLiabilities"]
            self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "netWorkingCapital"] = self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentAssets"]\
                - self.netWorkingCapital.loc[self.netWorkingCapital["fiscalDateEnding"] == year, "currentLiabilities"]
        
    def returnNetWorkingCapital(self):
        self.generateNetWorkingCapital()
        self.generateAssumptions()
        return self.netWorkingCapital