import os
import time
import pandas as pd
import signal
import sys
import traceback
import argparse
from datetime import datetime
from core.scraper import EmailScraper
from config.settings import OUTPUT_DIR

def signal_handler(sig, frame):
    print("\nScraping stopped by user. Saving results...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Email scraper with thresholds')
    parser.add_argument('--input', type=str, help='Path to the input Excel file')
    args = parser.parse_args()
    
    # Check if input Excel file exists, if not create it
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.input and os.path.exists(args.input):
        input_file = args.input
        print(f"Using provided Excel file: {input_file}")
    else:
        # Default locations to check
        possible_locations = [
            os.path.join(script_dir, "websites.xlsx"),
            os.path.join(os.path.expanduser("~"), "Desktop", "websites.xlsx"),
            os.path.join(os.path.expanduser("~"), "Documents", "websites.xlsx")
        ]
        
        input_file = None
        for location in possible_locations:
            if os.path.exists(location):
                input_file = location
                print(f"Found Excel file at: {input_file}")
                break
        
        if not input_file:
            print("Excel file not found. Please create it first with create_excel_template.py")
            print("Or specify the path with --input argument")
            return
    
    try:
        # Read the Excel file
        print(f"Reading Excel file: {input_file}")
        # df = pd.read_excel(input_file)
        df = pd.read_csv(input_file)
        
        # Create results column if it doesn't exist
        if 'Results File' not in df.columns:
            df['Results File'] = ""
        
        # Create a consolidated DataFrame for all emails
        all_emails_df = pd.DataFrame(columns=['Website', 'Email'])
        
        # Process each website
        for index, row in df.iterrows():
            website = row['Website URL']
            email_threshold = row['Email Threshold']
            timeout_mins = row['Timeout Threshold (minutes)']
            
            if pd.isna(website) or not isinstance(website, str) or not website.strip():
                continue
                
            print(f"\nProcessing {website}")
            print(f"Email Threshold: {email_threshold}")
            print(f"Timeout: {timeout_mins} minutes")
            
            # Create scraper instance
            scraper = EmailScraper(website)
            
            # Set timeout in seconds
            timeout_seconds = timeout_mins * 60
            
            # Start scraping with thresholds
            start_time = time.time()
            emails = []
            
            try:
                emails = scraper.scrape_with_thresholds(email_threshold, timeout_seconds)
            except Exception as e:
                print(f"Error scraping {website}: {str(e)}")
            
            # Save results to CSV
            if emails:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = scraper.get_domain()
                filename = f"{domain}_{timestamp}.csv"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                # Ensure output directory exists
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                
                # Save to CSV
                email_df = pd.DataFrame(emails, columns=['Email'])
                email_df.to_csv(filepath, index=False)
                
                # Update the Excel file
                df.at[index, 'Results File'] = filename
                
                # Add to consolidated DataFrame
                for email in emails:
                    all_emails_df = pd.concat([all_emails_df, pd.DataFrame({'Website': [website], 'Email': [email]})], ignore_index=True)
                
                print(f"Found {len(emails)} emails. Saved to {filepath}")
            else:
                print("No emails found.")
        
        # Save updated Excel file
        try:
            df.to_excel(input_file, index=False)
            print(f"\nUpdated {input_file} with results.")
        except Exception as e:
            print(f"Error updating original Excel file: {str(e)}")
            # Try saving to a new location
            results_file = os.path.join(os.path.dirname(input_file), "websites_results.xlsx")
            df.to_excel(results_file, index=False)
            print(f"Saved results to new file: {results_file}")
        
        # Save consolidated emails
        if not all_emails_df.empty:
            consolidated_file = os.path.join(os.path.dirname(input_file), "all_emails_consolidated.xlsx")
            try:
                all_emails_df.to_excel(consolidated_file, index=False)
                print(f"Saved consolidated emails to {consolidated_file}")
            except Exception as e:
                print(f"Error saving consolidated emails: {str(e)}")
                # Try saving as CSV instead
                csv_file = os.path.join(os.path.dirname(input_file), "all_emails_consolidated.csv")
                all_emails_df.to_csv(csv_file, index=False)
                print(f"Saved consolidated emails as CSV: {csv_file}")
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
