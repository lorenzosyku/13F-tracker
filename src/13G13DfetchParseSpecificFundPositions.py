# import requests
# import pandas as pd
# from datetime import datetime
# import time
# import json
# import re

# class SECAPIException(Exception):
#     pass

# def fetch_fund_positions(fund_name, tickers):
#     """
#     13D:

#     Filed when an investor acquires more than 5% of a company's   shares with the intent to influence control
#     Must be filed within 10 days of crossing the 5% threshold
#     Provides detailed information about the purpose of the investment and future plans
#     Generally indicates activist investor involvement

#     13G:

#     Similar to 13D but for passive investors who don't intend to  influence company control
#     Also required when acquiring more than 5% ownership
#     Less detailed than 13D as the investment is passive
#     Must be filed within 45 days after year-end (for qualified    institutional investors)



#     ---------------------------------------------------------
#     Fetch 13G/13D filings to identify positions for a specific fund across multiple companies
    
#     Parameters:
#     fund_name (str): Name of the fund to search for (e.g., "VANGUARD GROUP")
#     tickers (list): List of company ticker symbols to search
    
#     Returns:
#     pandas.DataFrame: Fund positions data
#     """
#     headers = {
#         'User-Agent': 'your.email@domain.com',  # Replace with your email
#         'Accept-Encoding': 'gzip, deflate'
#     }
    
#     def get_cik(ticker):
#         """Get CIK number from ticker"""
#         try:
#             response = requests.get(
#                 "https://www.sec.gov/files/company_tickers.json",
#                 headers=headers,
#                 timeout=10
#             )
#             response.raise_for_status()
            
#             companies = response.json()
#             for entry in companies.values():
#                 if entry['ticker'] == ticker.upper():
#                     return str(entry['cik_str']).zfill(10)
#             raise SECAPIException(f"Could not find CIK for ticker {ticker}")
            
#         except Exception as e:
#             raise SECAPIException(f"Error fetching CIK: {str(e)}")

#     def fetch_ownership_filings(cik):
#         """Fetch 13G/13D filings for the company"""
#         try:
#             url = f"https://data.sec.gov/submissions/CIK{cik}.json"
#             response = requests.get(url, headers=headers, timeout=10)
#             response.raise_for_status()
            
#             data = response.json()
#             filings = []
            
#             if 'filings' in data and 'recent' in data['filings']:
#                 forms = data['filings']['recent']
                
#                 for idx, form_type in enumerate(forms.get('form', [])):
#                     if any(f in form_type for f in ['13G', '13D']):
#                         filings.append({
#                             'form_type': form_type,
#                             'filing_date': forms['filingDate'][idx],
#                             'accession_number': forms['accessionNumber'][idx],
#                             'primary_doc': forms['primaryDocument'][idx]
#                         })
            
#             return filings
            
#         except Exception as e:
#             raise SECAPIException(f"Error fetching filings: {str(e)}")

#     def extract_percentage(text):
#         """
#         Enhanced percentage extraction from filing text
#         """
#         # Common patterns for percentage representation in filings
#         patterns = [
#             r'PERCENT OF CLASS REPRESENTED.*?(\d+\.?\d*)%',
#             r'PERCENT OF CLASS REPRESENTED.*?(\d+\.?\d*)\s*PERCENT',
#             r'PERCENTAGE OF CLASS REPRESENTED.*?(\d+\.?\d*)%',
#             r'PERCENTAGE OF CLASS REPRESENTED.*?(\d+\.?\d*)\s*PERCENT',
#             r'AGGREGATE.*?PERCENTAGE.*?(\d+\.?\d*)%',
#             r'AGGREGATE.*?PERCENTAGE.*?(\d+\.?\d*)\s*PERCENT'
#         ]
        
#         # Try each pattern
#         for pattern in patterns:
#             match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
#             if match:
#                 try:
#                     return float(match.group(1))
#                 except ValueError:
#                     continue
        
#         # If no pattern matches, try to find any percentage near relevant keywords
#         relevant_section = re.search(r'(PERCENT OF CLASS|PERCENTAGE OF CLASS|AGGREGATE AMOUNT|BENEFICIAL OWNERSHIP).{0,500}', text, re.DOTALL | re.IGNORECASE)
#         if relevant_section:
#             section_text = relevant_section.group(0)
#             # Find all numbers with decimal points in this section
#             numbers = re.findall(r'(\d+\.?\d*)\s*%', section_text)
#             if numbers:
#                 try:
#                     return float(numbers[0])
#                 except ValueError:
#                     pass
        
#         return None

#     def process_filing(filing, cik, ticker):
#         """Extract ownership information from filing"""
#         try:
#             accession = filing['accession_number'].replace('-', '')
#             doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filing['primary_doc']}"
#             print(f"debugging: {doc_url}...")
#             time.sleep(0.1)  # Respect SEC rate limits
#             response = requests.get(doc_url, headers=headers, timeout=10)
            
#             if response.status_code != 200:
#                 return None
                
#             content = response.text.upper()
#             # print(f"CONTENT debugging: {content}...")
#             # Check if the filing is from the specified fund
#             if fund_name.upper() not in content:
#                 return None
                
#             ownership_info = {
#                 'Ticker': ticker,
#                 'Form Type': filing['form_type'],
#                 'Filing Date': filing['filing_date'],
#                 'Document URL': doc_url
#             }
#             print(f"SECOND debugging: {ownership_info}...")
            
#             # Extract ownership percentage using enhanced method
#             percentage = extract_percentage(content)
#             if percentage is not None:
#                 ownership_info['Ownership %'] = percentage
            
#             # Extract number of shares with enhanced pattern matching
#             shares_patterns = [
#                 r'SHARES BENEFICIALLY OWNED.*?(\d+(?:,\d{3})*)',
#                 r'AGGREGATE.*?SHARES.*?(\d+(?:,\d{3})*)',
#                 r'AMOUNT BENEFICIALLY OWNED.*?(\d+(?:,\d{3})*)'
#             ]
            
#             for pattern in shares_patterns:
#                 shares_match = re.search(pattern, content, re.DOTALL)
#                 if shares_match:
#                     shares_str = shares_match.group(1).replace(',', '')
#                     try:
#                         ownership_info['Shares Owned'] = int(shares_str)
#                         break
#                     except ValueError:
#                         continue
            
#             return ownership_info
            
#         except Exception as e:
#             print(f"Error processing filing: {str(e)}")
#             return None

#     # Main execution
#     all_positions = []
    
#     for ticker in tickers:
#         try:
#             print(f"Fetching positions for {fund_name} in {ticker}...")
            
#             cik = get_cik(ticker)
#             print(f"Found CIK: {cik}")
            
#             filings = fetch_ownership_filings(cik)
#             print(f"Found {len(filings)} 13G/13D filings")
            
#             for filing in filings:
#                 print(f"Processing {filing['form_type']} filing from {filing['filing_date']}...")
#                 result = process_filing(filing, cik, ticker)
#                 if result:
#                     all_positions.append(result)
            
#         except SECAPIException as e:
#             print(f"SEC API Error for {ticker}: {str(e)}")
#             continue
#         except Exception as e:
#             print(f"Unexpected error for {ticker}: {str(e)}")
#             continue
    
#     if all_positions:
#         # Create DataFrame and sort by filing date
#         df = pd.DataFrame(all_positions)
#         df['Filing Date'] = pd.to_datetime(df['Filing Date'])
#         return df.sort_values(['Ticker', 'Filing Date'], ascending=[True, False])
#     else:
#         print(f"No positions found for {fund_name}")
#         return pd.DataFrame()

# # Example usage
# if __name__ == "__main__":
#     fund_name = "Beryl Capital Management LLC"  # Add any fund name you want to search
#     tickers = ["RGTI"]  # Add any tickers you want to search
    
#     positions = fetch_fund_positions(fund_name, tickers)
    
#     if not positions.empty:
#         print(f"\nPositions for {fund_name}:")
#         pd.set_option('display.max_columns', None)
#         pd.set_option('display.width', None)
#         print(positions.to_string(index=False))
        
#         # Save to CSV
#         output_file = f"{fund_name.replace(' ', '_').lower()}_positions.csv"
#         positions.to_csv(output_file, index=False)
#         print(f"\nData saved to {output_file}")
#     else:
#         print(f"No positions found for {fund_name}")

import requests
import pandas as pd
from datetime import datetime
import time
import json
import re
from bs4 import BeautifulSoup

class SECAPIException(Exception):
    pass

def get_cik(ticker):
    """Get CIK number from ticker"""
    headers = {
        'User-Agent': 'your.email@domain.com',  # Replace with your email
        'Accept-Encoding': 'gzip, deflate'
    }
    
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
    """Fetch 13G/13D filings using both current API and archive"""
    headers = {
        'User-Agent': 'your.email@domain.com',  # Replace with your email
        'Accept-Encoding': 'gzip, deflate'
    }
    
    filings = []
    
    # 1. Get recent filings from the new API
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'filings' in data and 'recent' in data['filings']:
            forms = data['filings']['recent']
            for idx, form_type in enumerate(forms.get('form', [])):
                if any(f in form_type for f in ['13G', '13D']):
                    filings.append({
                        'form_type': form_type,
                        'filing_date': forms['filingDate'][idx],
                        'accession_number': forms['accessionNumber'][idx],
                        'primary_doc': forms['primaryDocument'][idx]
                    })
    except Exception as e:
        print(f"Error fetching recent filings: {str(e)}")

    # 2. Get historical filings from EDGAR archive
    current_year = datetime.now().year
    start_year = 2018  # Configurable start year
    
    for year in range(start_year, current_year + 1):
        for quarter in range(1, 5):
            try:
                # Get the company directory listing
                archive_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}"
                response = requests.get(archive_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Find all links that might be accession numbers
                    for link in soup.find_all('a'):
                        accession = link.get('href', '').split('/')[-1]
                        if re.match(r'\d{10}-\d{2}-\d{6}', accession):
                            # Check the filing type
                            try:
                                filing_url = f"{archive_url}/{accession}"
                                filing_response = requests.get(filing_url, headers=headers, timeout=10)
                                filing_soup = BeautifulSoup(filing_response.text, 'html.parser')
                                
                                # Look for 13G/13D indicators
                                filing_type = None
                                filing_date = None
                                
                                for row in filing_soup.find_all('tr'):
                                    cells = row.find_all('td')
                                    for cell in cells:
                                        text = cell.get_text().upper()
                                        if '13G' in text or '13D' in text:
                                            filing_type = text.strip()
                                        if re.match(r'\d{4}-\d{2}-\d{2}', cell.get_text().strip()):
                                            filing_date = cell.get_text().strip()
                                
                                if filing_type and filing_date:
                                    # Find the primary document
                                    primary_doc = None
                                    for doc_link in filing_soup.find_all('a'):
                                        href = doc_link.get('href', '')
                                        if href.endswith('.htm') and not href.endswith('index.htm'):
                                            primary_doc = href.split('/')[-1]
                                            break
                                    
                                    if primary_doc:
                                        filings.append({
                                            'form_type': filing_type,
                                            'filing_date': filing_date,
                                            'accession_number': accession,
                                            'primary_doc': primary_doc
                                        })
                                
                                time.sleep(0.1)  # Respect SEC rate limits
                            except Exception as e:
                                print(f"Error processing archive filing {accession}: {str(e)}")
                                continue
                
                time.sleep(0.1)  # Respect SEC rate limits
            except Exception as e:
                print(f"Error accessing archive for {year} Q{quarter}: {str(e)}")
                continue
    
    return filings

def extract_percentage(text):
    """Extract percentage from filing text with improved footnote handling"""
    patterns = [
        # Handle percentages with footnote references
        r'\(13\).*?Percent.*?Row.*?(\d+\.?\d*)\s*(?:\([0-9]\))?',
        r'Percent of Class.*?:\s*(\d+\.?\d*)\s*(?:\([0-9]\))?',
        r'(\d+\.?\d*)%?\s*(?:\([0-9]\))?\s*$',
        # Original patterns
        r'PERCENT OF CLASS REPRESENTED.*?(\d+\.?\d*)%',
        r'PERCENTAGE OF CLASS REPRESENTED.*?(\d+\.?\d*)%'
    ]
    
    def clean_number(value):
        """Clean and convert extracted number to float"""
        try:
            return float(value.strip('% '))
        except ValueError:
            return None
            
    # First try exact patterns
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            result = clean_number(match.group(1))
            if result is not None and result <= 100:  # Basic validation
                return result
    
    # If no match, try to find percentage in the text
    numbers = re.findall(r'(\d+\.?\d*)\s*%?\s*(?:\([0-9]\))?', text)
    for num in numbers:
        result = clean_number(num)
        if result is not None and result <= 100:
            return result
    
    return None

def extract_shares(text):
    """Extract number of shares with improved footnote handling"""
    patterns = [
        # Handle share counts with footnote references
        r'\(11\).*?Aggregate Amount.*?:\s*(\d+(?:,\d{3})*)\s*(?:\([0-9]\))?',
        r'Aggregate Amount.*?Row.*?11.*?(\d+(?:,\d{3})*)\s*(?:\([0-9]\))?',
        r'(\d+(?:,\d{3})*)\s*(?:\([0-9]\))?\s*$',
        # Original patterns
        r'SHARES BENEFICIALLY OWNED.*?(\d+(?:,\d{3})*)',
        r'AGGREGATE.*?SHARES.*?(\d+(?:,\d{3})*)'
    ]
    
    def clean_number(value):
        """Clean and convert extracted number to integer"""
        try:
            return int(value.replace(',', ''))
        except ValueError:
            return None
    
    # First try exact patterns
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            result = clean_number(match.group(1))
            if result is not None:
                return result
    
    return None

def extract_source_of_funds(text):
    """Extract source of funds information"""
    match = re.search(r'\(4\).*?Source of Funds.*?:\s*(\w+)', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def process_filing(filing, cik, ticker):
    """Process filing with improved handling of different fund types"""
    headers = {
        'User-Agent': 'your.email@domain.com',  # Replace with your email
        'Accept-Encoding': 'gzip, deflate'
    }
    
    try:
        accession = filing['accession_number'].replace('-', '')
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filing['primary_doc']}"
        print(f"Processing: {doc_url}")
        time.sleep(0.1)  # Respect SEC rate limits
        
        response = requests.get(doc_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch document: {doc_url}")
            return None
            
        content = response.text.upper()
        
        # Split content into sections based on CUSIP repeated headers
        sections = re.split(r'CUSIP.*?\d+', content)
        
        results = []
        for section in sections:
            # Look for reporting person name
            name_match = re.search(r'NAME OF REPORTING PERSONS?.*?\n(.*?)\n', section, re.DOTALL)
            if name_match:
                investor_name = name_match.group(1).strip()
                
                # Skip empty or header sections
                if len(investor_name) < 3 or 'NAME OF REPORTING' in investor_name:
                    continue
                
                ownership_info = {
                    'Investor': investor_name,
                    'Ticker': ticker,
                    'Form Type': filing['form_type'],
                    'Filing Date': filing['filing_date'],
                    'Document URL': doc_url
                }
                
                # Extract source of funds
                source_of_funds = extract_source_of_funds(section)
                if source_of_funds:
                    ownership_info['Source of Funds'] = source_of_funds
                
                percentage = extract_percentage(section)
                if percentage is not None:
                    ownership_info['Ownership %'] = percentage
                
                shares = extract_shares(section)
                if shares is not None:
                    ownership_info['Shares Owned'] = shares
                
                # Check for sole/shared voting power
                sole_voting_match = re.search(r'\(7\).*?Sole Voting Power.*?(\d+(?:,\d{3})*)', section, re.DOTALL)
                if sole_voting_match:
                    ownership_info['Sole Voting Power'] = int(sole_voting_match.group(1).replace(',', ''))
                
                shared_voting_match = re.search(r'\(8\).*?Shared Voting Power.*?(\d+(?:,\d{3})*)', section, re.DOTALL)
                if shared_voting_match:
                    ownership_info['Shared Voting Power'] = int(shared_voting_match.group(1).replace(',', ''))
                
                if percentage is not None or shares is not None:
                    results.append(ownership_info)
        
        return results
            
    except Exception as e:
        print(f"Error processing filing: {str(e)}")
        return None

def fetch_fund_positions(fund_name, tickers, start_year=2018):
    """Main function with improved results handling"""
    all_positions = []
    
    for ticker in tickers:
        try:
            print(f"\nFetching positions for {fund_name} in {ticker}...")
            
            cik = get_cik(ticker)
            print(f"Found CIK: {cik}")
            
            filings = fetch_ownership_filings(cik)
            print(f"Found {len(filings)} 13G/13D filings")
            
            for filing in filings:
                results = process_filing(filing, cik, ticker)
                if results:
                    all_positions.extend(results)
                    print(f"Successfully processed {filing['form_type']} filing from {filing['filing_date']}")
            
        except SECAPIException as e:
            print(f"SEC API Error for {ticker}: {str(e)}")
            continue
        except Exception as e:
            print(f"Unexpected error for {ticker}: {str(e)}")
            continue
    
    if all_positions:
        df = pd.DataFrame(all_positions)
        df['Filing Date'] = pd.to_datetime(df['Filing Date'])
        return df.sort_values(['Ticker', 'Filing Date', 'Investor'], ascending=[True, False, True])
    else:
        print(f"No positions found for {fund_name}")
        return pd.DataFrame()

# Example usage
if __name__ == "__main__":
    fund_name = "VANGUARD GROUP INC"
    tickers = ["PLTR"]
    positions = fetch_fund_positions(fund_name, tickers)
    print(positions)
    
    if not positions.empty:
        print(f"\nPositions found:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(positions.to_string(index=False))
        
        # Save to CSV
        output_file = f"{fund_name.replace(' ', '_').lower()}_positions.csv"
        positions.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
    else:
        print("No positions found")