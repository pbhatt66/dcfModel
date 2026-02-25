from config import get_secret
from dcf import DCFAnalyzer
from sensitivityAnalysis import SensitivityAnalysis
# from excel_exporter import DCFExcelExporter

def main():
    # Configuration
    api_key = get_secret("ALPHAVANTAGE_API_KEY")
    ticker = "GOOGL"

    if not api_key:
        print("Missing Alpha Vantage API key. Set ALPHAVANTAGE_API_KEY in .streamlit/secrets.toml.")
        return
    
    # Initialize and run DCF analysis
    dcf_analyzer = DCFAnalyzer(ticker, api_key)
    
    if dcf_analyzer.run_full_analysis():
        # Print results
        results = dcf_analyzer.dcf_results
        print(f"\nDCF Analysis Results for {ticker}:")
        print(f"Current Price: ${results.current_share_price:.2f}")
        print(f"Implied Price: ${results.implied_share_price:.2f}")
        print(f"Upside/Downside: {results.upside_downside:.1%}")
        
        # Run sensitivity analysis
        sensitivity = SensitivityAnalysis(dcf_analyzer)
        sensitivity_table = sensitivity.wacc_terminal_growth_rate_sensitivity()
        print("\nSensitivity Analysis:")
        print(sensitivity_table)
        
        # # Export to Excel
        # exporter = DCFExcelExporter(dcf_analyzer, sensitivity)
        # exporter.export_complete_dcf()
        
        print("\nAnalysis complete!")
    else:
        print("Failed to complete analysis")

if __name__ == "__main__":
    main()