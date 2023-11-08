import pandas as pd


class fixedAssets:
    def __init__(self, balance_sheet_data, cash_flow_data):
        self.balance_sheet_data = balance_sheet_data
        self.cash_flow_data = cash_flow_data
        self.fixedAssets = pd.DataFrame()

    
    def generateFixedAssets(self):
        selectedColumnsBS = self.balance_sheet_data[["fiscalDateEnding", "propertyPlantEquipment"]]
        selectedColumnsCF = self.cash_flow_data[["depreciationDepletionAndAmortization", "capitalExpenditures"]]
        self.fixedAssets = pd.concat([selectedColumnsBS, selectedColumnsCF], axis=1)
    
    def returnFixedAssets(self):
        self.generateFixedAssets()
        return self.fixedAssets
        