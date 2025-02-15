""""13F-HR:

    Filed quarterly by institutional investment managers with over $100 million in assets
    Shows all long positions in US-listed stocks, certain options, and convertible bonds
    Must be filed within 45 days after the quarter ends
    Most useful for tracking hedge fund equity holdings, as it provides a comprehensive view of long positions
    Limitations: Doesn't show short positions or non-US securities"""

import requests
import pandas as pd
from datetime import datetime
import time
import json
import re
from bs4 import BeautifulSoup

class SECAPIException(Exception):
    pass

def fetch_fund_filings_and_holdings(fund_name):
    """
    Fetch all 13F-HR filings and holdings for a specific fund
    
    Parameters:
    fund_name (str): Name of the fund to search for (e.g., "VANGUARD GROUP")
    
    Returns:
    pandas.DataFrame: Fund filings and holdings data
    """
    headers = {
        'User-Agent': 'your.email@domain.com',  # Replace with your email
        'Accept-Encoding': 'gzip, deflate'
    }
    
    def get_fund_cik(fund_name):
        """Get CIK number for the fund"""
        try:
            response = requests.get(
                "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            for line in response.text.splitlines():
                if fund_name.upper() in line.upper():
                    cik_match = re.search(r'(\d{10})', line)
                    if cik_match:
                        return cik_match.group(1)
                    cik = line.split(':')[0].strip()
                    return re.sub(r'\D', '', cik).zfill(10)
                    
            raise SECAPIException(f"Could not find CIK for fund {fund_name}")
            
        except Exception as e:
            raise SECAPIException(f"Error fetching fund CIK: {str(e)}")

    def fetch_13f_filings(cik):
        """Fetch all 13F-HR filings for the fund"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            filings = []
            
            if 'filings' in data and 'recent' in data['filings']:
                forms = data['filings']['recent']
                
                for idx, form_type in enumerate(forms.get('form', [])):
                    if form_type == '13F-HR':
                        filings.append({
                            'filing_date': forms['filingDate'][idx],
                            'accession_number': forms['accessionNumber'][idx],
                            'primary_doc': forms['primaryDocument'][idx]
                        })
            
            return filings
            
        except Exception as e:
            raise SECAPIException(f"Error fetching filings: {str(e)}")

    def process_13f_filing(filing, cik):
        """Extract all holdings information from 13F-HR filing"""
        try:
            accession = filing['accession_number'].replace('-', '')
            info_table_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/infotable.xml"
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filing['primary_doc']}"
            
            time.sleep(0.1)  # Respect SEC rate limits
            response = requests.get(info_table_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
                
            # Parse XML content
            soup = BeautifulSoup(response.content, 'xml')
            holdings = []
            
            # Find all information table entries
            for entry in soup.find_all('infoTable'):
                name_of_issuer = entry.find('nameOfIssuer')
                shares = entry.find('sshPrnamt')
                
                if name_of_issuer and shares:
                    holdings.append({
                        'Filing Date': filing['filing_date'],
                        'Filing URL': filing_url,
                        'Company Name': name_of_issuer.text.strip(),
                        'Shares': int(shares.text.strip())
                    })
            
            return holdings
            
        except Exception as e:
            print(f"Error processing filing: {str(e)}")
            return []

    # Main execution
    all_holdings = []
    
    try:
        fund_cik = get_fund_cik(fund_name)
        print(f"Found CIK for {fund_name}: {fund_cik}")
        
        filings = fetch_13f_filings(fund_cik)
        print(f"Found {len(filings)} 13F-HR filings")
        
        for filing in filings:
            print(f"Processing 13F-HR filing from {filing['filing_date']}...")
            holdings = process_13f_filing(filing, fund_cik)
            all_holdings.extend(holdings)
            
    except SECAPIException as e:
        print(f"SEC API Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    if all_holdings:
        # Create DataFrame and sort by filing date
        df = pd.DataFrame(all_holdings)
        df['Filing Date'] = pd.to_datetime(df['Filing Date'])
        return df.sort_values(['Filing Date', 'Company Name'], ascending=[False, True])
    else:
        print(f"No holdings found for {fund_name}")
        return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    fund_name = "TWO SIGMA INVESTMENTS, LP"
    
    holdings = fetch_fund_filings_and_holdings(fund_name)
    
    if not holdings.empty:
        print(f"\nHoldings for {fund_name}:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(holdings.head().to_string(index=False))
        
        output_file = f"{fund_name.replace(' ', '_').lower()}_all_13f_holdings.csv"
        holdings.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
    else:
        print(f"No holdings found for {fund_name}")