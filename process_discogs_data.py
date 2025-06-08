#!/usr/bin/env python3
"""
Discogs Data Processor for Music Collection Manager

This script processes the downloaded Discogs data dumps and creates a SQLite database
for efficient barcode lookups.
"""

import os
import sys
import gzip
import sqlite3
import xml.etree.ElementTree as ET
from tqdm import tqdm

# Local directory with the Discogs data dumps
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
RELEASES_FILE = "discogs_20250601_releases.xml.gz"
DB_FILE = os.path.join(DATA_DIR, "discogs_barcodes.db")

def create_database():
    """Create the SQLite database for storing barcode data."""
    print("🔧 Creating database schema...")
    
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table for releases with barcodes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS releases (
        id INTEGER PRIMARY KEY,
        barcode TEXT,
        title TEXT,
        artist TEXT,
        year INTEGER,
        country TEXT,
        format TEXT,
        label TEXT,
        genre TEXT,
        catno TEXT
    )
    ''')
    
    # Create index on barcode for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcode ON releases (barcode)')
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema created.")

def process_releases(file_path):
    """
    Process the releases XML file and extract barcode information.
    
    Args:
        file_path: Path to the gzipped releases XML file
    """
    print(f"🔍 Processing releases from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM releases")
    conn.commit()
    
    # Process the XML file
    try:
        # Get the file size for progress tracking
        file_size = os.path.getsize(file_path)
        
        # Use a context manager to handle the gzipped file
        with gzip.open(file_path, 'rb') as f:
            # Process the XML in chunks to avoid loading the entire file into memory
            context = ET.iterparse(f, events=('end',))
            
            count = 0
            barcode_count = 0
            
            # Setup progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Processing") as pbar:
                for event, elem in context:
                    if elem.tag == 'release':
                        try:
                            release_id = elem.get('id')
                            title = elem.findtext('title', '')
                            
                            # Extract artist information
                            artists = elem.findall('.//artist/name')
                            artist_names = [artist.text for artist in artists if artist.text]
                            artist = ', '.join(artist_names)
                            
                            # Extract year
                            year = elem.findtext('released', '')
                            year = int(year) if year and year.isdigit() else None
                            
                            # Extract country
                            country = elem.findtext('country', '')
                            
                            # Extract format
                            formats = elem.findall('.//format')
                            format_names = [fmt.get('name', '') for fmt in formats if fmt.get('name')]
                            format_str = ', '.join(format_names)
                            
                            # Extract label and catalog number
                            labels = elem.findall('.//label')
                            label_names = [label.get('name', '') for label in labels if label.get('name')]
                            label = ', '.join(label_names)
                            
                            catnos = [label.get('catno', '') for label in labels if label.get('catno')]
                            catno = ', '.join(catnos)
                            
                            # Extract genre
                            genres = elem.findall('.//genre')
                            genre_names = [genre.text for genre in genres if genre.text]
                            genre = ', '.join(genre_names)
                            
                            # Extract barcode
                            barcodes = elem.findall('.//identifier[@type="Barcode"]')
                            for barcode_elem in barcodes:
                                barcode = barcode_elem.get('value', '').strip()
                                if barcode:
                                    # Clean up barcode (remove spaces, dashes, etc.)
                                    barcode = ''.join(c for c in barcode if c.isdigit())
                                    
                                    # Insert into database
                                    cursor.execute('''
                                    INSERT OR REPLACE INTO releases 
                                    (id, barcode, title, artist, year, country, format, label, genre, catno)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (release_id, barcode, title, artist, year, country, format_str, label, genre, catno))
                                    
                                    barcode_count += 1
                        except Exception as e:
                            print(f"Error processing release {release_id}: {e}")
                        
                        # Clear element to free memory
                        elem.clear()
                        
                        count += 1
                        if count % 10000 == 0:
                            conn.commit()
                            
                        # Update progress bar based on file position
                        if hasattr(f, 'fileobj'):
                            pbar.update(f.fileobj.tell() - pbar.n)
        
        conn.commit()
        print(f"✅ Processing complete. Processed {count} releases with {barcode_count} barcodes.")
    
    except Exception as e:
        print(f"❌ Error processing releases: {e}")
    
    finally:
        conn.close()

def search_barcode(barcode):
    """
    Search for a barcode in the database.
    
    Args:
        barcode: The barcode to search for
    """
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file not found: {DB_FILE}")
        return
    
    # Clean up barcode (remove spaces, dashes, etc.)
    barcode = ''.join(c for c in barcode if c.isdigit())
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM releases WHERE barcode = ?
    ''', (barcode,))
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        print(f"❌ No results found for barcode: {barcode}")
        return
    
    print(f"✅ Found {len(results)} results for barcode: {barcode}")
    for i, row in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Title: {row['title']}")
        print(f"  Artist: {row['artist']}")
        print(f"  Year: {row['year']}")
        print(f"  Country: {row['country']}")
        print(f"  Format: {row['format']}")
        print(f"  Label: {row['label']}")
        print(f"  Catalog #: {row['catno']}")
        print(f"  Genre: {row['genre']}")
        print(f"  Discogs URL: https://www.discogs.com/release/{row['id']}")

def main():
    # Check if the releases file exists
    releases_path = os.path.join(DATA_DIR, RELEASES_FILE)
    if not os.path.exists(releases_path):
        print(f"❌ Releases file not found: {releases_path}")
        print("Please run download_discogs_data.py first.")
        return
    
    # Create the database
    create_database()
    
    # Process the releases
    process_releases(releases_path)
    
    # If a barcode was provided as a command-line argument, search for it
    if len(sys.argv) > 1:
        barcode = sys.argv[1]
        search_barcode(barcode)

if __name__ == "__main__":
    main()
