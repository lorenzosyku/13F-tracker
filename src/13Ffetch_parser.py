

import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from datetime import datetime

def get_13f_holdings(cik, accession_number, email):
    """
    Fetch and parse 13F holdings from a specific SEC filing.

    Parameters:
    cik (str): Company CIK
    accession_number (str): Filing accession number
    email (str): Email for SEC request header

    Returns:
    tuple: (pandas.DataFrame, dict) containing holding information and filing metadata
    """
    headers = {'User-Agent': email}
    accession_number = accession_number.replace('-', '')
    cik = str(cik).zfill(10)
    base_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}"
    
    try:
        # Fetch index.json for filing metadata
        index_url = f"{base_url}/index.json"
        index_response = requests.get(index_url, headers=headers)
        if index_response.status_code != 200:
            raise ValueError(f"Failed to fetch index: {index_response.status_code}")
        
        index_data = index_response.json()
        
        # Get filing date from the last-modified field of the first item
        filing_date = index_data['directory']['item'][0]['last-modified'].split(' ')[0]
        
        # Extract filing metadata
        filing_metadata = {
            'filing_date': filing_date,
            'accession_number': accession_number,
            'cik': cik
        }
        
        print(f"\n📅 Filing Date: {filing_date}")
        print("\nAvailable files in index:")
        for file in index_data['directory']['item']:
            print(f"- {file['name']}")

        # Try each XML file to find one containing <infoTable>
        xml_file = None
        xml_content = None
        for file in index_data['directory']['item']:
            if file['name'].endswith('.xml'):
                xml_url = f"{base_url}/{file['name']}"
                xml_response = requests.get(xml_url, headers=headers)
                
                if xml_response.status_code == 200:
                    print(f"\nTrying XML file: {file['name']}")
                    if "<infoTable" in xml_response.text:
                        xml_file = file['name']
                        xml_content = xml_response.content
                        print(f"\n✅ Using XML file: {xml_file}")
                        break  # Stop at first valid XML file

        if not xml_file:
            raise ValueError("No XML file found with <infoTable> elements")

        root = ET.fromstring(xml_content)

        # Detect namespace
        namespace = ''
        if root.tag.startswith('{'):
            namespace = root.tag.split('}')[0] + '}'

        holdings = []
        for info_table in root.findall(f'.//{namespace}infoTable'):
            holding = {
                'nameOfIssuer': info_table.findtext(f'{namespace}nameOfIssuer'),
                'titleOfClass': info_table.findtext(f'{namespace}titleOfClass'),
                'cusip': info_table.findtext(f'{namespace}cusip'),
                'value': int(info_table.findtext(f'{namespace}value', '0')),
                'shares': int(info_table.findtext(f'{namespace}shrsOrPrnAmt/{namespace}sshPrnamt', '0')),
                'shareType': info_table.findtext(f'{namespace}shrsOrPrnAmt/{namespace}sshPrnamtType'),
                'investmentDiscretion': info_table.findtext(f'{namespace}investmentDiscretion')
            }
            holdings.append(holding)

        if not holdings:
            raise ValueError("No holdings data found in XML")

        holdings_df = pd.DataFrame(holdings)
        holdings_df['filingCik'] = cik
        holdings_df['accessionNumber'] = accession_number
        holdings_df['filingDate'] = filing_date
        holdings_df['portfolioPercent'] = (holdings_df['value'] / holdings_df['value'].sum() * 100).round(4)
        holdings_df = holdings_df.sort_values('value', ascending=False)

        return holdings_df, filing_metadata

    except Exception as e:
        print(f"\n⚠️ Error fetching holdings: {str(e)}")
        return pd.DataFrame(), None

# Example usage
if __name__ == "__main__":
    email = "xhaxhilenzi@gmail.com"  # Replace with your email
    cik = "0001067983"  # Example: Berkshire Hathaway
    accession_number = "0000950123-24-011775"

    holdings_df, filing_metadata = get_13f_holdings(cik, accession_number, email)

    if not holdings_df.empty:
        print("\n📄 Filing Information:")
        print(f"Filing Date: {filing_metadata['filing_date']}")
        print(f"CIK: {filing_metadata['cik']}")
        print(f"Accession Number: {filing_metadata['accession_number']}")
        
        print("\n📊 Top 10 holdings by value:")
        print(holdings_df[['nameOfIssuer', 'shares', 'value', 'portfolioPercent']].head(21))
        
        print("\n📈 Portfolio Summary:")
        print(f"Total Positions: {len(holdings_df)}")
        print(f"Total Value: ${holdings_df['value'].sum():,.0f}")