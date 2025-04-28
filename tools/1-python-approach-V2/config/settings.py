import os

# Define the output directory for CSV files
# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

# Define the output directory for CSV files
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "exports", "1-python-approach")

# Print the output directory for debugging
print(f"Output directory set to: {OUTPUT_DIR}")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
