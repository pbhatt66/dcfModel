import argparse
import sys
from dcf import DCFAnalyzer
from sensitivityAnalysis import SensitivityAnalysis
# from excel_exporter import DCFExcelExporter
from config import get_secret

def main():
    parser = argparse.ArgumentParser(description='DCF Valuation Tool')
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument('--api-key', required=False, help='Alpha Vantage API key')
    parser.add_argument('--sensitivity', action='store_true', help='Run sensitivity analysis')
    parser.add_argument('--export', action='store_true', help='Export to Excel')
    parser.add_argument('--output', help='Output filename for Excel export')
    
    args = parser.parse_args()
    
    api_key = args.api_key or get_secret("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("Missing Alpha Vantage API key. Set ALPHAVANTAGE_API_KEY in .streamlit/secrets.toml or pass --api-key.")
        sys.exit(1)
    
    # Initialize DCF analyzer
    dcf_analyzer = DCFAnalyzer(args.ticker, api_key)
    
    # Run DCF analysis
    if not dcf_analyzer.run_full_analysis():
        print("Failed to complete DCF analysis")
        sys.exit(1)
    
    # Print results
    results = dcf_analyzer.dcf_results
    print(f"\n{'='*50}")
    print(f"DCF ANALYSIS RESULTS for {args.ticker}")
    print(f"{'='*50}")
    print(f"Current Stock Price: ${results.current_share_price:.2f}")
    print(f"Implied Share Price: ${results.implied_share_price:.2f}")
    print(f"Upside/(Downside): {results.upside_downside:.1%}")
    print(f"WACC: {results.wacc:.1%}")
    print(f"Enterprise Value: ${results.enterprise_value:,.0f}")
    print(f"Equity Value: ${results.equity_value:,.0f}")
    
    if args.sensitivity:
        print(f"\n{'='*50}")
        print("SENSITIVITY ANALYSIS")
        print(f"{'='*50}")
        
        sensitivity = SensitivityAnalysis(dcf_analyzer)
        sensitivity_table = sensitivity.wacc_terminal_growth_sensitivity()
        print("\nWACC vs Terminal Growth Sensitivity:")
        print(sensitivity_table)
        
        # Monte Carlo simulation
        monte_carlo = sensitivity.monte_carlo_simulation()
        print(f"\nMonte Carlo Simulation (1,000 iterations):")
        print(f"Mean Price: ${monte_carlo['mean']:.2f}")
        print(f"5th Percentile: ${monte_carlo['percentile_5']:.2f}")
        print(f"95th Percentile: ${monte_carlo['percentile_95']:.2f}")
    
    # Export to Excel if requested
    # if args.export:
    #     sensitivity_analyzer = SensitivityAnalysis(dcf_analyzer) if args.sensitivity else None
    #     exporter = DCFExcelExporter(dcf_analyzer, sensitivity_analyzer)
    #     filepath = exporter.export_complete_dcf(args.output)
    #     print(f"\nResults exported to: {filepath}")

if __name__ == "__main__":
    main()