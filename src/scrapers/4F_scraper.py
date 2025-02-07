# Description: Fetch and parse Form 4 insider trading data from the SEC website.
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time

def get_form4_transactions(cik, accession_number, email):
    """
    Fetch and parse Form 4 insider trading data, extracting issuer, reporting owner details,
    relationships, non-derivative transactions, and derivative transactions.
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
        
        if index_response.status_code != 200:
            raise ValueError(f"Failed to fetch index: {index_response.status_code}")
        
        index_data = index_response.json()
        filing_date = index_data['directory']['item'][0]['last-modified'].split(' ')[0]
        
        # Find the XML file
        xml_file = None
        xml_content = None
        for file in index_data['directory']['item']:
            if file['name'].endswith('.xml'):
                xml_url = f"{base_url}/{file['name']}"
                print(f"\nFetching XML from: {xml_url}")
                xml_response = requests.get(xml_url, headers=headers)
                
                if xml_response.status_code == 200:
                    xml_content = xml_response.content
                    xml_file = file['name']
                    break

        if not xml_file:
            raise ValueError("No XML file found")

        # ✅ Parse XML
        root = ET.fromstring(xml_content)

        # 🔹 Issuer Details
        issuer_details = {
            "Issuer CIK": root.findtext("issuer/issuerCik", "N/A"),
            "Issuer Name": root.findtext("issuer/issuerName", "N/A"),
            "Trading Symbol": root.findtext("issuer/issuerTradingSymbol", "N/A")
        }

        # 🔹 Reporting Owner Details
        reporting_owner = {
            "Owner CIK": root.findtext("reportingOwner/reportingOwnerId/rptOwnerCik", "N/A"),
            "Owner Name": root.findtext("reportingOwner/reportingOwnerId/rptOwnerName", "N/A"),
            "Owner Street": root.findtext("reportingOwner/reportingOwnerAddress/rptOwnerStreet1", "N/A"),
            "City": root.findtext("reportingOwner/reportingOwnerAddress/rptOwnerCity", "N/A"),
            "State": root.findtext("reportingOwner/reportingOwnerAddress/rptOwnerState", "N/A"),
            "Zip Code": root.findtext("reportingOwner/reportingOwnerAddress/rptOwnerZipCode", "N/A")
        }

        # 🔹 Relationship to Issuer
        relationship = {
            "Is Director": root.findtext("reportingOwner/reportingOwnerRelationship/isDirector", "false"),
            "Is Officer": root.findtext("reportingOwner/reportingOwnerRelationship/isOfficer", "false"),
            "Is Ten Percent Owner": root.findtext("reportingOwner/reportingOwnerRelationship/isTenPercentOwner", "false"),
            "Officer Title": root.findtext("reportingOwner/reportingOwnerRelationship/officerTitle", "N/A")
        }

        # 🔹 Non-Derivative Transactions (Regular Stock Trades)
        non_derivative_transactions = []
        for txn in root.findall(".//nonDerivativeTransaction"):
            non_derivative_transactions.append({
                "Security Title": txn.findtext("securityTitle/value", "N/A"),
                "Transaction Date": txn.findtext("transactionDate/value", "N/A"),
                "Transaction Code": txn.findtext("transactionCoding/transactionCode", "N/A"),
                "Shares Traded": txn.findtext("transactionAmounts/transactionShares/value", "0"),
                "Price per Share": txn.findtext("transactionAmounts/transactionPricePerShare/value", "0"),
                "Transaction Type": txn.findtext("transactionAmounts/transactionAcquiredDisposedCode/value", "N/A"),
                "Shares Owned After": txn.findtext("postTransactionAmounts/sharesOwnedFollowingTransaction/value", "0"),
                "Ownership Type": txn.findtext("ownershipNature/directOrIndirectOwnership/value", "N/A")
            })

        # 🔹 Derivative Transactions (Options, Warrants, etc.)
        derivative_transactions = []
        for txn in root.findall(".//derivativeTransaction"):
            derivative_transactions.append({
                "Security Title": txn.findtext("securityTitle/value", "N/A"),
                "Exercise Price": txn.findtext("conversionOrExercisePrice/value", "0"),
                "Transaction Date": txn.findtext("transactionDate/value", "N/A"),
                "Transaction Code": txn.findtext("transactionCoding/transactionCode", "N/A"),
                "Shares Traded": txn.findtext("transactionAmounts/transactionShares/value", "0"),
                "Price per Share": txn.findtext("transactionAmounts/transactionPricePerShare/value", "0"),
                "Transaction Type": txn.findtext("transactionAmounts/transactionAcquiredDisposedCode/value", "N/A"),
                "Expiration Date": txn.findtext("expirationDate/value", "N/A"),
                "Underlying Security": txn.findtext("underlyingSecurity/underlyingSecurityTitle/value", "N/A"),
                "Underlying Shares": txn.findtext("underlyingSecurity/underlyingSecurityShares/value", "0"),
                "Shares Owned After": txn.findtext("postTransactionAmounts/sharesOwnedFollowingTransaction/value", "0"),
                "Ownership Type": txn.findtext("ownershipNature/directOrIndirectOwnership/value", "N/A")
            })

        # Convert transaction lists to DataFrames
        non_derivative_df = pd.DataFrame(non_derivative_transactions)
        derivative_df = pd.DataFrame(derivative_transactions)

        # ✅ Return all data
        metadata = {
            "filing_date": filing_date,
            "xml_file": xml_file,
            "issuer": issuer_details,
            "reporting_owner": reporting_owner,
            "relationship": relationship
        }

        return non_derivative_df, derivative_df, metadata

    except Exception as e:
        print(f"\n⚠️ Error fetching Form 4: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), None  # Always return a tuple

# Example usage
if __name__ == "__main__":
    email = "xhaxhilenzi@gmail.com"  # Replace with your email
    cik = "0001838359" # Example CIK for Rigetti Computing
    accession_number = "0001415889-24-029293"

    print(f"\nFetching Form 4 for:")
    print(f"CIK: {cik}")
    print(f"Accession: {accession_number}")
    
    non_derivative_df, derivative_df, metadata = get_form4_transactions(cik, accession_number, email)

    print("\n📌 Issuer Details:")
    print(metadata["issuer"])

    print("\n👤 Reporting Owner Details:")
    print(metadata["reporting_owner"])

    print("\n🔗 Relationship to Issuer:")
    print(metadata["relationship"])

    print("\n📈 Non-Derivative Transactions:")
    print(non_derivative_df)

    print("\n📉 Derivative Transactions:")
    print(derivative_df)

    print("\n🗂 Metadata:", metadata)
