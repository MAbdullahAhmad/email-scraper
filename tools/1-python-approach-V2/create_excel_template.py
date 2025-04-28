import os
import sys
import pandas as pd

def create_excel_template():
    """
    Standalone script to create the Excel template file.
    This can be run separately if the main script fails to create the file.
    """
    print("Creating Excel template file...")
    
    # Try different locations
    locations = [
        "websites.xlsx",
        os.path.join(os.path.expanduser("~"), "Desktop", "websites.xlsx"),
        os.path.join(os.path.expanduser("~"), "Documents", "websites.xlsx")
    ]
    
    # Create the DataFrame
    data = {
        'Website URL': [
            'http://www.alnaboodahconstruction.com/',
            'http://www.gcc-uae.net/',
            'http://www.dcc-group.com/',
            'https://gccuae.com/'
        ] + [''] * 46,
        'Email Threshold': [3, 3, 3, 3] + [3] * 46,
        'Timeout Threshold (minutes)': [60, 60, 60, 60] + [60] * 46
    }
    
    df = pd.DataFrame(data)
    
    success = False
    created_location = None
    
    for location in locations:
        try:
            print(f"Attempting to create Excel file at: {location}")
            df.to_excel(location, index=False)
            print(f"Successfully created Excel file at: {location}")
            success = True
            created_location = location
            break
        except Exception as e:
            print(f"Failed to create Excel at {location}: {str(e)}")
    
    # If all attempts fail, try creating a CSV instead
    if not success:
        csv_location = "websites.csv"
        try:
            print(f"Attempting to create CSV file instead at: {csv_location}")
            df.to_csv(csv_location, index=False)
            print(f"Successfully created CSV file at: {csv_location}")
            print("NOTE: You'll need to manually convert this CSV to Excel format.")
            created_location = csv_location
        except Exception as e:
            print(f"Failed to create CSV at {csv_location}: {str(e)}")
            print("All attempts to create a template file have failed.")
            print("Please check your permissions and ensure pandas and openpyxl are installed.")
    
    return created_location

if __name__ == "__main__":
    location = create_excel_template()
    if location:
        print(f"\nTemplate created successfully at: {location}")
        print("Please fill in the websites and thresholds, then run the main.py script.")
    else:
        print("\nFailed to create template file.")
        sys.exit(1)
