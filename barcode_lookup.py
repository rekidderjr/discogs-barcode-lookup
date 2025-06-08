#!/usr/bin/env python3
"""
Barcode Lookup Tool for Music Collection Manager

This script looks up album information from barcodes using a local database
created from Discogs data dumps.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Get the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File to store barcode associations
BARCODE_DB_FILE = os.path.join(SCRIPT_DIR, "data", "barcode_database.json")
LOCAL_DISCOGS_DB = os.path.join(SCRIPT_DIR, "data", "discogs_barcodes.db")

def lookup_barcode(barcode):
    """
    Look up album information using a barcode via the local database.
    
    Args:
        barcode: The barcode string (UPC/EAN)
        
    Returns:
        Dictionary with album metadata or None if not found
    """
    print(f"🔍 Looking up barcode: {barcode}")
    
    if not os.path.exists(LOCAL_DISCOGS_DB):
        print(f"❌ Local database not found at {LOCAL_DISCOGS_DB}")
        print("Please run the process_discogs_data.py script first.")
        return None
    
    # Clean up barcode (remove spaces, dashes, etc.)
    barcode = ''.join(c for c in barcode if c.isdigit())
    
    try:
        conn = sqlite3.connect(LOCAL_DISCOGS_DB)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Query the database for the barcode
        cursor.execute('''
        SELECT * FROM releases WHERE barcode = ?
        ''', (barcode,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"❌ No results found for barcode: {barcode}")
            return None
        
        # Extract metadata from the result
        metadata = {
            'barcode': barcode,
            'discogs_id': result['id'],
            'discogs_url': f"https://www.discogs.com/release/{result['id']}",
            'title': result['title'],
            'artist': result['artist'],
            'year': result['year'],
            'country': result['country'],
            'formats': result['format'].split(', ') if result['format'] else [],
            'labels': result['label'].split(', ') if result['label'] else [],
            'genres': result['genre'].split(', ') if result['genre'] else [],
            'catno': result['catno']
        }
        
        print(f"✅ Found album: {metadata['artist']} - {metadata['title']} ({metadata['year']})")
        return metadata
    
    except Exception as e:
        print(f"❌ Error looking up barcode: {e}")
    
    return None

def load_barcode_database():
    """Load the existing barcode database."""
    if os.path.exists(BARCODE_DB_FILE):
        try:
            with open(BARCODE_DB_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Error reading barcode database. Creating new one.")
            return {}
    else:
        # Create the data directory if it doesn't exist
        os.makedirs(os.path.dirname(BARCODE_DB_FILE), exist_ok=True)
        return {}

def save_barcode_database(database):
    """Save the barcode database."""
    with open(BARCODE_DB_FILE, 'w') as f:
        json.dump(database, f, indent=2)

def associate_barcode_with_album(barcode, metadata, artist=None, album=None):
    """
    Associate a barcode with an album in the database.
    
    Args:
        barcode: The barcode string
        metadata: The metadata from the local database
        artist: Optional artist name override
        album: Optional album name override
    """
    database = load_barcode_database()
    
    # Use provided artist/album or extract from metadata
    artist_name = artist or metadata.get('artist', '')
    album_name = album or metadata.get('title', '')
    
    # Create entry
    entry = {
        'barcode': barcode,
        'artist': artist_name,
        'album': album_name,
        'discogs_id': metadata.get('discogs_id', ''),
        'discogs_url': metadata.get('discogs_url', ''),
        'year': metadata.get('year', ''),
        'genres': metadata.get('genres', []),
        'formats': metadata.get('formats', []),
        'labels': metadata.get('labels', []),
        'country': metadata.get('country', ''),
        'catno': metadata.get('catno', ''),
        'timestamp': datetime.now().isoformat()
    }
    
    # Add to database
    database[barcode] = entry
    save_barcode_database(database)
    
    print(f"✅ Associated barcode {barcode} with {artist_name} - {album_name}")

def interactive_mode():
    """Run the barcode lookup tool in interactive mode."""
    print("=== Barcode Lookup Tool ===")
    print("Enter 'quit' to exit")
    
    while True:
        barcode = input("\nScan or enter barcode: ").strip()
        if barcode.lower() == 'quit':
            break
        
        if not barcode:
            print("Please enter a valid barcode")
            continue
        
        metadata = lookup_barcode(barcode)
        
        if metadata:
            print("\n=== Album Information ===")
            print(f"Artist: {metadata.get('artist', 'Unknown')}")
            print(f"Title: {metadata.get('title', 'Unknown')}")
            print(f"Year: {metadata.get('year', 'Unknown')}")
            print(f"Country: {metadata.get('country', 'Unknown')}")
            print(f"Genres: {', '.join(metadata.get('genres', []))}")
            print(f"Labels: {', '.join(metadata.get('labels', []))}")
            print(f"Catalog #: {metadata.get('catno', 'Unknown')}")
            print(f"Formats: {', '.join(metadata.get('formats', []))}")
            print(f"Discogs URL: {metadata.get('discogs_url', '')}")
            
            # Ask if the information is correct
            correct = input("\nIs this information correct? (y/n): ").strip().lower()
            if correct == 'n':
                # Ask if user wants to manually update or skip
                action = input("Do you want to manually update or skip? (m/s): ").strip().lower()
                if action == 'm':
                    artist = input("Enter artist name: ").strip()
                    album = input("Enter album name: ").strip()
                    associate_barcode_with_album(barcode, metadata, artist, album)
                else:
                    print("Skipping this barcode.")
            else:
                # Ask if user wants to associate this barcode with the album
                associate = input("Associate this barcode with the album? (y/n): ").strip().lower()
                if associate == 'y':
                    associate_barcode_with_album(barcode, metadata)
        else:
            print("No album information found for this barcode.")
            
            # Ask if user wants to manually associate this barcode
            associate = input("\nManually associate this barcode with an album? (y/n): ").strip().lower()
            if associate == 'y':
                artist = input("Enter artist name: ").strip()
                album = input("Enter album name: ").strip()
                
                # Create minimal metadata
                minimal_metadata = {
                    'artist': artist,
                    'title': album
                }
                
                associate_barcode_with_album(barcode, minimal_metadata, artist, album)

def main():
    # Create data directory if it doesn't exist
    os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)
    
    # Check if barcode was provided as command line argument
    if len(sys.argv) > 1:
        barcode = sys.argv[1]
        metadata = lookup_barcode(barcode)
        if metadata:
            # Pretty print the metadata
            print(json.dumps(metadata, indent=2))
            
            # Ask if the information is correct
            correct = input("\nIs this information correct? (y/n): ").strip().lower()
            if correct == 'n':
                # Ask if user wants to manually update or skip
                action = input("Do you want to manually update or skip? (m/s): ").strip().lower()
                if action == 'm':
                    artist = input("Enter artist name: ").strip()
                    album = input("Enter album name: ").strip()
                    associate_barcode_with_album(barcode, metadata, artist, album)
                else:
                    print("Skipping this barcode.")
            else:
                # Ask if user wants to associate this barcode with the album
                associate = input("Associate this barcode with the album? (y/n): ").strip().lower()
                if associate == 'y':
                    associate_barcode_with_album(barcode, metadata)
    else:
        # Run in interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
