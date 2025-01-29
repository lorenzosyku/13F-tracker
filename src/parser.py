import xml.etree.ElementTree as ET
import pandas as pd
import os

def parse_13f_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Namespace handling (SEC XML uses namespaces)
    ns = {'ns': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
    
    holdings = []
    for entry in root.findall('.//ns:infoTable', ns):
        data = {
            'name': entry.find('ns:nameOfIssuer', ns).text,
            'ticker': entry.find('ns:ticker', ns).text,
            'value': int(entry.find('ns:value', ns).text),
            'shares': int(entry.find('ns:shrsOrPrnAmt/ns:sshPrnamt', ns).text)
        }
        holdings.append(data)
    
    return pd.DataFrame(holdings)

def parse_all_filings(data_dir="data/raw"):
    all_dfs = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".xml"):
            xml_path = os.path.join(data_dir, filename)
            df = parse_13f_xml(xml_path)
            df['filing_date'] = filename.split("_")[1]  # Extract date from filename
            all_dfs.append(df)
    
    return pd.concat(all_dfs)

# Example usage:
if __name__ == "__main__":
    df = parse_all_filings()
    df.to_csv("data/parsed_holdings.csv", index=False)