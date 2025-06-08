# Discogs Barcode Lookup

A tool for looking up music album barcodes using Discogs data. Downloads and processes Discogs data dumps to create a local SQLite database for offline barcode lookups. Features include multipart downloading, interactive scanning, and integration with music collection management workflows.

## Features

- **Offline Barcode Lookups**: Look up album information using barcodes without requiring an internet connection
- **Comprehensive Data**: Access to the complete Discogs database with millions of releases
- **Fast Performance**: SQLite database optimized for quick barcode searches
- **Accelerated Downloads**: Multipart downloading for faster acquisition of Discogs data dumps
- **Interactive Mode**: User-friendly interface for scanning and managing barcodes
- **Batch Processing**: Open album directories and scan barcodes in batch
- **Data Correction**: Manually update or correct information when needed
- **Sample Database**: Includes a sample database for immediate testing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rekidderjr/discogs-barcode-lookup.git
cd discogs-barcode-lookup
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure all scripts are executable:
```bash
chmod +x *.py *.sh
```

4. For immediate testing, you can use the included sample database:
```bash
python3 sample_data.py
```

## Usage

### Quick Start with Sample Data

To quickly test the functionality without downloading the full Discogs data:

```bash
# Create the sample database
python3 sample_data.py

# Look up a sample barcode
python3 barcode_lookup.py 075596082921
```

### Full Workflow

#### Step 1: Download Discogs Data

```bash
python3 download_discogs_data.py
```

This will download the Discogs releases data dump (9.9GB) to the `data` directory using multipart downloading for better performance.

#### Step 2: Process the Data

```bash
python3 process_discogs_data.py
```

This will process the downloaded data and create a SQLite database for barcode lookups.

#### Step 3: Look Up Barcodes

```bash
# Look up a specific barcode
python3 barcode_lookup.py 075596082921

# Run in interactive mode
python3 barcode_lookup.py
```

#### Step 4: Open Albums and Scan Barcodes

```bash
./open_albums_with_barcode.sh
```

This will open each processed album directory in Finder and prompt you to scan its barcode.

## Components

### 1. Data Downloader (`download_discogs_data.py`)

Downloads the Discogs data dumps using multipart downloads for faster and more reliable transfers.

- Uses 8 concurrent connections to accelerate downloads
- Handles large files (9.9GB releases file)
- Provides progress tracking

### 2. Data Processor (`process_discogs_data.py`)

Processes the downloaded Discogs data dumps and creates a SQLite database for efficient barcode lookups.

- Extracts barcode information from the XML data
- Creates a searchable database
- Optimized for fast lookups

### 3. Barcode Lookup (`barcode_lookup.py`)

Looks up album information using barcodes and allows you to associate barcodes with albums.

- Searches the local database
- Returns detailed album information
- Allows manual corrections
- Stores barcode associations

### 4. Album Opener (`open_albums_with_barcode.sh`)

Opens processed album directories in Finder and prompts for barcode scanning.

- Works with the processed_albums_summary.txt file
- Opens each album in a separate Finder window
- Prompts for barcode scanning

### 5. Sample Data Generator (`sample_data.py`)

Creates a small sample SQLite database with hardcoded entries for testing.

- Includes 5 popular albums with their barcodes
- Allows testing without downloading the full Discogs data

## Data Storage

- **Discogs Data**: Stored in `data/discogs_20250601_releases.xml.gz`
- **SQLite Database**: Stored in `data/discogs_barcodes.db`
- **Barcode Associations**: Stored in `data/barcode_database.json`

## Integration with Music Collection Manager

This tool can be integrated with music collection management workflows:

1. After albums are processed, use `open_albums_with_barcode.sh` to open them and scan barcodes
2. The barcode associations are stored in a JSON database
3. These associations can be used to enhance metadata or cross-reference with other sources

## Notes

- The initial download and processing will take significant time due to the large size of the Discogs data dumps.
- Once the database is created, barcode lookups are fast and work offline.
- The barcode database is updated whenever you associate a barcode with an album.
- The tool is designed to work on macOS but can be adapted for other platforms.

## License

MIT License

## Acknowledgments

- [Discogs](https://www.discogs.com/) for providing the data dumps
- [Discogs Data Dumps](https://discogs-data-dumps.s3.us-west-2.amazonaws.com/index.html) for hosting the data files
