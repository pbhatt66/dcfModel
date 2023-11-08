import pandas as pd
import json

class makeBalanceSheet:
    def __init__(self, json_file_path):
        self.balanceSheet = pd.read_json(json_file_path).replace("None", "0")
    
    def generateBalanceSheet(self):
        self.balanceSheet = self.balanceSheet[::-1]
        self.balanceSheet["fiscalDateEnding"] = pd.to_datetime(self.balanceSheet["fiscalDateEnding"]).dt.strftime("%Y")
        self.balanceSheet.drop(columns=["reportedCurrency"], inplace=True)
        self.balanceSheet.drop([3, 4], inplace=True)
        self.balanceSheet = self.balanceSheet.astype(int)
    
    def returnBalanceSheet(self):
        self.generateBalanceSheet()
        return self.balanceSheet

class makeIncomeStatement:
    def __init__(self, json_file_path):
        self.incomeStatement = pd.read_json(json_file_path).replace("None", "0")
    
    def generateIncomeStatement(self):
        self.incomeStatement = self.incomeStatement[::-1]
        self.incomeStatement["fiscalDateEnding"] = pd.to_datetime(self.incomeStatement["fiscalDateEnding"]).dt.strftime("%Y")
        self.incomeStatement.drop(
            columns=[
                "reportedCurrency",
                "costOfRevenue",
                "sellingGeneralAndAdministrative",
                "researchAndDevelopment",
            ], inplace=True
        )
        self.incomeStatement.drop([3, 4], inplace=True)
        self.incomeStatement = self.incomeStatement.astype(int)
        self.incomeStatement["ebit"] = (
            self.incomeStatement["ebitda"] - self.incomeStatement["depreciationAndAmortization"]
        )
    
    def returnIncomeStatement(self):
        self.generateIncomeStatement()
        return self.incomeStatement

class makeCashFlow:
    def __init__(self, json_file_path):
        self.cashFlow = pd.read_json(json_file_path).replace("None", "0")
        
    def generateCashFlow(self):
        self.cashFlow = self.cashFlow[::-1]
        self.cashFlow["fiscalDateEnding"] = pd.to_datetime(self.cashFlow["fiscalDateEnding"]).dt.strftime("%Y")
        self.cashFlow.drop(columns=["reportedCurrency", "changeInExchangeRate"], inplace=True)
        self.cashFlow.drop([3, 4], inplace=True)
        self.cashFlow = self.cashFlow.astype(int)
    
    def returnCashFlow(self):
        self.generateCashFlow()
        return self.cashFlow
        