

import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
from datetime import datetime

def get_form4_transactions(cik, accession_number, email):
    """
    Fetch and parse Form 4 insider trading data with added debugging information.
    """
    headers = {'User-Agent': email}
    accession_number = accession_number.replace('-', '')
    cik = str(cik).zfill(10)
    base_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}"
    
    try:
        time.sleep(0.1)

        index_url = f"{base_url}/index.json"
        print(f"\nTrying to fetch index from: {index_url}")
        index_response = requests.get(index_url, headers=headers)
        print(f"Index response status: {index_response.status_code}")
        
        if index_response.status_code != 200:
            print(f"Index response content: {index_response.text[:500]}")
            raise ValueError(f"Failed to fetch index: {index_response.status_code}")
        
        index_data = index_response.json()
        print("\nAvailable files in directory:")
        for file in index_data['directory']['item']:
            print(f"- {file['name']}")
            
        filing_date = index_data['directory']['item'][0]['last-modified'].split(' ')[0]
        
        xml_file = None
        xml_content = None
        for file in index_data['directory']['item']:
            if file['name'].endswith('.xml'):
                xml_url = f"{base_url}/{file['name']}"
                print(f"\nTrying to fetch XML from: {xml_url}")
                xml_response = requests.get(xml_url, headers=headers)
                print(f"XML response status: {xml_response.status_code}")
                
                if xml_response.status_code == 200:
                    xml_content = xml_response.content
                    xml_file = file['name']
                    break

        if not xml_file:
            raise ValueError("No XML file found")

        # ✅ Parse the XML and return a DataFrame
        root = ET.fromstring(xml_content)
        transactions = []
        
        for txn in root.findall(".//nonDerivativeTransaction"):
            try:
                security_title = txn.findtext("securityTitle/value", "N/A")
                transaction_date = txn.findtext("transactionDate/value", "N/A")
                transaction_code = txn.findtext("transactionCoding/transactionCode", "N/A")
                transaction_shares = txn.findtext("transactionAmounts/transactionShares/value", "0")
                transaction_price = txn.findtext("transactionAmounts/transactionPricePerShare/value", "0")
                
                transactions.append({
                    "Security Title": security_title,
                    "Transaction Date": transaction_date,
                    "Transaction Code": transaction_code,
                    "Transaction Shares": transaction_shares,
                    "Transaction Price": transaction_price
                })
            except Exception as e:
                print(f"⚠️ Error parsing transaction: {e}")
        
        df = pd.DataFrame(transactions)

        # ✅ Always return a tuple
        metadata = {"filing_date": filing_date, "xml_file": xml_file}
        print(xml_content.decode())
        return df, metadata

    except Exception as e:
        print(f"\n⚠️ Error fetching Form 4: {str(e)}")
        return pd.DataFrame(), None  # Ensure function always returns a tuple

# Example usage
if __name__ == "__main__":
    email = "xhaxhilenzi@gmail.com"  # Replace with your email
    cik = "0001838359"
    accession_number = "0001415889-24-029293"

    print(f"\nFetching Form 4 for:")
    print(f"CIK: {cik}")
    print(f"Accession: {accession_number}")
    
    tx_df, metadata = get_form4_transactions(cik, accession_number, email)
    print("\nParsed Transactions:")
    print(tx_df)
    print("\nMetadata:", metadata)
