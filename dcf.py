import os
import requests
import pandas as pd
import json
import numpy as np
import time
from dataclasses import dataclass
from fixedAssets import fixedAssets
from utility import makeBalanceSheet, makeIncomeStatement, makeCashFlow
from netWorkingCapital import netWorkingCapital
from freeCashFlow import freeCashFlow
from wacc import wacc
from terminalValue import terminalValue
import finnhub
from config import get_secret

@dataclass
class DCFResults:
    wacc: float
    enterprise_value: float
    equity_value: float
    implied_share_price: float
    current_share_price: float
    upside_downside: float
    terminal_value: float
    pv_of_fcf: float

class DCFAnalyzer:
    def __init__(self, ticker: str, api_key: str, finnhub_key: str | None = None, data_dir: str = "data"):
        self.ticker = ticker.upper()
        self.api_key = api_key
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.company_data = None
        self.income_statement = None
        self.balance_sheet = None
        self.cash_flow = None
        self.dcf_results = None
        self.fixed_asset_schedule = None
        self.finnhub_client = None

        if finnhub_key:
            self.finnhub_client = finnhub.Client(api_key=finnhub_key)

        print(f"DEBUG: DCFAnalyzer initialized for {self.ticker}")
    
    def fetch_company_data(self) -> bool:
        file_path = os.path.join(self.data_dir, f"{self.ticker}_companyData.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    self.company_data = json.load(f)
                print(f"DEBUG: Loaded company data from {file_path}")
                return True
            except Exception as e:
                print(f"ERROR: Failed to load cached company data: {e}")
        try:
            print(f"DEBUG: Fetching company data for {self.ticker}")
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={self.ticker}&apikey={self.api_key}"
            response = requests.get(url)
            company_data = response.json()
            self.company_data = company_data
            with open(file_path, "w") as file:
                json.dump(company_data, file)
            
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"ERROR: Error fetching company data: {e}")
            return False
    
    def fetch_financial_statements(self) -> bool:
        inc_fp = os.path.join(self.data_dir, f"{self.ticker}_incomeStatement.json")
        bs_fp = os.path.join(self.data_dir, f"{self.ticker}_balanceSheet.json")
        cf_fp = os.path.join(self.data_dir, f"{self.ticker}_cashFlow.json")
        
        if os.path.exists(inc_fp) and os.path.exists(bs_fp) and os.path.exists(cf_fp):
            return True
        
        try:
            print("DEBUG: Fetching financial statements...")
            
            # Fetch Income Statement
            print("DEBUG: Fetching Income Statement...")
            income_statement_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={self.ticker}&apikey={self.api_key}"
            response = requests.get(income_statement_url)
            income_statement_data = response.json()["annualReports"][0:5]
            with open(inc_fp, "w") as file:
                json.dump(income_statement_data, file)
            print(f"DEBUG: Income statement saved, {len(income_statement_data)} years of data")
            
            time.sleep(1.5)
            
            # Fetch Balance Sheet
            print("DEBUG: Fetching Balance Sheet...")
            balance_sheet_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={self.ticker}&apikey={self.api_key}"
            response = requests.get(balance_sheet_url)
            balance_sheet_data = response.json()["annualReports"][0:5]
            with open(bs_fp, "w") as file:
                json.dump(balance_sheet_data, file)
            print(f"DEBUG: Balance sheet saved, {len(balance_sheet_data)} years of data")
            
            time.sleep(1.5)
            
            # Fetch Cash Flow
            print("DEBUG: Fetching Cash Flow...")
            cash_flow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={self.ticker}&apikey={self.api_key}"
            response = requests.get(cash_flow_url)
            cash_flow_data = response.json()["annualReports"][0:5]
            with open(cf_fp, "w") as file:
                json.dump(cash_flow_data, file)
            print(f"DEBUG: Cash flow saved, {len(cash_flow_data)} years of data")
                
            return True
        except Exception as e:
            print(f"ERROR: Error fetching financial statements: {e}")
            return False
    
    def process_financial_data(self):
        try:
            print("DEBUG: Processing financial data...")
            
            print("DEBUG: Processing income statement...")
            self.income_statement = makeIncomeStatement(os.path.join(self.data_dir, f"{self.ticker}_incomeStatement.json")).returnIncomeStatement()
            
            print("DEBUG: Processing balance sheet...")
            self.balance_sheet = makeBalanceSheet(os.path.join(self.data_dir, f"{self.ticker}_balanceSheet.json")).returnBalanceSheet()
            
            print("DEBUG: Processing cash flow...")
            self.cash_flow = makeCashFlow(os.path.join(self.data_dir, f"{self.ticker}_cashFlow.json")).returnCashFlow()
            
            print("DEBUG: Financial data processing completed")
            
        except Exception as e:
            print(f"ERROR: Error processing financial data: {e}")
            raise
    
    def calculate_dcf(self):
        try:
            print("DEBUG: Starting DCF calculation...")
            
            print("DEBUG: Calculating fixed asset schedule...")
            self.fixed_asset_schedule = fixedAssets(self.balance_sheet, self.cash_flow).returnFixedAssets()
            
            print("DEBUG: Calculating net working capital...")
            self.nwc = netWorkingCapital(self.balance_sheet, self.income_statement, self.cash_flow)
            nwc = self.nwc.returnNetWorkingCapital()
            
            
            print("DEBUG: Calculating free cash flow...")
            self.free_cash_flow = freeCashFlow(self.cash_flow, self.income_statement, nwc, self.fixed_asset_schedule)
            fcf = self.free_cash_flow.generateFCF()
            
            print(f"DEBUG: FCF years: {fcf['fiscalDateEnding'].tolist()}")
            print(f"DEBUG: Unlevered FCF values: {fcf['unleveredFreeCashFlow'].tolist()}")
            
            print("DEBUG: Calculating WACC...")
            wacc_calculator = wacc(self.balance_sheet, self.income_statement, self.company_data)
            wacc_value = wacc_calculator.getWacc()
            print(f"DEBUG: WACC value: {wacc_value}")
            
            print("DEBUG: Calculating terminal value...")
            tv_calculator = terminalValue(fcf, wacc_value, self.balance_sheet, self.company_data)
            pv_fcf = tv_calculator.calculatePVofFCF()
            
            self.tv_calculator = tv_calculator
            
            # Check if 'PV FCF' column exists
            if 'PV FCF' not in pv_fcf.columns:
                print("ERROR: 'PV FCF' column not found in pv_fcf DataFrame")
                print(f"DEBUG: Available columns: {list(pv_fcf.columns)}")
                return None
            
            terminal_val = (fcf["unleveredFreeCashFlow"].iloc[-1] * (1 + tv_calculator.growth_rate)) / (wacc_value - tv_calculator.growth_rate)
            print(f"DEBUG: Terminal value: {terminal_val}")
            
            pv_terminal_val = terminal_val / ((1 + wacc_value) ** 5)
            print(f"DEBUG: PV of terminal value: {pv_terminal_val}")
            
            sum_of_pv_fcf = pv_fcf["PV FCF"].sum()
            print(f"DEBUG: Sum of PV FCF: {sum_of_pv_fcf}")
            
            enterprise_value = sum_of_pv_fcf + pv_terminal_val
            print(f"DEBUG: Enterprise value: {enterprise_value}")
            
            cash = self.balance_sheet["cashAndCashEquivalentsAtCarryingValue"].iloc[-1]
            total_debt = self.balance_sheet["currentLongTermDebt"].iloc[-1] + self.balance_sheet["longTermDebtNoncurrent"].iloc[-1]
            print(f"DEBUG: Cash: {cash}")
            print(f"DEBUG: Total debt: {total_debt}")
            
            equity_value = enterprise_value + cash - total_debt
            print(f"DEBUG: Equity value: {equity_value}")
            
            shares_outstanding = int(self.company_data["SharesOutstanding"])
            print(f"DEBUG: Shares outstanding: {shares_outstanding}")
            
            implied_share_price = equity_value / shares_outstanding
            print(f"DEBUG: Implied share price: {implied_share_price}")
            
            if not self.finnhub_client:
                raise ValueError("Missing FINNHUB_API_KEY. Set it in .streamlit/secrets.toml or env.")
            current_share_price = self.finnhub_client.quote(self.ticker)['c']
            
            upside_downside = (implied_share_price - current_share_price) / current_share_price
            print(f"DEBUG: Upside/Downside: {upside_downside}")
            
            self.dcf_results = DCFResults(
                wacc=wacc_value,
                enterprise_value=enterprise_value,
                equity_value=equity_value,
                implied_share_price=implied_share_price,
                current_share_price=current_share_price,
                upside_downside=upside_downside,
                terminal_value=pv_terminal_val,
                pv_of_fcf=sum_of_pv_fcf
            )
            print("DEBUG: DCF results created successfully")
            return self.dcf_results
            
        except Exception as e:
            print(f"ERROR: Error in DCF calculation: {e}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            return None
    
    def run_full_analysis(self) -> bool:
        print(f"DEBUG: Starting DCF analysis for {self.ticker}...")
        
        if not self.fetch_company_data():
            print("ERROR: Failed to fetch company data")
            return False
            
        if not self.fetch_financial_statements():
            print("ERROR: Failed to fetch financial statements")
            return False
        
        try:
            self.process_financial_data()
            result = self.calculate_dcf()
            if result is None:
                print("ERROR: DCF calculation returned None")
                return False
            print(f"DEBUG: DCF analysis completed for {self.ticker}.")
            return True
        except Exception as e:
            print(f"ERROR: Error in full analysis: {e}")
            return False

if __name__ == "__main__":
    dcf = DCFAnalyzer(
        "WMT",
        get_secret("ALPHAVANTAGE_API_KEY"),
        get_secret("FINNHUB_API_KEY")
    )
    dcf.fetch_company_data()
    # display(DCFAnalyzer.company_data)
    print(DCFAnalyzer.company_data["SharesOutstanding"])
    # display(DCFAnalyzer.dcf_results)