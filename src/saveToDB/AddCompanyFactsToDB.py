import requests
import json
from firebase_admin import credentials, firestore, initialize_app
import os

def generate_edgar_url(cik, accession_number, form_type):
    """Generate SEC EDGAR URL for the filing."""
    # Remove dashes from accession number if present
    accession_clean = accession_number.replace('-', '')
    
    # Base URL for document views
    view_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession_number}-index.htm"
    
    # Interactive URL for certain forms (10-K, 10-Q, 8-K)
    interactive_forms = ['10-K', '10-Q', '8-K']
    interactive_url = f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik}/{accession_clean}/{accession_number}.htm" if form_type in interactive_forms else None
    
    return {
        "view_url": view_url,
        "interactive_url": interactive_url
    }

def fetch_and_store_sec_data(cik):
    # Get the directory where your script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_account_path = os.path.join(current_dir, 'serviceAccount.json')
    
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate(service_account_path)
    initialize_app(cred)
    
    # Initialize Firestore client
    db = firestore.client()
    
    # Strip leading zeros from CIK for URLs
    cik_stripped = cik.lstrip('0')
    
    # Define headers
    headers = {
        "User-Agent": "xhaxhilenzi@gmail.com"
    }
    
    # Fetch company facts data
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=headers)
    
    # Check response status
    if response.status_code == 200:
        data = response.json()
        batch = db.batch()
        
        # Create a collection reference
        collection_ref = db.collection(f'sec_data_{cik}')
        
        # Track processed labels to merge data for same metrics
        processed_data = {}
        
        for taxonomy, items in data.get("facts", {}).items():
            for metric, details in items.items():
                # Use metric as fallback if label is None
                label = details.get("label") or metric
                description = details.get('description') or metric
                
                # Skip if we somehow still have a None label
                if label is None:
                    print(f"Skipping entry with None label in taxonomy {taxonomy}")
                    continue
                
                if label not in processed_data:
                    processed_data[label] = {
                        'description': description,
                        'units': {}
                    }
                
                # Process all units and their values
                for unit, values in details.get("units", {}).items():
                    if unit not in processed_data[label]['units']:
                        processed_data[label]['units'][unit] = []
                    
                    # Add all entries for this unit
                    for entry in values:
                        # Get accession number from the filing data
                        accession_number = entry.get('accn', '')
                        form_type = entry.get('form', 'N/A')
                        
                        # Generate URLs if we have an accession number
                        filing_urls = generate_edgar_url(cik_stripped, accession_number, form_type) if accession_number else {}
                        
                        entry_data = {
                            'end': entry.get('end', 'N/A'),
                            'val': entry.get('val', 'N/A'),
                            'filed': entry.get('filed', 'N/A'),
                            'form': form_type,
                            'fy': entry.get('fy', 'N/A'),
                            'fp': entry.get('fp', 'N/A'),
                            'accn': accession_number,
                            'filing_urls': filing_urls
                        }
                        processed_data[label]['units'][unit].append(entry_data)
        
        # Now write the processed data to Firestore
        count = 0
        batch_size = 500
        
        for label, data in processed_data.items():
            try:
                # Create a valid document ID from the label
                doc_id = str(label).replace('/', '_').replace('.', '_')
                
                # Add document to batch
                doc_ref = collection_ref.document(doc_id)
                batch.set(doc_ref, data)
                count += 1
                
                # If batch size limit is reached, commit and start new batch
                if count >= batch_size:
                    batch.commit()
                    batch = db.batch()
                    count = 0
            except Exception as e:
                print(f"Error processing label {label}: {str(e)}")
                continue
        
        # Commit any remaining documents in the final batch
        if count > 0:
            batch.commit()
            
        print(f"Data successfully stored in Firestore collection: sec_data_{cik}")
        return True
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False

# Usage
if __name__ == "__main__":
    cik = "0001838359"
    fetch_and_store_sec_data(cik)