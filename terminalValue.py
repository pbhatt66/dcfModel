import pandas as pd
import json

class terminalValue:
    growth_rate = 0.05
    
    def __init__(self, freeCashFlow, wacc, balanceSheet):
        self.freeCashFlow = freeCashFlow
        self.wacc = wacc
        self.balanceSheet = balanceSheet
        self.projectedCashFlowPV = pd.DataFrame()
    
    def calculatePVofFCF(self):
        self.projectedCashFlowPV["fiscalDateEnding"] = self.freeCashFlow["fiscalDateEnding"]
        self.projectedCashFlowPV["Unlevered FCF"] = self.freeCashFlow["unleveredFreeCashFlow"]
        # for future years 1 to 5, PV_FCF = UFCF / (1+wacc)^year
        latest_year = self.projectedCashFlowPV["fiscalDateEnding"].iloc[3]
        for year in range(latest_year + 1, latest_year + 6):
            self.projectedCashFlowPV.loc[self.projectedCashFlowPV["fiscalDateEnding"] == year, "PV FCF"] = self.projectedCashFlowPV.loc[self.projectedCashFlowPV["fiscalDateEnding"] == year, "Unlevered FCF"] / (1+self.wacc)**(year - latest_year)
            # self.projectedCashFlowPV["PV FCF"] = self.projectedCashFlowPV["Unlevered FCF"]/(1+self.wacc)**(year - latest_year)
        
        return self.projectedCashFlowPV
    
    def calculateTerminalValue(self):
        # terminal value = (FCF year n + (1 + growth rate))/ (wacc - growth rate)
        terminal_value = (self.projectedCashFlowPV["Unlevered FCF"].iloc[-1] * (1 + self.growth_rate)) / (self.wacc - self.growth_rate)
        pv_terminal_value = terminal_value / ((1+self.wacc)**5)
        sum_of_pv_fcf = self.projectedCashFlowPV["PV FCF"].sum()
        enterprise_value = sum_of_pv_fcf + pv_terminal_value
        equity_value = enterprise_value + self.balanceSheet["cashAndCashEquivalentsAtCarryingValue"].iloc[-1]\
            - (self.balanceSheet["currentLongTermDebt"].iloc[-1] + self.balanceSheet["longTermDebtNoncurrent"].iloc[-1])
        print(f"Equity Value: {equity_value}")
        # read in shares outstanding from companyData.json
        with open("companyData.json") as json_file:
            company_data = json.load(json_file)
        shares_outstanding = int(company_data["SharesOutstanding"])
        implied_share_price = equity_value / shares_outstanding
        print(f"Implied Share Price: {implied_share_price}")