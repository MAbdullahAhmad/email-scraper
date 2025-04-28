# Email Scraper

A Python tool to scrape generic/main email addresses from websites based on thresholds.

## Features

- Scrape emails from websites with configurable thresholds
- Focus on "main" emails only (info@, sales@, admin@, etc.)
- Stop scraping when email threshold or timeout is reached
- Save results to CSV files and update Excel with results
- Create consolidated report of all emails

## Requirements

- Python 3.6+
- Required packages: requests, beautifulsoup4, pandas, openpyxl

Install dependencies:
\`\`\`
pip install -r requirements.txt
\`\`\`

## Usage

### 1. Create Excel Template

First, create an Excel template with the websites you want to scrape:

\`\`\`
python create_excel_template_v2.py
\`\`\`

This will create an Excel file with columns:
- Website URL
- Email Threshold (number of emails to find before stopping)
- Timeout Threshold (minutes)
- Results File (will be populated by the script)

### 2. Run the Scraper

Run the main script with the Excel file:

\`\`\`
python main.py --input path/to/your/excel_file.xlsx
\`\`\`

Or let the script find the Excel file automatically:

\`\`\`
python main.py
\`\`\`

You can also create a new template directly from the main script:

\`\`\`
python main.py --create-template
\`\`\`

### 3. Results

The script will:
1. Process each website in the Excel file
2. Extract main/generic emails (info@, sales@, admin@, etc.)
3. Stop when the email threshold or timeout is reached
4. Save emails to CSV files in the exports directory
5. Update the Excel file with the results file names
6. Create a consolidated Excel file with all emails

## Project Structure

\`\`\`
email-scraper/
├── exports/                  # Output directory for CSV files
│   └── 1-python-approach/    
├── tools/
│   └── 1-python-approach/
│       ├── config/           # Configuration settings
│       │   └── settings.py
│       ├── core/             # Core functionality
│       │   ├── scraper.py    # Main scraper class
│       │   └── util/
│       │       └── functions/
│       │           └── email_extractor.py  # Email extraction logic
│       ├── main.py           # Main script
│       ├── create_excel_template_v2.py  # Excel template creator
│       ├── requirements.txt  # Dependencies
│       └── README.md         # Documentation
└── _notes/                   # Project notes
\`\`\`

## How It Works

1. The script reads websites and thresholds from an Excel file
2. For each website, it:
   - Scrapes the website and follows internal links
   - Extracts email addresses using regex
   - Filters for "main" emails only (info@, sales@, etc.)
   - Stops when it finds the threshold number of emails or reaches the timeout
3. Results are saved to CSV files and the Excel file is updated
4. A consolidated report of all emails is created

## Customization

- Edit `email_extractor.py` to modify the email extraction logic
- Edit `scraper.py` to change the scraping behavior
- Edit `settings.py` to change the output directory
