import requests
import json

def find_cik(company_name):
    """
    Find CIK number for a company using SEC's EDGAR API
    
    Parameters:
    company_name (str): Name of the company to search for
    
    Returns:
    dict: Dictionary containing CIK and company name if found, None if not found
    """
    # Format the URL and headers
    base_url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        'User-Agent': 'xhaxhilenzi@gmail.com'  # Replace with your information
    }
    
    try:
        # Make the request to SEC
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        # Search for the company (case-insensitive)
        company_name_lower = company_name.lower()
        for entry in data.values():
            if company_name_lower in entry['title'].lower():
                return {
                    'cik': str(entry['cik_str']).zfill(10),
                    'name': entry['title']
                }
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None

def main():
    # Example usage
    company_name = input("Enter hedge fund name to search: ")
    result = find_cik(company_name)
    
    if result:
        print(f"\nFound matching company:")
        print(f"Name: {result['name']}")
        print(f"CIK: {result['cik']}")
    else:
        print(f"\nNo matching company found for '{company_name}'")
        print("Note: Some companies might not be listed in the SEC database.")

if __name__ == "__main__":
    main()