import pandas as pd
import numpy as np

class fixedAssets:
    
    def __init__(self, balance_sheet_data, cash_flow_data):
        self.balance_sheet_data = balance_sheet_data
        self.cash_flow_data = cash_flow_data
        self.fixedAssets = pd.DataFrame()
        self.assumptions = self._calculate_assumptions()

    def _calculate_assumptions(self):
        try:
            merged_data = pd.merge(
                self.balance_sheet_data[["fiscalDateEnding", "propertyPlantEquipment"]], 
                self.cash_flow_data[["depreciationDepletionAndAmortization", "capitalExpenditures"]], 
                left_index=True, 
                right_index=True
            )
            merged_data["beginningPPE"] = merged_data["propertyPlantEquipment"].shift(1)
            merged_data = merged_data.dropna()
            
            if len(merged_data) == 0:
                print("WARNING: No historical data available for fixed asset calculations")
                return

            merged_data["DA_pct"] = merged_data["depreciationDepletionAndAmortization"] / merged_data["beginningPPE"]
            merged_data["CapEx_pct"] = abs(merged_data["capitalExpenditures"]) / merged_data["beginningPPE"]
            
            merged_data = merged_data.replace([np.inf, -np.inf], np.nan).dropna()
            
            avg_da_pct = merged_data["DA_pct"].mean()
            avg_capex_pct = merged_data["CapEx_pct"].mean()
            
            return {
                "DandA_as_percentage_of_beginning_PPE": avg_da_pct,
                "CapEx_as_percentage_of_beginning_PPE": avg_capex_pct
            }
            
        except Exception as e:
            print(f"Error calculating assumptions: {e}")
            
    def _get_latest_year(self):
        return self.balance_sheet_data["fiscalDateEnding"].iloc[-1]
    
    def _clean_capex_data(self):
        for i in range(len(self.fixedAssets)):
            year = self.fixedAssets.iloc[i]["fiscalDateEnding"]
            
            if year <= self._get_latest_year() and i > 0:
                beginning_ppe = self.fixedAssets.iloc[i]["beginningPPE"]
                ending_ppe = self.fixedAssets.iloc[i]["endingPPE"]
                depreciation = self.fixedAssets.iloc[i]["depreciationDepletionAndAmortization"]
                
                calculated_capex = ending_ppe - beginning_ppe + depreciation
                reported_capex = abs(self.fixedAssets.iloc[i]["capitalExpenditures"])
                
                if abs(calculated_capex - reported_capex) > 0.05 * abs(reported_capex):
                    self.fixedAssets.loc[i, "capitalExpenditures"] = calculated_capex
                    print(f"Adjusted capital expenditures for {year}: {calculated_capex} (was {reported_capex})")
                
    
    def generateFixedAssets(self):
        selectedColumnsBS = self.balance_sheet_data[["fiscalDateEnding", "propertyPlantEquipment"]]
        selectedColumnsCF = self.cash_flow_data[["depreciationDepletionAndAmortization", "capitalExpenditures"]]
        
        self.fixedAssets = pd.concat([selectedColumnsBS, selectedColumnsCF], axis=1)
        self.fixedAssets.rename(columns={"propertyPlantEquipment": "endingPPE"}, inplace=True)
        self.fixedAssets["beginningPPE"] = self.fixedAssets["endingPPE"].shift(1)
        
        self._clean_capex_data()
        
        self.fixedAssets["D&A as percentage of beginning PPE"] = self.fixedAssets["depreciationDepletionAndAmortization"] / self.fixedAssets["beginningPPE"]
        self.fixedAssets["CapEx as percentage of beginning PPE"] = self.fixedAssets["capitalExpenditures"] / self.fixedAssets["beginningPPE"]
        
        latest_year = self._get_latest_year()
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.fixedAssets = pd.concat([self.fixedAssets, next_years], ignore_index=True)
        
        future_mask = self.fixedAssets["fiscalDateEnding"] > latest_year
        self.fixedAssets.loc[future_mask, "D&A as percentage of beginning PPE"] = self.assumptions["DandA_as_percentage_of_beginning_PPE"]
        self.fixedAssets.loc[future_mask, "CapEx as percentage of beginning PPE"] = self.assumptions["CapEx_as_percentage_of_beginning_PPE"]
        
        for year in range(latest_year + 1, latest_year + 6):
            year_mask = self.fixedAssets["fiscalDateEnding"] == year
            prev_year_mask = self.fixedAssets["fiscalDateEnding"] == year - 1
            
            prev_ending_ppe = self.fixedAssets.loc[prev_year_mask, "endingPPE"].values[0]
            self.fixedAssets.loc[year_mask, "beginningPPE"] = prev_ending_ppe
            
            da_pct = self.fixedAssets.loc[year_mask, "D&A as percentage of beginning PPE"].values[0]
            calculated_da = da_pct * prev_ending_ppe
            self.fixedAssets.loc[year_mask, "depreciationDepletionAndAmortization"] = calculated_da
            
            capex_pct = self.fixedAssets.loc[year_mask, "CapEx as percentage of beginning PPE"].values[0]
            calculated_capex = capex_pct * prev_ending_ppe
            self.fixedAssets.loc[year_mask, "capitalExpenditures"] = calculated_capex
            
            ending_ppe = prev_ending_ppe + calculated_capex - calculated_da
            self.fixedAssets.loc[year_mask, "endingPPE"] = ending_ppe
            
            print(f"DEBUG: Year {year} - Beginning PPE: {prev_ending_ppe:.0f}, CapEx: {calculated_capex:.0f}, D&A: {calculated_da:.0f}, Ending PPE: {ending_ppe:.0f}")
    
    
    def returnFixedAssets(self):
        self.generateFixedAssets()
        return self.fixedAssets
        