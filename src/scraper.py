from sec_edgar_downloader import Downloader
import os

def download_13f_filings(cik, email, num_filings=5):
    # Initialize downloader with your email (SEC requires this)
    dl = Downloader("My 13F Tracker", email)
    
    # Ensure the data directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # Download filings (e.g., Berkshire Hathaway CIK: 0001067983)
    dl.get("13F", cik, num_filings, download_details=True, output_dir="data/raw")

# Example usage:
if __name__ == "__main__":
    download_13f_filings("0001067983", "your-email@example.com")
