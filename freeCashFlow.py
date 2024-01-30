import pandas as pd
import numpy as np

class freeCashFlow:
    assumptions = {
        "revenue_growth_rate": [0.1, 0.1, 0.1, 0.1, 0.1],
        "cogs_percentage_of_revenue": [0.55, 0.55, 0.55, 0.55, 0.55],
        "operating_expenses_percentage_of_revenue": [0.13, 0.13, 0.13, 0.13, 0.13],
    }
    
    def __init__(self, cash_flow_data, income_statement_data, nwc, fixedAssetSchedule):
        self.cash_flow_data = cash_flow_data
        self.income_statement_data = income_statement_data
        self.nwc = nwc
        self.fixedAssetSchedule = fixedAssetSchedule
        self.unleveredFreeCashFlow = pd.DataFrame()
    
        
    def generateFCF(self):
        def format_as_percentage(number):
            return f"{number * 100:.2f}%"
        
        selectedColumnsIS = self.income_statement_data[
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
        selectedColumnsCF = self.cash_flow_data[
            ["depreciationDepletionAndAmortization", "capitalExpenditures"]
        ]
        
        self.unleveredFreeCashFlow = pd.concat([selectedColumnsIS, selectedColumnsCF], axis=1)
        # self.unleveredFreeCashFlow["changeNWC"] = self.nwc["netWorkingCapital"].diff()
        # set changeNWC column to be equal to current year's netWorkingCapital - previous year's netWorkingCapital
        # Initialize an empty list to store the changeNWC values
        nwc_filtered = self.nwc[self.nwc["fiscalDateEnding"].isin(self.unleveredFreeCashFlow["fiscalDateEnding"])]
        changeNWC = [np.nan]  # The first value is NaN because there's no change for the first year

        # Calculate changeNWC for each year
        for i in range(1, len(nwc_filtered)):
            change = nwc_filtered["netWorkingCapital"].iloc[i] - nwc_filtered["netWorkingCapital"].iloc[i - 1]
            changeNWC.append(change)

        # Assign the changeNWC list to the changeNWC column of the unleveredFreeCashFlow DataFrame
        self.unleveredFreeCashFlow["changeNWC"] = changeNWC
        
        self.unleveredFreeCashFlow["unleveredFreeCashFlow"] = (
            self.unleveredFreeCashFlow["netIncome"]
            + self.unleveredFreeCashFlow["depreciationDepletionAndAmortization"]
            - self.unleveredFreeCashFlow["changeNWC"]
            - self.unleveredFreeCashFlow["capitalExpenditures"]
        )
        self.unleveredFreeCashFlow["revenueGrowth"] = self.unleveredFreeCashFlow["totalRevenue"].pct_change()
        self.unleveredFreeCashFlow["cogs_as_percentage_of_revenue"] = self.unleveredFreeCashFlow["costofGoodsAndServicesSold"] / self.unleveredFreeCashFlow["totalRevenue"]
        self.unleveredFreeCashFlow["operating_expenses_as_percentage_of_revenue"] = self.unleveredFreeCashFlow["operatingExpenses"] / self.unleveredFreeCashFlow["totalRevenue"]
        
        latest_year = self.unleveredFreeCashFlow["fiscalDateEnding"].iloc[-1]
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.unleveredFreeCashFlow = pd.concat([self.unleveredFreeCashFlow, next_years], ignore_index=True)
        
        # project future revenues using the revenue growth rate
        self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] > latest_year, "revenueGrowth"] = self.assumptions["revenue_growth_rate"]
        self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] > latest_year, "cogs_as_percentage_of_revenue"] = self.assumptions["cogs_percentage_of_revenue"]
        self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] > latest_year, "operating_expenses_as_percentage_of_revenue"] = self.assumptions["operating_expenses_percentage_of_revenue"]
        
        for year in range(latest_year + 1, latest_year + 6):
            # project total revenue
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year - 1, 'totalRevenue'].values[0] * \
                (1 + self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'revenueGrowth'])
            # project COGS
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'costofGoodsAndServicesSold'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'cogs_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            # project gross profit
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'grossProfit'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'costofGoodsAndServicesSold']
            # project operating expenses
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operatingExpenses'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operating_expenses_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            # project EBITDA
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebitda'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'grossProfit'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operatingExpenses']
            # project depreciation and amortization
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization'] = self.fixedAssetSchedule.loc[self.fixedAssetSchedule["fiscalDateEnding"] == year, 'depreciationDepletionAndAmortization'].values[0]
            #  project EBIT
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebitda'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization']
            # project income tax expense
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'incomeTaxExpense'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] * 0.21
            # project net income
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'netIncome'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'incomeTaxExpense']
            # add back depreciation and amortization
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationDepletionAndAmortization'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization']
            # pull capital expenditures from fixedAssetSchedule
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'capitalExpenditures'] = self.fixedAssetSchedule.loc[self.fixedAssetSchedule["fiscalDateEnding"] == year, 'capitalExpenditures']
            # pull changeNWC from nwc
            # self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'changeNWC'] = self.nwc.loc[self.nwc["fiscalDateEnding"] == year, 'netWorkingCapital'] - self.nwc.loc[self.nwc["fiscalDateEnding"] == year - 1, 'netWorkingCapital']
            # print out NWC for each future year
            # print(f"Net Working Capital for {year}: {self.nwc.loc[self.nwc['fiscalDateEnding'] == year, 'netWorkingCapital'].values[0]}")
            # print(f"Change in NWC from {year - 1} to {year}: {self.nwc.loc[self.nwc['fiscalDateEnding'] == year, 'netWorkingCapital'].values[0] - self.nwc.loc[self.nwc['fiscalDateEnding'] == year - 1, 'netWorkingCapital'].values[0]}")
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'changeNWC'] = self.nwc.loc[self.nwc['fiscalDateEnding'] == year, 'netWorkingCapital'].values[0] - self.nwc.loc[self.nwc['fiscalDateEnding'] == year - 1, 'netWorkingCapital'].values[0]
            # calculate unlevered free cash flow
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'unleveredFreeCashFlow'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'netIncome'] + \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationDepletionAndAmortization'] - self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'changeNWC'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'capitalExpenditures']
        
        return self.unleveredFreeCashFlow
    
        
        