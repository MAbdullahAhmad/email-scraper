import os

# Define the output directory for CSV files
# Use a more reliable path that doesn't depend on complex directory traversal
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(os.path.dirname(script_dir))
OUTPUT_DIR = os.path.join(project_root, "exports", "1-python-approach")

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Output directory set to: {OUTPUT_DIR}")
