import requests
import pandas as pd
import csv
import sys
from datetime import datetime

def get_shares_outstanding(cik, output_filename='shares_outstanding.csv'):
    """
    Fetches all common shares outstanding data for a given CIK number
    and saves it to a CSV file.
    
    Parameters:
    cik (str): The CIK number of the company (without leading zeros)
    output_filename (str): The name of the output CSV file
    
    Returns:
    pandas.DataFrame: DataFrame containing the shares outstanding data
    """
    # Ensure CIK is properly formatted (remove leading zeros)
    # cik = cik.lstrip('0')
    
    # Create request header (SEC requires a user-agent with email)
    headers = {'User-Agent': "your_email@example.com"}  # Replace with your email
    
    try:
        # Request company facts data from SEC API
        response = requests.get(
            f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
            headers=headers
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        company_data = response.json()
        
        # Extract company name
        company_name = company_data.get('entityName', f'CIK{cik}')
        print(f"Retrieving data for: {company_name}")
        
        # Check if common shares outstanding data exists
        if 'CommonStockSharesOutstanding' not in company_data.get('facts', {}).get('us-gaap', {}):
            # Try alternative field if CommonStockSharesOutstanding doesn't exist
            if 'SharesOutstanding' in company_data.get('facts', {}).get('us-gaap', {}):
                shares_data = company_data['facts']['us-gaap']['SharesOutstanding']
                print("Using 'SharesOutstanding' field instead of 'CommonStockSharesOutstanding'")
            else:
                raise KeyError("Could not find shares outstanding data for this company")
        else:
            shares_data = company_data['facts']['us-gaap']['CommonStockSharesOutstanding']
        
        # Check which unit the shares are reported in (typically 'shares')
        if 'units' not in shares_data:
            raise KeyError("No units found in shares data")
        
        # Get the unit key (usually 'shares')
        unit_key = list(shares_data['units'].keys())[0]
        entries = shares_data['units'][unit_key]
        
        # Prepare data for DataFrame
        data = []
        for entry in entries:
            # Extract relevant fields
            record = {
                'end_date': entry.get('end', 'N/A'),
                'shares_outstanding': entry.get('val', 'N/A'),
                'form': entry.get('form', 'N/A'),
                'filed_date': entry.get('filed', 'N/A'),
                'fiscal_year': entry.get('fy', 'N/A'),
                'fiscal_period': entry.get('fp', 'N/A'),
                'accn': entry.get('accn', 'N/A')
            }
            data.append(record)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by end_date (chronological order)
        df = df.sort_values('end_date')
        
        # Format shares as integers with commas
        df['shares_outstanding_formatted'] = df['shares_outstanding'].apply(
            lambda x: f"{int(x):,}" if isinstance(x, (int, float)) else x
        )
        
        # Save to CSV
        df.to_csv(output_filename, index=False)
        print(f"Data saved to {output_filename}")
        
        return df
    
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response.status_code == 404:
            print(f"CIK {cik} not found. Please check the CIK number.")
    except KeyError as e:
        print(f"Data Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return None

if __name__ == "__main__":
    # If script is run directly, can take CIK as command line argument
    if len(sys.argv) > 1:
        cik = sys.argv[1]
        output_file = f"shares_outstanding_CIK{cik}_{datetime.now().strftime('%Y%m%d')}.csv"
        get_shares_outstanding(cik, output_file)
    else:
        # Example usage (ZURA BIO LD)
        cik = "0001855644"
        get_shares_outstanding(cik)