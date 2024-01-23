import pandas as pd

class terminalValue:
    growth_rate = 0.03
    
    def __init(self, freeCashFlow, wacc):
        self.freeCashFlow = freeCashFlow
        self.wacc = wacc
        self.projectedCashFlowPV = pd.DataFrame()
    
    def calculateTerminalValue(self):
        self.projectedCashFlowPV["Unlevered FCF"] = self.freeCashFlow["unleveredFreeCashFlow"]
        # for future years 1 to 5, PV_FCF = UFCF / (1+wacc)^year
        self.projectedCashFlowPV["PV FCF"] = self.projectedCashFlowPV["Unlevered FCF"]/(1+self.wacc)^year
        
        # terminal value = (FCF year n + (1 + growth rate))/ (wacc - growth rate)