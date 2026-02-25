import json
import pandas as pd

class wacc:
    riskFreeRate = 0.044
    expectedMarketReturn = 0.09
    riskPremium = expectedMarketReturn - riskFreeRate
    
    def __init__(self, balance_sheet_data, income_statement_data, company_data):
        self.balance_sheet_data = balance_sheet_data
        self.income_statement_data = income_statement_data
        self.company_data = company_data
        self.wacc = pd.DataFrame()
        
    
    def getDebt(self):
        try:
            current_debt = self.balance_sheet_data["currentLongTermDebt"].iloc[-1]
            long_term_debt = (self.balance_sheet_data["longTermDebtNoncurrent"].iloc[-1] if self.balance_sheet_data["longTermDebtNoncurrent"].iloc[-1] != 0
                              else self.balance_sheet_data["longTermDebt"].iloc[-1])
            total_debt = current_debt + long_term_debt
            print(f"DEBUG: Current long-term debt: {current_debt}")
            print(f"DEBUG: Long-term debt noncurrent: {long_term_debt}")
            print(f"DEBUG: Total debt: {total_debt}")
            return total_debt
        except Exception as e:
            print(f"ERROR: Error calculating debt: {e}")
            return 0
        
    def getWacc(self):
        try:
            print("DEBUG: Starting WACC calculation...")
            
            total_equity = int(self.company_data["MarketCapitalization"])
            print(f"DEBUG: Market capitalization (total equity): {total_equity}")
            
            total_debt = self.getDebt()
            
            if total_debt == 0:
                print("WARNING: Total debt is zero, setting cost of debt to 0")
                cost_of_debt = 0
                afterTax_cost_of_debt = 0
            else:
                interest_expense = self.income_statement_data["interestExpense"].iloc[-1]
                cost_of_debt = interest_expense / total_debt
                print(f"DEBUG: Interest expense: {interest_expense}")
                print(f"DEBUG: Cost of Debt: {cost_of_debt}")
                afterTax_cost_of_debt = cost_of_debt * (1 - 0.21)
            
            print(f"DEBUG: After-tax cost of debt: {afterTax_cost_of_debt}")
            
            weight_of_debt = total_debt / (total_debt + total_equity)
            print(f"DEBUG: Weight of debt: {weight_of_debt}")
            
            cost_of_equity = self.riskFreeRate + float(self.company_data["Beta"]) * self.riskPremium
            print(f"DEBUG: Cost of Equity: {cost_of_equity}")
            
            weight_of_equity = total_equity / (total_debt + total_equity)
            print(f"DEBUG: Weight of equity: {weight_of_equity}")
            
            wacc_value = (weight_of_debt * afterTax_cost_of_debt) + (weight_of_equity * cost_of_equity)
            print(f"DEBUG: Final WACC: {wacc_value}")
            
            return wacc_value
            
        except Exception as e:
            print(f"ERROR: Error in WACC calculation: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return None