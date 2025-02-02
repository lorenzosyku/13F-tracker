import requests
import pandas as pd
from datetime import datetime

def fetch_13f_filings(email, max_companies=None):
    """
    Fetch 13F-HR filings from SEC EDGAR
    
    Parameters:
    email (str): Email for SEC request header
    max_companies (int): Optional limit on number of companies to process
    
    Returns:
    pandas.DataFrame: DataFrame containing 13F-HR filing information
    """
    # Create request header
    headers = {'User-Agent': email}
    
    # Get all companies data
    companyTickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
    )
    
    # Convert to dataframe
    companyData = pd.DataFrame.from_dict(companyTickers.json(), orient='index')
    
    # Add leading zeros to CIK
    companyData['cik_str'] = companyData['cik_str'].astype(str).str.zfill(10)
    
    if max_companies:
        companyData = companyData.head(max_companies)
    
    all_13f_filings = []
    
    # Process each company
    for idx, row in companyData.iterrows():
        try:
            # Get company specific filing metadata
            filingMetadata = requests.get(
                f'https://data.sec.gov/submissions/CIK{row["cik_str"]}.json',
                headers=headers
            )
            
            if filingMetadata.status_code != 200:
                print(f"Failed to fetch data for {row['title']}: {filingMetadata.status_code}")
                continue
                
            # Convert to dataframe
            recent_filings = pd.DataFrame.from_dict(
                filingMetadata.json()['filings']['recent']
            )
            
            # Filter for 13F-HR filings only
            thirteen_f_filings = recent_filings[
                recent_filings['form'].isin(['13F-HR', '13F-HR/A'])
            ].copy()
            
            if len(thirteen_f_filings) > 0:
                # Add company information
                thirteen_f_filings['company_name'] = row['title']
                thirteen_f_filings['ticker'] = row['ticker']
                thirteen_f_filings['cik'] = row['cik_str']
                
                # Add to our collection
                all_13f_filings.append(thirteen_f_filings)
                
                print(f"Found {len(thirteen_f_filings)} 13F-HR filings for {row['title']}")
        
        except Exception as e:
            print(f"Error processing {row['title']}: {str(e)}")
            continue
    
    if not all_13f_filings:
        return pd.DataFrame()
    
    # Combine all filings
    combined_filings = pd.concat(all_13f_filings, ignore_index=True)
    
    # Clean up the data
    combined_filings['reportDate'] = pd.to_datetime(combined_filings['reportDate'])
    combined_filings['filingDate'] = pd.to_datetime(combined_filings['filingDate'])
    
    # Select and reorder relevant columns
    relevant_columns = [
        'company_name', 'ticker', 'cik', 'form', 'reportDate', 'filingDate',
        'accessionNumber', 'primaryDocument', 'fileNumber'
    ]
    
    final_df = combined_filings[relevant_columns].sort_values(
        ['reportDate', 'company_name'], 
        ascending=[False, True]
    )
    
    return final_df

def get_filing_url(cik, accession_number):
    """
    Generate the SEC EDGAR URL for a specific filing
    
    Parameters:
    cik (str): Company CIK
    accession_number (str): Filing accession number
    
    Returns:
    str: URL to the filing
    """
    accession_number = accession_number.replace('-', '')
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}"

# Example usage:
if __name__ == "__main__":
    email = "xhaxhilenzi@gmail.com"  # Replace with your email
    
    # Fetch filings (optionally limit to first 10 companies for testing)
    filings_df = fetch_13f_filings(email, max_companies=10)
    
    if not filings_df.empty:
        print("\nMost recent 13F-HR filings:")
        print(filings_df.head())
        
        # Example of generating a filing URL
        sample_filing = filings_df.iloc[0]
        url = get_filing_url(sample_filing['cik'], sample_filing['accessionNumber'])
        print(f"\nSample filing URL: {url}")