import requests

def get_accession_numbers(cik, form_type='4'):
    cik = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    headers = {'User-Agent': "xhaxhilenzi@gmail.com"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        filings = response.json()['filings']['recent']
        accession_numbers = [
            filings['accessionNumber'][i]
            for i, form in enumerate(filings['form'])
            if form == form_type
        ]
        return accession_numbers
    else:
        print("Failed to fetch data")
        return []

# Example: Get Rigetti's 4F accession numbers
cik = "0001838359"
accession_numbers = get_accession_numbers(cik, '4')
print("rigetti's 4F accession numbers:", accession_numbers)