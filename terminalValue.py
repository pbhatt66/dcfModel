import pandas as pd
import json

class terminalValue:
    growth_rate = 0.05
    
    def __init__(self, freeCashFlow, wacc, balanceSheet, company_data):
        self.freeCashFlow = freeCashFlow
        self.wacc = wacc
        self.balanceSheet = balanceSheet
        self.company_data = company_data
        self.projectedCashFlowPV = pd.DataFrame()
        print(f"DEBUG: terminalValue initialized with growth_rate: {self.growth_rate}")
        print(f"DEBUG: WACC: {self.wacc}")
        print(f"DEBUG: FCF shape: {self.freeCashFlow.shape}")
    
    def calculatePVofFCF(self):
        try:
            print("DEBUG: Starting PV of FCF calculation...")
            
            self.projectedCashFlowPV["fiscalDateEnding"] = self.freeCashFlow["fiscalDateEnding"]
            self.projectedCashFlowPV["Unlevered FCF"] = self.freeCashFlow["unleveredFreeCashFlow"]
            # print(f"DEBUG: Initial PV DataFrame shape: {self.projectedCashFlowPV.shape}")
            # print(f"DEBUG: Years in PV DataFrame: {self.projectedCashFlowPV['fiscalDateEnding'].tolist()}")
            
            # for future years 1 to 5, PV_FCF = UFCF / (1+wacc)^year
            latest_year = self.projectedCashFlowPV["fiscalDateEnding"].iloc[3]
            # print(f"DEBUG: Latest year (index 3): {latest_year}")
            
            # Initialize PV FCF column
            self.projectedCashFlowPV["PV FCF"] = 0.0
            
            for year in range(latest_year + 1, latest_year + 6):
                # print(f"DEBUG: Calculating PV for year {year}")
                
                # Check if year exists in dataframe
                year_mask = self.projectedCashFlowPV["fiscalDateEnding"] == year
                if not year_mask.any():
                    # print(f"WARNING: Year {year} not found in DataFrame")
                    continue
                
                fcf_value = self.projectedCashFlowPV.loc[year_mask, "Unlevered FCF"].iloc[0]
                discount_factor = (1 + self.wacc) ** (year - latest_year)
                pv_value = fcf_value / discount_factor
                
                # print(f"DEBUG: Year {year} - FCF: {fcf_value}, Discount Factor: {discount_factor}, PV: {pv_value}")
                
                self.projectedCashFlowPV.loc[year_mask, "PV FCF"] = pv_value
            
            # print(f"DEBUG: PV FCF calculation completed")
            # print(f"DEBUG: Final PV DataFrame:\n{self.projectedCashFlowPV}")
            
            return self.projectedCashFlowPV
            
        except Exception as e:
            print(f"ERROR: Error in calculatePVofFCF: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return self.projectedCashFlowPV
    
    def calculateTerminalValue(self):
        try:
            print("DEBUG: Starting terminal value calculation...")
            
            # terminal value = (FCF year n + (1 + growth rate))/ (wacc - growth rate)
            last_fcf = self.projectedCashFlowPV["Unlevered FCF"].iloc[-1]
            # print(f"DEBUG: Last FCF: {last_fcf}")
            
            terminal_value = (last_fcf * (1 + self.growth_rate)) / (self.wacc - self.growth_rate)
            # print(f"DEBUG: Terminal value: {terminal_value}")
            
            pv_terminal_value = terminal_value / ((1+self.wacc)**5)
            # print(f"DEBUG: PV of terminal value: {pv_terminal_value}")
            
            sum_of_pv_fcf = self.projectedCashFlowPV["PV FCF"].sum()
            # print(f"DEBUG: Sum of PV FCF: {sum_of_pv_fcf}")
            
            enterprise_value = sum_of_pv_fcf + pv_terminal_value
            # print(f"DEBUG: Enterprise value: {enterprise_value}")
            
            cash = self.balanceSheet["cashAndCashEquivalentsAtCarryingValue"].iloc[-1]
            total_debt = (self.balanceSheet["currentLongTermDebt"].iloc[-1] + 
                         self.balanceSheet["longTermDebtNoncurrent"].iloc[-1])
            
            equity_value = enterprise_value + cash - total_debt
            # print(f"DEBUG: Equity Value: {equity_value}")
            
            shares_outstanding = int(self.company_data["SharesOutstanding"])
            implied_share_price = equity_value / shares_outstanding
            # print(f"DEBUG: Implied Share Price: {implied_share_price}")
            
            return {
                'terminal_value': terminal_value,
                'pv_terminal_value': pv_terminal_value,
                'enterprise_value': enterprise_value,
                'equity_value': equity_value,
                'implied_share_price': implied_share_price
            }
            
        except Exception as e:
            print(f"ERROR: Error in calculateTerminalValue: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return None