import pandas as pd
import numpy as np

class freeCashFlow:
    
    def __init__(self, cash_flow_data, income_statement_data, nwc, fixedAssetSchedule):
        self.cash_flow_data = cash_flow_data
        self.income_statement_data = income_statement_data
        self.nwc = nwc
        self.fixedAssetSchedule = fixedAssetSchedule
        self.unleveredFreeCashFlow = pd.DataFrame()
        self.assumptions = self._calculate_assumptions()
        
    def _calculate_assumptions(self):
        try:
            revenue_growth_rate = self.income_statement_data["totalRevenue"].pct_change().dropna()
            # print(f"Revenue Growth Rate: {revenue_growth_rate.tolist()}")

            avg_revenue_growth = max(-0.1, min(0.3, revenue_growth_rate.tail(3).mean()))
            growth_rates = []
            current_growth_rate = avg_revenue_growth
            for i in range(5):
                growth_rates.append(current_growth_rate)
                current_growth_rate *= 0.8
                current_growth_rate = max(0.02, current_growth_rate)
            
            # print(f"Projected Revenue Growth Rates: {growth_rates}")
            
            cogs_percentages = (self.income_statement_data["costofGoodsAndServicesSold"] / self.income_statement_data["totalRevenue"]).dropna()
            avg_cogs_percentage = cogs_percentages.mean()
            recent_cogs_trend = cogs_percentages.tail(3).mean() - avg_cogs_percentage
            
            cogs_projections = []
            current_cogs_percentage = cogs_percentages.iloc[-1]
            annual_improvement = -0.002 if recent_cogs_trend < 0 else 0.002
            for i in range(5):
                cogs_projections.append(current_cogs_percentage)
                current_cogs_percentage = max(0.2, min(0.8, current_cogs_percentage + annual_improvement))

            # print("Historical COGS Percentages:", cogs_percentages.tolist())
            # print("Projected COGS Percentages:", cogs_projections)
        
            opex_percentages = (self.income_statement_data["operatingExpenses"] / self.income_statement_data["totalRevenue"]).dropna()
            recent_opex_trend = opex_percentages.tail(3).mean() - opex_percentages.head(3).mean()
            
            opex_projections = []
            current_opex = opex_percentages.iloc[-1]
            annual_leverage = -0.003 if recent_opex_trend < 0 else 0.003
            for i in range(5):
                opex_projections.append(current_opex)
                current_opex = max(0.05, min(0.5, current_opex + annual_leverage))
                
            da_pct = (self.income_statement_data["depreciationAndAmortization"] / self.income_statement_data["totalRevenue"]).dropna().tail(3).mean()
            da_projections = [da_pct] * 5
            
            print(self.cash_flow_data["capitalExpenditures"])
            
            capex_pct = (self.cash_flow_data["capitalExpenditures"] / self.income_statement_data["totalRevenue"]).dropna().tail(3).mean()
            capex_projections = [capex_pct] * 5
            
            return {
                "revenue_growth_rate": growth_rates,
                "cogs_percentage_of_revenue": cogs_projections,
                "operating_expenses_percentage_of_revenue": opex_projections,
                "d&a_percentage_of_revenue": da_projections,
                "capex_percentage_of_revenue": capex_projections,
            }
            
        except Exception as e:
            print(f"Error calculating assumptions: {e}")
    
    def generateFCF(self):
        print(self.assumptions)
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
        nwc_filtered = self.nwc[self.nwc["fiscalDateEnding"].isin(self.unleveredFreeCashFlow["fiscalDateEnding"])]
        changeNWC = [np.nan]  # The first value is NaN because there's no change for the first year

        for i in range(1, len(nwc_filtered)):
            change = nwc_filtered["netWorkingCapital"].iloc[i] - nwc_filtered["netWorkingCapital"].iloc[i - 1]
            changeNWC.append(change)

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
        self.unleveredFreeCashFlow["d&a_as_percentage_of_revenue"] = self.unleveredFreeCashFlow["depreciationAndAmortization"] / self.unleveredFreeCashFlow["totalRevenue"]
        self.unleveredFreeCashFlow["capex_as_percentage_of_revenue"] = self.unleveredFreeCashFlow["capitalExpenditures"] / self.unleveredFreeCashFlow["totalRevenue"]
        
        latest_year = self.unleveredFreeCashFlow["fiscalDateEnding"].iloc[-1]
        next_years = pd.DataFrame({"fiscalDateEnding": [latest_year + i for i in range(1, 6)]})
        self.unleveredFreeCashFlow = pd.concat([self.unleveredFreeCashFlow, next_years], ignore_index=True)
        
        for i, year in enumerate(range(latest_year + 1, latest_year + 6)):
            year_index = i
            
            self.unleveredFreeCashFlow.loc[
                self.unleveredFreeCashFlow["fiscalDateEnding"] == year, "revenueGrowth"
            ] = self.assumptions["revenue_growth_rate"][year_index]
            
            self.unleveredFreeCashFlow.loc[
                self.unleveredFreeCashFlow["fiscalDateEnding"] == year, "cogs_as_percentage_of_revenue"
            ] = self.assumptions["cogs_percentage_of_revenue"][year_index]
            
            self.unleveredFreeCashFlow.loc[
                self.unleveredFreeCashFlow["fiscalDateEnding"] == year, "operating_expenses_as_percentage_of_revenue"
            ] = self.assumptions["operating_expenses_percentage_of_revenue"][year_index]
            self.unleveredFreeCashFlow.loc[
                self.unleveredFreeCashFlow["fiscalDateEnding"] == year, "d&a_as_percentage_of_revenue"
            ] = self.assumptions["d&a_percentage_of_revenue"][year_index]
            self.unleveredFreeCashFlow.loc[
                self.unleveredFreeCashFlow["fiscalDateEnding"] == year, "capex_as_percentage_of_revenue"
            ] = self.assumptions["capex_percentage_of_revenue"][year_index]
                    
        for year in range(latest_year + 1, latest_year + 6):
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year - 1, 'totalRevenue'].values[0] * \
                (1 + self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'revenueGrowth'])
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'costofGoodsAndServicesSold'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'cogs_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'grossProfit'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'costofGoodsAndServicesSold']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operatingExpenses'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operating_expenses_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebitda'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'grossProfit'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'operatingExpenses']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'd&a_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebitda'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'incomeTaxExpense'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] * 0.21
           
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'netIncome'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'ebit'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'incomeTaxExpense']

            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationDepletionAndAmortization'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationAndAmortization']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'capitalExpenditures'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'capex_as_percentage_of_revenue'] * \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'totalRevenue']
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'changeNWC'] = self.nwc.loc[self.nwc['fiscalDateEnding'] == year, 'netWorkingCapital'].values[0] - self.nwc.loc[self.nwc['fiscalDateEnding'] == year - 1, 'netWorkingCapital'].values[0]
            
            self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'unleveredFreeCashFlow'] = self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'netIncome'] + \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'depreciationDepletionAndAmortization'] - self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'changeNWC'] - \
                self.unleveredFreeCashFlow.loc[self.unleveredFreeCashFlow["fiscalDateEnding"] == year, 'capitalExpenditures']
        
        return self.unleveredFreeCashFlow