# Email Scraper with Selenium

This tool scrapes websites for email addresses using Selenium for better handling of modern websites with JavaScript content.

## Setup Instructions

### 1. Install Dependencies

\`\`\`bash
pip install selenium pandas openpyxl
\`\`\`

### 2. Download ChromeDriver

You need to download ChromeDriver that matches your Chrome browser version:

1. Check your Chrome version: Open Chrome and go to Menu > Help > About Google Chrome
2. Download the matching ChromeDriver from: https://chromedriver.chromium.org/downloads
3. Place the `chromedriver.exe` file in the same directory as the `main.py` script

### 3. Prepare Excel File

Create an Excel file with the following columns:
- Website URL
- Email Threshold (number of emails to find before stopping)
- Timeout Threshold (minutes)

You can use the included script to create a template:

\`\`\`bash
python create_excel_template.py
\`\`\`

### 4. Run the Scraper

\`\`\`bash
python main.py --input path/to/your/excel_file.xlsx
\`\`\`

Optional arguments:
- `--headless`: Run Chrome in headless mode (no visible browser window)
- `--chromedriver path/to/chromedriver.exe`: Specify custom ChromeDriver path

## Features

- Scrapes websites for generic email addresses (info@, sales@, admin@, etc.)
- Respects email threshold and timeout settings
- Handles JavaScript-rendered content
- Saves results to CSV files and updates the Excel file
- Creates a consolidated file with all found emails
