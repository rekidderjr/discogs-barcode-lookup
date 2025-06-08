# Discogs Barcode Lookup

A tool for looking up music album barcodes using Discogs data. Downloads and processes Discogs data dumps to create a local SQLite database for offline barcode lookups. Features include multipart downloading, interactive scanning, and integration with music collection management workflows.

## Features

- **Offline Barcode Lookups**: Look up album information using barcodes without requiring an internet connection
- **Comprehensive Data**: Access to the complete Discogs database with millions of releases
- **Fast Performance**: SQLite database optimized for quick barcode searches
- **Accelerated Downloads**: Multipart downloading for faster acquisition of Discogs data dumps
- **Interactive Mode**: User-friendly interface for scanning and managing barcodes
- **Batch Processing**: Process multiple barcodes at once
- **Arrow Key Navigation**: Select from multiple matching albums using arrow keys
- **Individual Album JSON Files**: Create separate JSON files for each album
- **Master Inventory**: Maintain a master inventory of all albums in your collection
- **Data Correction**: Manually update or correct information when needed
- **Path Tracking**: Store the physical location of your albums

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

## Usage

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

#### Step 4: Create Album JSON Files

```bash
# Create JSON for a specific barcode
python3 album_json_creator.py 075596082921

# Run in interactive mode
python3 album_json_creator.py

# Process multiple barcodes from a file
python3 album_json_creator.py barcodes.txt
```

#### Step 5: Open Albums and Scan Barcodes

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
- Stores barcode associations in `data/barcode_database.json`
- Supports arrow key navigation for selecting from multiple matches
- Keeps only the first artist name for cleaner data

### 4. Album JSON Creator (`album_json_creator.py`)

Creates individual JSON files for each album based on barcode scans.

- Creates JSON files in `data/albums/` directory
- Updates a master inventory file (`data/albums/cd_inventory.json`)
- Detects duplicate barcodes and allows selection from multiple matches
- Supports interactive, single barcode, and batch modes
- Color-coded output: green for new albums, yellow for duplicates
- Keeps only the first artist name for cleaner data
- Stores album path information

### 5. Album Opener (`open_albums_with_barcode.sh`)

Opens processed album directories in Finder and prompts for barcode scanning.

- Works with the processed_albums_summary.txt file
- Opens each album in a separate Finder window
- Prompts for barcode scanning

## Data Storage

- **Discogs Data**: Stored in `data/discogs_20250601_releases.xml.gz`
- **SQLite Database**: Stored in `data/discogs_barcodes.db`
- **Barcode Associations**: Stored in `data/barcode_database.json`
- **Album JSON Files**: Stored in `data/albums/` directory
- **Master Inventory**: Stored in `data/albums/cd_inventory.json`

## Maintenance

### Updating the Discogs Database

To update the Discogs database with the latest data:

1. Download the latest Discogs data dump:
```bash
python3 download_discogs_data.py --force
```

2. Reprocess the data:
```bash
python3 process_discogs_data.py --rebuild
```

### Managing the Master Inventory

The master inventory is automatically updated whenever you run `album_json_creator.py`. To manually update it:

1. Edit individual album JSON files in the `data/albums/` directory
2. Run `album_json_creator.py` with any barcode to trigger an update

### Handling Duplicate Barcodes

When a barcode matches multiple albums:

1. In interactive mode, use arrow keys to navigate and select the correct album
2. Press Enter to select or Esc to cancel
3. If curses fails, you'll get a text-based menu as a fallback

### Adding Album Paths

To add or update the physical location of an album:

1. When prompted during barcode lookup or album creation, enter the path
2. To update existing entries, edit the JSON files directly or rescan the barcode

### Quitting and Saving Progress

Both tools support quick exit with progress saving:

1. Type 'q' or 'quit' when prompted for a barcode
2. All changes will be saved before exiting

## Integration with Music Collection Manager

This tool can be integrated with music collection management workflows:

1. After albums are processed, use `open_albums_with_barcode.sh` to open them and scan barcodes
2. The barcode associations are stored in JSON files and a master inventory
3. These associations can be used to enhance metadata or cross-reference with other sources
4. The Path field allows tracking the physical location of albums

## Notes

- The initial download and processing will take significant time due to the large size of the Discogs data dumps.
- Once the database is created, barcode lookups are fast and work offline.
- The barcode database and album JSON files are updated whenever you associate a barcode with an album.
- The tool is designed to work on macOS but can be adapted for other platforms.
- Only the first artist name is kept (before any comma) for cleaner data presentation.

## License

MIT License

## Acknowledgments

- [Discogs](https://www.discogs.com/) for providing the data dumps
- [Discogs Data Dumps](https://discogs-data-dumps.s3.us-west-2.amazonaws.com/index.html) for hosting the data files
