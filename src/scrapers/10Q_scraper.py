import requests
import pandas as pd

def get_company_financials(ticker, email):
    """
    Fetches the latest financial data for a given company (by ticker) from SEC's XBRL API.
    Returns recent 10-Q filing metadata and key financial metrics.
    """
    headers = {'User-Agent': email}

    # Step 1: Get all company tickers
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    tickers_response = requests.get(tickers_url, headers=headers)
    tickers_data = tickers_response.json()

    # Convert to DataFrame
    tickers_df = pd.DataFrame.from_dict(tickers_data, orient="index")

    # Find the CIK for the given ticker
    company = tickers_df[tickers_df['ticker'] == ticker.upper()]
    if company.empty:
        raise ValueError(f"Ticker '{ticker}' not found in SEC database.")

    cik = str(company.iloc[0]['cik_str']).zfill(10)  # Ensure 10-digit CIK

    print(f"🔍 Found CIK: {cik} for {ticker.upper()}")

    # Step 2: Fetch recent filings
    filings_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    filings_response = requests.get(filings_url, headers=headers)
    filings_data = filings_response.json()

    # Extract latest 10-Q
    filings_df = pd.DataFrame.from_dict(filings_data['filings']['recent'])
    filings_10q = filings_df[filings_df['form'] == "10-Q"]

    if filings_10q.empty:
        raise ValueError(f"No recent 10-Q filings found for {ticker.upper()}.")

    latest_10q = filings_10q.iloc[0]
    accession_number = latest_10q['accessionNumber'].replace("-", "")
    report_date = latest_10q['reportDate']

    print(f"📄 Latest 10-Q found: {accession_number} (Report Date: {report_date})")

    # Step 3: Get financial data using SEC XBRL API
    company_facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    company_facts_response = requests.get(company_facts_url, headers=headers)
    company_facts_data = company_facts_response.json()



    # Financial metrics to extract
    metrics = {
        "Total Assets": "Assets",
        "Total Liabilities": "Liabilities",
        "Shareholders' Equity": "StockholdersEquity",
        "Revenue": "Revenues",
        "Net Income": "NetIncomeLoss",
        "Operating Income": "OperatingIncomeLoss",
        "Gross Profit": "GrossProfit",
        "EBIT": "EarningsBeforeInterestAndTaxes",
        "EBITDA": "EarningsBeforeInterestTaxesDepreciationAndAmortization",
        "EPS (Basic)": "EarningsPerShareBasic",
        "EPS (Diluted)": "EarningsPerShareDiluted",
        "Operating Cash Flow": "NetCashProvidedByUsedInOperatingActivities",
        "Capital Expenditures": "PaymentsToAcquirePropertyPlantAndEquipment",
    }

    financials = {}

    for label, key in metrics.items():
        try:
            data_points = company_facts_data['facts']['us-gaap'][key]['units']['USD']
            latest_value = data_points[0]['val']  # Most recent value
            financials[label] = latest_value
        except KeyError:
            financials[label] = "N/A"  # Some companies may not report all metrics

    # Calculate Free Cash Flow (FCF) if both values exist
    if financials["Operating Cash Flow"] != "N/A" and financials["Capital Expenditures"] != "N/A":
        financials["Free Cash Flow"] = financials["Operating Cash Flow"] - financials["Capital Expenditures"]
    else:
        financials["Free Cash Flow"] = "N/A"

    # Convert to DataFrame
    financials_df = pd.DataFrame([financials])

    return financials_df, {
        "CIK": cik,
        "Ticker": ticker.upper(),
        "Latest 10-Q Accession": accession_number,
        "Report Date": report_date
    }

# Example usage
if __name__ == "__main__":
    email = "your.email@example.com"  # Replace with your SEC-compliant email
    ticker = "ZURA"  # Example ticker (Rigetti Computing)

    print(f"\nFetching financial data for {ticker.upper()}...")
    
    financials_df, metadata = get_company_financials(ticker, email)

    print("\n📊 Company Info:")
    print(metadata)

    print("\n💰 Financial Data:")
    print(financials_df)
