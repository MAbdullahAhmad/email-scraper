import os

# Define the output directory for CSV files
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "exports", "1-python-approach")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
