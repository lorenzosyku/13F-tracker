import requests
import pandas as pd

def get_latest_shares_outstanding(cik, email):
    """
    Fetches the latest reported Total Shares Outstanding for a given company CIK.
    """
    headers = {'User-Agent': email}
    sec_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    print(f"📡 Fetching shares outstanding data from: {sec_url}")
    
    response = requests.get(sec_url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch company facts: {response.status_code}")

    company_facts = response.json()

    try:
        # ✅ Extract all reported shares outstanding data
        shares_data = company_facts['facts']['dei']['EntityCommonStockSharesOutstanding']['units']['shares']
        print(f"\n📊 Raw Shares Outstanding Data: {shares_data}")
        # ✅ Convert to DataFrame for easy processing
        shares_df = pd.DataFrame(shares_data)

        # ✅ Sort by 'end' date to get the latest available number
        shares_df = shares_df.sort_values(by="end", ascending=False)

        # ✅ Print all available shares outstanding data
        print("\n📊 Available Shares Outstanding Data:")
        print(shares_df[["val", "end", "form"]])  # Show value, date, and form type

        # ✅ Select the most recent valid entry
        latest_shares_outstanding = shares_df.iloc[0]["val"]
        latest_report_date = shares_df.iloc[0]["end"]
        latest_filing_type = shares_df.iloc[0]["form"]

        print(f"\n✅ Most Recent Shares Outstanding: {latest_shares_outstanding} (Reported on: {latest_report_date}, Filing: {latest_filing_type})")

        return latest_shares_outstanding, latest_report_date, latest_filing_type

    except KeyError:
        print("⚠️ Shares Outstanding data not available.")
        return "N/A", "N/A", "N/A"

# Example usage
if __name__ == "__main__":
    email = "xhaxhilenzi@gmail.com"  # Replace with your SEC-compliant email
    cik = "0001838359"  # Example CIK for Rigetti Computing

    shares_outstanding, report_date, filing_type = get_latest_shares_outstanding(cik, email)

    print("\n📌 Final Shares Outstanding Result:")
    print(f"Shares Outstanding: {shares_outstanding}, Report Date: {report_date}, Filing Type: {filing_type}")
