import requests
import pandas as pd
from IPython.display import display
import json
from fixedAssets import fixedAssets
from utility import makeBalanceSheet, makeIncomeStatement, makeCashFlow
from netWorkingCapital import netWorkingCapital
from freeCashFlow import freeCashFlow
from wacc import wacc

api_key = "0QIZ1SNXRHO8UH7A"
symbol = "AAPL"

company_overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
r = requests.get(company_overview_url)
company_data_request = r.json()
save_file = open("companyData.json", "w")
json.dump(company_data_request, save_file)
save_file.close()

# Income Statement
# income_statement_url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={api_key}"
# r = requests.get(income_statement_url)
# income_statement_data = r.json()["annualReports"]
# save_file = open("incomeStatement.json", "w")
# json.dump(income_statement_data, save_file)
# save_file.close()

incomeStatement = makeIncomeStatement("./incomeStatement.json").returnIncomeStatement()
selectedColumnsIS = incomeStatement[
    [
        "fiscalDateEnding",
        "totalRevenue",
        "costofGoodsAndServicesSold",
        "grossProfit",
        "operatingExpenses",
        "ebitda",
        "depreciationAndAmortization",
        "ebit",
        "incomeTaxExpense",
        "netIncome",
    ]
]

# Cash Flow
# cash_flow_url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={api_key}"
# r = requests.get(cash_flow_url)
# cash_flow_data = r.json()["annualReports"]
# save_file = open("cashFlow.json", "w")
# json.dump(cash_flow_data, save_file)
# save_file.close()

cashFlow = makeCashFlow("./cashFlow.json").returnCashFlow()
selectedColumnsCF = cashFlow[
    ["depreciationDepletionAndAmortization", "capitalExpenditures"]
]


# Balance Sheet
# balance_sheet_url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={api_key}"
# r = requests.get(balance_sheet_url)
# balance_sheet_data = r.json()["annualReports"]
# save_file = open("balanceSheet.json", "w")
# json.dump(balance_sheet_data, save_file)
# save_file.close()

balanceSheet = makeBalanceSheet("./balanceSheet.json").returnBalanceSheet()


def format_as_percentage(number):
    return f"{number * 100:.2f}%"


fixedAssetSchedule = fixedAssets(balanceSheet, cashFlow).returnFixedAssets()
nwc = netWorkingCapital(balanceSheet, incomeStatement).returnNetWorkingCapital()

# UNLEVERED FREE CASH FLOW
unleveredFreeCashFlow = freeCashFlow(cashFlow, incomeStatement, nwc, fixedAssetSchedule).generateFCF()

wacc = wacc(balanceSheet, incomeStatement).getWacc()

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
display(unleveredFreeCashFlow)
# display(nwc)
# print(wacc)
