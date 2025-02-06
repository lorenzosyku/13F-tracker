import requests
import json
import csv

# Define CIK and headers
cik = "0001838359"
headers = {
    "User-Agent": "xhaxhilenzi@gmail.com"
}

# Fetch company facts data
url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
response = requests.get(url, headers=headers)

# Check response status
if response.status_code == 200:
    data = response.json()
    
    # Extract relevant financial facts
    financial_data = []
    for taxonomy, items in data.get("facts", {}).items():
        for metric, details in items.items():
            label = details.get("label", metric)  # Use label if available
            for unit, values in details.get("units", {}).items():
                for entry in values:
                    financial_data.append([
                        label,
                        unit,
                        entry.get("end", "N/A"),  # End date
                        entry.get("val", "N/A")  # Value
                    ])
    
    # Define CSV file name
    csv_filename = f"SEC_CIK_{cik}_financials.csv"

    # Save data to CSV
    with open(csv_filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Unit", "Date", "Value"])  # Header
        writer.writerows(financial_data)

    print(f"Data saved successfully as {csv_filename}")

else:
    print(f"Error: {response.status_code}, {response.text}")
