import requests
import pandas as pd
from datetime import datetime
import time
import json
import re

class SECAPIException(Exception):
    pass

def fetch_major_shareholders(ticker, company_name):
    """
    Fetch 13G/13D filings to identify major shareholders
    
    Parameters:
    ticker (str): Company ticker symbol
    company_name (str): Full company name
    
    Returns:
    pandas.DataFrame: Major shareholders data
    """
    
    headers = {
        'User-Agent': 'xhaxhilenzi@gmail.com',  # Replace with your information
        'Accept-Encoding': 'gzip, deflate'
    }
    
    def get_cik(ticker):
        """Get CIK number from ticker"""
        try:
            response = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            companies = response.json()
            for entry in companies.values():
                if entry['ticker'] == ticker.upper():
                    return str(entry['cik_str']).zfill(10)
            raise SECAPIException(f"Could not find CIK for ticker {ticker}")
            
        except Exception as e:
            raise SECAPIException(f"Error fetching CIK: {str(e)}")

    def fetch_ownership_filings(cik):
        """Fetch 13G/13D filings for the company"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            filings = []
            
            if 'filings' in data and 'recent' in data['filings']:
                forms = data['filings']['recent']
                
                # Look for both 13G and 13D filings
                for idx, form_type in enumerate(forms.get('form', [])):
                    if any(f in form_type for f in ['13G', '13D']):
                        filings.append({
                            'form_type': form_type,
                            'filing_date': forms['filingDate'][idx],
                            'accession_number': forms['accessionNumber'][idx],
                            'primary_doc': forms['primaryDocument'][idx]
                        })
            
            return filings
            
        except Exception as e:
            raise SECAPIException(f"Error fetching filings: {str(e)}")

    def process_filing(filing, cik):
        """Extract ownership information from filing"""
        try:
            # Construct document URL
            accession = filing['accession_number'].replace('-', '')
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filing['primary_doc']}"
            
            time.sleep(0.1)  # Respect SEC rate limits
            response = requests.get(doc_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
                
            content = response.text.upper()  # Convert to upper case for easier searching
            
            # Extract ownership information
            ownership_info = {
                'Form Type': filing['form_type'],
                'Filing Date': filing['filing_date'],
                'Document URL': doc_url
            }
            
            # Extract shareholder name
            name_start = content.find('NAME OF REPORTING PERSON')
            if name_start != -1:
                name_end = content.find('\n', name_start)
                ownership_info['Shareholder Name'] = content[name_start:name_end].split('>')[-1].strip()
            
            # Extract ownership percentage
            ownership_start = content.find('PERCENT OF CLASS REPRESENTED')
            if ownership_start != -1:
                ownership_end = content.find('\n', ownership_start)
                percentage_text = content[ownership_start:ownership_end]
                numbers = re.findall(r'\d+\.?\d*', percentage_text)
                if numbers:
                    ownership_info['Ownership %'] = float(numbers[0])
            
            # Extract number of shares
            shares_start = content.find('SHARES BENEFICIALLY OWNED')
            if shares_start != -1:
                shares_end = content.find('\n', shares_start)
                shares_text = content[shares_start:shares_end]
                numbers = re.findall(r'\d+', shares_text)
                if numbers:
                    ownership_info['Shares Owned'] = int(numbers[0])
            
            return ownership_info
            
        except Exception as e:
            print(f"Error processing filing: {str(e)}")
            return None

    # Main execution
    try:
        print(f"Fetching major shareholders for {company_name} ({ticker})...")
        
        cik = get_cik(ticker)
        print(f"Found CIK: {cik}")
        
        filings = fetch_ownership_filings(cik)
        print(f"Found {len(filings)} 13G/13D filings")
        
        ownership_data = []
        for filing in filings:
            print(f"Processing {filing['form_type']} filing from {filing['filing_date']}...")
            result = process_filing(filing, cik)
            if result:
                ownership_data.append(result)
        
        if ownership_data:
            # Create DataFrame and sort by filing date
            df = pd.DataFrame(ownership_data)
            df['Filing Date'] = pd.to_datetime(df['Filing Date'])
            return df.sort_values('Filing Date', ascending=False)
        else:
            print("No ownership data found")
            return pd.DataFrame()
            
    except SECAPIException as e:
        print(f"SEC API Error: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    ticker = "IONQ"
    company_name = "IonQ, Inc."
    
    shareholders = fetch_major_shareholders(ticker, company_name)
    
    if not shareholders.empty:
        print("\nMajor Shareholders for", company_name)
        # Format the display output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(shareholders.to_string(index=False))
        
        # Save to CSV
        output_file = f"{ticker}_major_shareholders.csv"
        shareholders.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
    else:
        print("No major shareholders data found.")