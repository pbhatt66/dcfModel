import pandas as pd
import numpy as np
from typing import List, Dict
import matplotlib.pyplot as plt
import seaborn as sns

from freeCashFlow import freeCashFlow
from netWorkingCapital import netWorkingCapital
from terminalValue import terminalValue

class SensitivityAnalysis:
    def __init__(self, dcf_analyzer):
        self.dcf_analyzer = dcf_analyzer
        self.base_case_price = dcf_analyzer.dcf_results.implied_share_price if dcf_analyzer.dcf_results else None
        print(f"DEBUG: SensitivityAnalysis initialized with base case price: {self.base_case_price}")
        
    def wacc_terminal_growth_rate_sensitivity(self,
                                            wacc_range: List[float] = None,
                                            growth_rate_range: List[float] = None) -> pd.DataFrame:
        
        print("DEBUG: Starting WACC vs Terminal Growth sensitivity analysis...")
        
        if wacc_range is None:
            base_wacc = self.dcf_analyzer.dcf_results.wacc
            wacc_range = [base_wacc + i * 0.005 for i in range(-4, 5)]
            print(f"DEBUG: Using default WACC range: {wacc_range}")
            
        if growth_rate_range is None:
            base_growth_rate = terminalValue.growth_rate
            growth_rate_range = [base_growth_rate + 0.005 * i for i in range(-4, 5)]
            print(f"DEBUG: Using default growth rate range: {growth_rate_range}")
            
        results = pd.DataFrame(index=[f"{g:.1%}" for g in growth_rate_range],
                               columns=[f"{w:.1%}" for w in wacc_range])
        
        for i, growth_rate in enumerate(growth_rate_range):
            for j, wacc in enumerate(wacc_range):
                print(f"DEBUG: Calculating sensitivity for WACC={wacc:.1%}, Growth={growth_rate:.1%}")
                price = self.calculate_price_with_sensitivity(growth_rate, wacc)
                results.iloc[i, j] = price
        
        print("DEBUG: Sensitivity analysis completed")
        return results.astype(float).round(2)
    
    def calculate_price_with_sensitivity(self, growth_rate: float, wacc: float) -> float:
        try:
            print(f"DEBUG: Calculating price with growth_rate={growth_rate}, wacc={wacc}")
            
            fixed_asset_schedule = self.dcf_analyzer.fixed_asset_schedule
            nwc = netWorkingCapital(self.dcf_analyzer.balance_sheet, self.dcf_analyzer.income_statement, self.dcf_analyzer.cash_flow).returnNetWorkingCapital()
            fcf = freeCashFlow(self.dcf_analyzer.cash_flow, self.dcf_analyzer.income_statement, nwc, fixed_asset_schedule).generateFCF()
            
            # Ensure growth rate is less than WACC
            if growth_rate >= wacc:
                print(f"WARNING: Growth rate ({growth_rate}) >= WACC ({wacc}), adjusting growth rate")
                growth_rate = wacc - 0.01
            
            terminal_val = (fcf["unleveredFreeCashFlow"].iloc[-1] * (1 + growth_rate)) / (wacc - growth_rate)
            pv_terminal_val = terminal_val / ((1 + wacc) ** 5)
            
            latest_year = fcf["fiscalDateEnding"].iloc[3]
            sum_pv_fcf = 0
            for year in range(latest_year + 1, latest_year + 6):
                year_fcf = fcf.loc[fcf["fiscalDateEnding"] == year, "unleveredFreeCashFlow"].values[0]
                pv_fcf = year_fcf / (1 + wacc) ** (year - latest_year)
                sum_pv_fcf += pv_fcf
            
            enterprise_value = sum_pv_fcf + pv_terminal_val
            cash = self.dcf_analyzer.balance_sheet["cashAndCashEquivalentsAtCarryingValue"].iloc[-1]
            current_debt = self.dcf_analyzer.balance_sheet["currentLongTermDebt"].iloc[-1]
            long_term_debt = (self.dcf_analyzer.balance_sheet["longTermDebtNoncurrent"].iloc[-1] if self.dcf_analyzer.balance_sheet["longTermDebtNoncurrent"].iloc[-1] is not None 
                              else self.dcf_analyzer.balance_sheet["longTermDebt"].iloc[-1])
            total_debt = current_debt + long_term_debt
            equity_value = enterprise_value + cash - total_debt
            
            shares_outstanding = int(self.dcf_analyzer.company_data["SharesOutstanding"])
            price = equity_value / shares_outstanding
            
            print(f"DEBUG: Calculated price: {price}")
            return price
            
        except Exception as e:
            print(f"ERROR: Error in calculate_price_with_sensitivity: {e}")
            return 0
    
    def monte_carlo_simulation(self, n_simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation with random inputs"""
        print(f"DEBUG: Starting Monte Carlo simulation with {n_simulations} iterations...")
        
        np.random.seed(42)
        
        wacc_base = self.dcf_analyzer.dcf_results.wacc
        wacc_std = wacc_base * 0.15  # 15% standard deviation
        
        growth_base = 0.03  # 3% base terminal growth
        growth_std = 0.01   # 1% standard deviation
        
        results = []
        
        for i in range(n_simulations):
            if i % 100 == 0:
                print(f"DEBUG: Monte Carlo iteration {i}/{n_simulations}")
                
            wacc_sim = max(0.01, np.random.normal(wacc_base, wacc_std))
            growth_sim = max(0.005, min(wacc_sim - 0.01, np.random.normal(growth_base, growth_std)))
            
            price = self.calculate_price_with_sensitivity(growth_sim, wacc_sim)
            results.append(price)
        
        results = np.array(results)
        print("DEBUG: Monte Carlo simulation completed")
        
        return {
            'mean': np.mean(results),
            'std': np.std(results),
            'percentile_5': np.percentile(results, 5),
            'percentile_25': np.percentile(results, 25),
            'percentile_50': np.percentile(results, 50),
            'percentile_75': np.percentile(results, 75),
            'percentile_95': np.percentile(results, 95),
            'all_results': results
        }
    
    def forward_pe_eps_projection(self, growth_rate_range: List[float] = None, horizon: int = 5) -> pd.DataFrame:
        company_data = self.dcf_analyzer.company_data
        forward_pe = float(company_data.get("ForwardPE", 0) or 0)
        shares = int(company_data.get("SharesOutstanding", 1))
        
        last_net_income = self.dcf_analyzer.income_statement["netIncome"].iloc[-1]
        last_eps = last_net_income / shares
        
        if growth_rate_range is None:
            growth_rate_range = [0.05 * i for i in range(1, 6)]
        
        pe_min = forward_pe * 0.75
        pe_max = forward_pe * 1.25
        pe_steps = 9
        pe_range = list(np.linspace(pe_min, pe_max, pe_steps))
        
        rows = []
        for g in growth_rate_range:
            eps_projection = last_eps * (1+g) ** horizon
            row = [eps_projection * pe for pe in pe_range]
            rows.append(row)

        idx = [f"{g:.0%}" for g in growth_rate_range]
        cols = [f"{pe:.1f}" for pe in pe_range]
        df = pd.DataFrame(rows, index=idx, columns=cols)
        return df.round(2)
