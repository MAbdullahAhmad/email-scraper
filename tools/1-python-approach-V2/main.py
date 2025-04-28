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
    parser.add_argument('--create-template', action='store_true', help='Create a new template Excel file')
    args = parser.parse_args()
    
    # If user wants to create a template, import and run the template creator
    if args.create_template:
        try:
            from create_excel_template_v2 import create_excel_template
            template_path = create_excel_template()
            if template_path:
                print(f"Template created at: {template_path}")
                print("Please fill in the websites and run this script again with:")
                print(f"python main.py --input {template_path}")
            return
        except ImportError:
            print("Could not import create_excel_template_v2.py")
            print("Please run create_excel_template_v2.py separately.")
            return
    
    # Check if input Excel file exists
    if args.input and os.path.exists(args.input):
        input_file = args.input
        print(f"Using provided Excel file: {input_file}")
    else:
        # Default locations to check
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_locations = [
            os.path.join(script_dir, "websites.xlsx"),
            os.path.join(os.path.expanduser("~"), "Desktop", "websites.xlsx"),
            os.path.join(os.path.expanduser("~"), "Documents", "websites.xlsx")
        ]
        
        # Also check for files with "template" in the name
        for root, dirs, files in os.walk(script_dir):
            for file in files:
                if file.endswith(".xlsx") and "website" in file.lower():
                    possible_locations.append(os.path.join(root, file))
        
        input_file = None
        for location in possible_locations:
            if os.path.exists(location):
                input_file = location
                print(f"Found Excel file at: {input_file}")
                break
        
        if not input_file:
            print("Excel file not found. Creating a new template...")
            try:
                from create_excel_template_v2 import create_excel_template
                template_path = create_excel_template()
                if template_path:
                    print(f"Template created at: {template_path}")
                    print("Please fill in the websites and run this script again.")
                return
            except ImportError:
                print("Could not create template automatically.")
                print("Please run create_excel_template_v2.py first.")
                return
    
    try:
        # Read the Excel file
        print(f"Reading Excel file: {input_file}")
        df = pd.read_excel(input_file)
        
        # Validate the Excel structure
        required_columns = ['Website URL', 'Email Threshold', 'Timeout Threshold (minutes)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Excel file is missing required columns: {', '.join(missing_columns)}")
            print("Please use the template created by create_excel_template_v2.py")
            return
        
        # Create results column if it doesn't exist
        if 'Results File' not in df.columns:
            df['Results File'] = ""
        
        # Create a consolidated DataFrame for all emails
        all_emails_df = pd.DataFrame(columns=['Website', 'Email', 'Email Type'])
        
        # Ensure the output directory exists
        # FIX: Create the output directory structure if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Output directory: {OUTPUT_DIR}")
        
        # Process each website
        for index, row in df.iterrows():
            website = row['Website URL']
            email_threshold = row['Email Threshold']
            timeout_mins = row['Timeout Threshold (minutes)']
            
            if pd.isna(website) or not isinstance(website, str) or not website.strip():
                continue
                
            print(f"\n{'='*50}")
            print(f"Processing {website} ({index+1}/{len(df)})")
            print(f"Email Threshold: {email_threshold}")
            print(f"Timeout: {timeout_mins} minutes")
            print(f"{'='*50}")
            
            # Create scraper instance
            scraper = EmailScraper(website)
            
            # Set timeout in seconds
            timeout_seconds = timeout_mins * 60
            
            # Start scraping with thresholds
            start_time = time.time()
            emails = []
            
            try:
                emails = scraper.scrape_with_thresholds(email_threshold, timeout_seconds)
                
                elapsed_time = time.time() - start_time
                print(f"\nCompleted in {elapsed_time:.2f} seconds")
                print(f"Found {len(emails)} emails for {website}")
                
                if len(emails) >= email_threshold:
                    print(f"Email threshold reached: {email_threshold}")
                elif elapsed_time >= timeout_seconds:
                    print(f"Timeout reached: {timeout_mins} minutes")
                
            except Exception as e:
                print(f"Error scraping {website}: {str(e)}")
                traceback.print_exc()
            
            # Save results to CSV
            if emails:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = scraper.get_domain()
                filename = f"{domain}_{timestamp}.csv"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                try:
                    # Save to CSV
                    email_df = pd.DataFrame(emails, columns=['Email'])
                    email_df.to_csv(filepath, index=False)
                    
                    # Update the Excel file
                    df.at[index, 'Results File'] = filename
                    
                    # Add to consolidated DataFrame
                    for email in emails:
                        # Determine email type
                        email_type = "Generic"
                        if '@' in email:
                            prefix = email.split('@')[0].lower()
                            if prefix in ['info', 'contact', 'sales', 'admin', 'support']:
                                email_type = prefix.capitalize()
                        
                        all_emails_df = pd.concat([
                            all_emails_df, 
                            pd.DataFrame({'Website': [website], 'Email': [email], 'Email Type': [email_type]})
                        ], ignore_index=True)
                    
                    print(f"Saved {len(emails)} emails to {filepath}")
                except Exception as e:
                    print(f"Error saving CSV file: {str(e)}")
                    print(f"Attempted to save to: {filepath}")
                    # Try an alternative location
                    alt_filepath = os.path.join(os.path.dirname(input_file), f"{domain}_{timestamp}.csv")
                    try:
                        email_df.to_csv(alt_filepath, index=False)
                        print(f"Saved to alternative location: {alt_filepath}")
                        df.at[index, 'Results File'] = os.path.basename(alt_filepath)
                    except Exception as alt_e:
                        print(f"Failed to save to alternative location: {str(alt_e)}")
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
                
        print("\nEmail scraping completed successfully!")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
