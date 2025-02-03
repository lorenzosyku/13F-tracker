import requests

def get_accession_numbers(cik, form_type='13F-HR'):
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    headers = {'User-Agent': "xhaxhilenzi@gmail.com"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        filings = response.json().get('filings', {}).get('recent', {})
        accession_numbers = [
            filings['accessionNumber'][i]
            for i, form in enumerate(filings.get('form', []))
            if form == form_type
        ]
        return accession_numbers
    else:
        print("Failed to fetch data")
        return []

# Example: Get 13F-HR accession numbers for BlackRock Inc.
cik = "0001364742"  # BlackRock Inc.
accession_numbers = get_accession_numbers(cik, '13F-HR')
print("BlackRock's 13F-HR accession numbers:", accession_numbers)
