import os
import pandas as pd
from datetime import datetime

def create_excel_template():
    """
    Create an Excel template with the required structure:
    - Website URL
    - Email Threshold
    - Timeout Threshold (minutes)
    - Results File (will be populated by the main script)
    """
    print("Creating Excel template file...")
    
    # Sample websites to include
    sample_websites = [
        'http://www.alnaboodahconstruction.com/',
        'http://www.gcc-uae.net/',
        'http://www.dcc-group.com/',
        'https://gccuae.com/',
        'http://www.silvercoast.ae/',
        'https://www.ric-uae.com/',
        'http://www.bcg-uae.com/',
        'http://www.hilalco.com/',
        'http://www.nafcontractingllc.com/',
        'http://adicc-uae.com/',
        'http://www.adcc.ae/',
        'http://www.alikhaagroup.com/',
        'https://algeemi.com/',
        'http://www.unec.co/',
        'http://www.astraenc.com/',
        'http://www.alryum.com/',
        'http://www.accgroup.com/',
        'http://www.dhabicontracting.com/',
        'http://www.fibrex.ae/',
        'http://www.galfaremirates.com/',
        'https://www.morals.ae/',
        'https://www.unitekuae.com/',
        'https://www.wadeadams.com/',
        'http://www.groupamana.com/',
        'http://www.alec.ae/',
        'http://agcmco.com/',
        'https://adnan.ae/ ',
    ]
    
    # Add empty rows to reach 50-60 websites
    total_websites = 60
    empty_websites = [''] * (total_websites - len(sample_websites))
    
    # Create the DataFrame
    data = {
        'Website URL': sample_websites + empty_websites,
        'Email Threshold': [3] * len(sample_websites) + [3] * len(empty_websites),
        'Timeout Threshold (minutes)': [60] * len(sample_websites) + [60] * len(empty_websites),
        'Results File': [''] * total_websites
    }
    
    df = pd.DataFrame(data)
    
    # Define possible locations to save the file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    locations = [
        f"websites_template_{timestamp}.xlsx",
        os.path.join(os.path.expanduser("~"), "Desktop", f"websites_template_{timestamp}.xlsx"),
        os.path.join(os.path.expanduser("~"), "Documents", f"websites_template_{timestamp}.xlsx")
    ]
    
    # Try to save to each location
    for location in locations:
        try:
            print(f"Attempting to create Excel file at: {location}")
            df.to_excel(location, index=False)
            print(f"Successfully created Excel file at: {location}")
            return location
        except Exception as e:
            print(f"Failed to create Excel at {location}: {str(e)}")
    
    # If all attempts fail, try creating a CSV instead
    csv_location = f"websites_template_{timestamp}.csv"
    try:
        print(f"Attempting to create CSV file instead at: {csv_location}")
        df.to_csv(csv_location, index=False)
        print(f"Successfully created CSV file at: {csv_location}")
        print("NOTE: You'll need to manually convert this CSV to Excel format.")
        return csv_location
    except Exception as e:
        print(f"Failed to create CSV at {csv_location}: {str(e)}")
        print("All attempts to create a template file have failed.")
        return None

if __name__ == "__main__":
    location = create_excel_template()
    if location:
        print(f"\nTemplate created successfully at: {location}")
        print("Please fill in the websites and thresholds, then run the main.py script.")
        
        # Open the file if possible
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == 'Windows':
                os.startfile(location)
            elif system == 'Darwin':  # macOS
                subprocess.call(['open', location])
            else:  # Linux
                subprocess.call(['xdg-open', location])
                
            print(f"Opened {location} for editing.")
        except Exception as e:
            print(f"Could not automatically open the file: {str(e)}")
            print(f"Please open {location} manually to edit.")
    else:
        print("\nFailed to create template file.")
