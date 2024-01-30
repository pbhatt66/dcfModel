import pandas as pd


class fixedAssets:
    assumptions = {
        "DandA_as_percentage_of_beginning_PPE": 0.287,
        "CapEx_as_percentage_of_beginning_PPE": 0.347
    }
    
    def __init__(self, balance_sheet_data, cash_flow_data):
        self.balance_sheet_data = balance_sheet_data
        self.cash_flow_data = cash_flow_data
        self.fixedAssets = pd.DataFrame()

    
    def generateFixedAssets(self):
        selectedColumnsBS = self.balance_sheet_data[["fiscalDateEnding", "propertyPlantEquipment"]]
        selectedColumnsCF = self.cash_flow_data[["depreciationDepletionAndAmortization", "capitalExpenditures"]]
        self.fixedAssets = pd.concat([selectedColumnsBS, selectedColumnsCF], axis=1)
        self.fixedAssets.rename(columns={"propertyPlantEquipment": "endingPPE"}, inplace=True)
        self.fixedAssets["beginningPPE"] = self.fixedAssets["endingPPE"].shift(1)
        
        # set capital expenditures until 2023 to be equal to endingPPE - beginningPPE + D&A
        self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] <= 2023, "capitalExpenditures"] = self.fixedAssets["endingPPE"] - self.fixedAssets["beginningPPE"] + self.fixedAssets["depreciationDepletionAndAmortization"]
        
        self.fixedAssets["D&A as percentage of beginning PPE"] = self.fixedAssets["depreciationDepletionAndAmortization"] / self.fixedAssets["beginningPPE"]
        self.fixedAssets["CapEx as percentage of beginning PPE"] = self.fixedAssets["capitalExpenditures"] / self.fixedAssets["beginningPPE"]
        
        # create future years
        latest_year = self.fixedAssets["fiscalDateEnding"].iloc[-1]
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.fixedAssets = pd.concat([self.fixedAssets, next_years], ignore_index=True)
        
        # project future D&A and CapEx
        self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] > latest_year, "D&A as percentage of beginning PPE"] = self.assumptions["DandA_as_percentage_of_beginning_PPE"]
        self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] > latest_year, "CapEx as percentage of beginning PPE"] = self.assumptions["CapEx_as_percentage_of_beginning_PPE"]
        
        # for future years 2024 - 2028, set beginning PPE = ending PPE from previous year, then calculate D&A and CapEx using the percentages as percentages of beginning PPE, and then calculate ending PPE
        for year in range(latest_year + 1, latest_year + 6):
            self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "beginningPPE"] = self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year - 1, "endingPPE"].values[0]
            self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "depreciationDepletionAndAmortization"] = self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "D&A as percentage of beginning PPE"] * self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "beginningPPE"]
            self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "capitalExpenditures"] = self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "CapEx as percentage of beginning PPE"] * self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "beginningPPE"]
            self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "endingPPE"] = self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "beginningPPE"] + self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "capitalExpenditures"] - self.fixedAssets.loc[self.fixedAssets["fiscalDateEnding"] == year, "depreciationDepletionAndAmortization"]
    
    def returnFixedAssets(self):
        self.generateFixedAssets()
        return self.fixedAssets
        