#!/usr/bin/env python3
"""
Album JSON Creator for Music Collection Manager

This script creates individual JSON files for each album in a 'data/albums' folder
based on barcode scans. It uses the barcode lookup functionality to retrieve
album data from the local Discogs database.
"""

import os
import sys
import json
import sqlite3
import re
import glob
from datetime import datetime
from barcode_lookup import lookup_barcode

# Get the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory to store album JSON files
ALBUMS_DIR = os.path.join(SCRIPT_DIR, "data", "albums")

# Master inventory file
INVENTORY_FILE = os.path.join(ALBUMS_DIR, "cd_inventory.json")

def sanitize_filename(filename):
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: The string to sanitize
        
    Returns:
        A sanitized string safe for use as a filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized

def find_existing_album_by_barcode(barcode):
    """
    Check if an album with the given barcode already exists in the albums directory.
    
    Args:
        barcode: The barcode to search for
        
    Returns:
        Tuple of (exists, filepath, album_data) or (False, None, None) if not found
    """
    # Create albums directory if it doesn't exist
    os.makedirs(ALBUMS_DIR, exist_ok=True)
    
    # Get all JSON files in the albums directory except the inventory file
    json_files = [f for f in glob.glob(os.path.join(ALBUMS_DIR, "*.json")) 
                 if os.path.basename(f) != "cd_inventory.json"]
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                album_data = json.load(f)
                if album_data.get('Barcode') == barcode:
                    return True, json_file, album_data
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
    
    return False, None, None

def load_inventory():
    """
    Load the master CD inventory file.
    
    Returns:
        Dictionary containing the inventory data
    """
    # Create albums directory if it doesn't exist
    os.makedirs(ALBUMS_DIR, exist_ok=True)
    
    # Create inventory file if it doesn't exist
    if not os.path.exists(INVENTORY_FILE):
        inventory = {
            "albums": [],
            "last_updated": datetime.now().isoformat()
        }
        with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        return inventory
    
    # Load existing inventory
    try:
        with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading inventory file: {e}")
        # Return a new inventory if there was an error
        return {
            "albums": [],
            "last_updated": datetime.now().isoformat()
        }

def update_inventory():
    """
    Update the master CD inventory file with all individual album JSON files.
    Avoids duplicates by checking barcodes.
    
    Returns:
        Number of albums in the inventory
    """
    # Load current inventory
    inventory = load_inventory()
    
    # Get all album JSON files except the inventory file
    json_files = [f for f in glob.glob(os.path.join(ALBUMS_DIR, "*.json")) 
                 if os.path.basename(f) != "cd_inventory.json"]
    
    # Track existing barcodes to avoid duplicates
    existing_barcodes = {album.get("Barcode") for album in inventory["albums"]}
    
    # Count of new albums added
    new_albums = 0
    
    # Process each album file
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                album_data = json.load(f)
                
                # Skip if this barcode is already in the inventory
                barcode = album_data.get("Barcode")
                if barcode and barcode in existing_barcodes:
                    continue
                
                # Add to inventory and track the barcode
                inventory["albums"].append(album_data)
                if barcode:
                    existing_barcodes.add(barcode)
                new_albums += 1
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Update the last updated timestamp
    inventory["last_updated"] = datetime.now().isoformat()
    
    # Save the updated inventory
    try:
        with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated master inventory with {new_albums} new albums. Total: {len(inventory['albums'])}")
    except Exception as e:
        print(f"❌ Error saving inventory file: {e}")
    
    return len(inventory["albums"])

def create_album_json(metadata):
    """
    Create a JSON file for an album based on metadata.
    
    Args:
        metadata: Dictionary with album metadata
        
    Returns:
        Path to the created JSON file or None if failed
    """
    if not metadata:
        print("❌ No metadata provided")
        return None
    
    # Create albums directory if it doesn't exist
    os.makedirs(ALBUMS_DIR, exist_ok=True)
    
    # Extract key information
    artist = metadata.get('artist', 'Unknown Artist')
    # Keep only the first artist (before any comma)
    if ',' in artist:
        artist = artist.split(',')[0].strip()
        
    title = metadata.get('title', 'Unknown Album')
    year = metadata.get('year', 'Unknown Year')
    barcode = metadata.get('barcode', 'unknown')
    
    # Create a sanitized filename
    filename = sanitize_filename(f"{artist} - {title} ({year})")
    json_path = os.path.join(ALBUMS_DIR, f"{filename}.json")
    
    # Format the data in the desired structure
    album_data = {
        "Artist": artist,
        "Title": title,
        "Year": year,
        "Country": metadata.get('country', ''),
        "Genres": ", ".join(metadata.get('genres', [])),
        "Labels": ", ".join(metadata.get('labels', [])),
        "Catalog #": metadata.get('catno', ''),
        "Formats": ", ".join(metadata.get('formats', [])),
        "Discogs URL": metadata.get('discogs_url', ''),
        "Barcode": barcode,
        "Path": metadata.get('path', ''),
        "Created": datetime.now().isoformat()
    }
    
    # Write the JSON file
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(album_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Created album JSON file: {json_path}")
        return json_path
    except Exception as e:
        print(f"❌ Error creating album JSON file: {e}")
        return None

def interactive_mode():
    """Run the album JSON creator in interactive mode."""
    print("=== Album JSON Creator ===")
    print("Enter 'quit' or 'q' to exit and save progress")
    
    while True:
        barcode = input("\nScan or enter barcode [or q for quit]: ").strip()
        if barcode.lower() in ['quit', 'q']:
            print("Saving progress and updating inventory...")
            update_inventory()
            print("Done! Exiting.")
            break
        
        if not barcode:
            print("Please enter a valid barcode")
            continue
        
        # First check if the album already exists in our JSON files
        exists, json_file, album_data = find_existing_album_by_barcode(barcode)
        
        if exists:
            # Yellow color for duplicate
            print(f"\033[93m[DUPLICATE] {album_data.get('Artist')} - {album_data.get('Title')} ({album_data.get('Year')})\033[0m")
            print(f"Already exists in: {json_file}")
            
            # Ask if user wants to view the existing data
            view = input("\nView existing data? (y/n): ").strip().lower()
            if view == 'y':
                print("\n=== Existing Album Information ===")
                for key, value in album_data.items():
                    if key != "Created":  # Skip the timestamp
                        print(f"{key}: {value}")
            
            continue
        
        # If not found in JSON files, look up in the database
        metadata = lookup_barcode(barcode)
        
        if metadata:
            # Green color for new entries
            print(f"\033[92m[NEW] {metadata.get('artist')} - {metadata.get('title')} ({metadata.get('year')})\033[0m")
            
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
                # Allow manual corrections
                print("Enter corrections (leave blank to keep current value):")
                artist = input(f"Artist [{metadata.get('artist', '')}]: ").strip()
                title = input(f"Title [{metadata.get('title', '')}]: ").strip()
                year = input(f"Year [{metadata.get('year', '')}]: ").strip()
                country = input(f"Country [{metadata.get('country', '')}]: ").strip()
                genres = input(f"Genres [{', '.join(metadata.get('genres', []))}]: ").strip()
                labels = input(f"Labels [{', '.join(metadata.get('labels', []))}]: ").strip()
                catno = input(f"Catalog # [{metadata.get('catno', '')}]: ").strip()
                formats = input(f"Formats [{', '.join(metadata.get('formats', []))}]: ").strip()
                path = input(f"Path [{metadata.get('path', '')}]: ").strip()
                
                # Update metadata with corrections
                if artist: metadata['artist'] = artist
                if title: metadata['title'] = title
                if year: metadata['year'] = year
                if country: metadata['country'] = country
                if genres: metadata['genres'] = [g.strip() for g in genres.split(',')]
                if labels: metadata['labels'] = [l.strip() for l in labels.split(',')]
                if catno: metadata['catno'] = catno
                if formats: metadata['formats'] = [f.strip() for f in formats.split(',')]
                if path: metadata['path'] = path
            
            # Create the JSON file
            json_path = create_album_json(metadata)
            if json_path:
                print(f"Album JSON created at: {json_path}")
        else:
            print("No album information found for this barcode.")
            
            # Ask if user wants to manually create an album entry
            create_manual = input("\nManually create an album entry? (y/n): ").strip().lower()
            if create_manual == 'y':
                manual_metadata = {
                    'barcode': barcode,
                    'artist': input("Enter artist name: ").strip(),
                    'title': input("Enter album title: ").strip(),
                    'year': input("Enter release year: ").strip(),
                    'country': input("Enter country: ").strip(),
                    'genres': [g.strip() for g in input("Enter genres (comma separated): ").strip().split(',')],
                    'labels': [l.strip() for l in input("Enter labels (comma separated): ").strip().split(',')],
                    'catno': input("Enter catalog number: ").strip(),
                    'formats': [f.strip() for f in input("Enter formats (comma separated): ").strip().split(',')],
                    'discogs_url': input("Enter Discogs URL (optional): ").strip(),
                    'path': input("Enter album path (optional): ").strip()
                }
                
                json_path = create_album_json(manual_metadata)
                if json_path:
                    print(f"Manual album JSON created at: {json_path}")

def batch_mode(barcodes):
    """
    Process a batch of barcodes.
    
    Args:
        barcodes: List of barcode strings
    """
    print(f"Processing {len(barcodes)} barcodes in batch mode...")
    
    for barcode in barcodes:
        print(f"\nProcessing barcode: {barcode}")
        
        # First check if the album already exists in our JSON files
        exists, json_file, album_data = find_existing_album_by_barcode(barcode)
        
        if exists:
            # Yellow color for duplicate
            print(f"\033[93m[DUPLICATE] {album_data.get('Artist')} - {album_data.get('Title')} ({album_data.get('Year')})\033[0m")
            print(f"Already exists in: {json_file}")
            continue
        
        # If not found in JSON files, look up in the database
        metadata = lookup_barcode(barcode)
        
        if metadata:
            # Green color for new entries
            print(f"\033[92m[NEW] {metadata.get('artist')} - {metadata.get('title')} ({metadata.get('year')})\033[0m")
            
            json_path = create_album_json(metadata)
            if json_path:
                print(f"Album JSON created at: {json_path}")
        else:
            print(f"❌ No information found for barcode: {barcode}")

def main():
    # Create albums directory if it doesn't exist
    os.makedirs(ALBUMS_DIR, exist_ok=True)
    
    # Check if barcodes were provided as command line arguments
    if len(sys.argv) > 1:
        # First argument could be a single barcode or a file with barcodes
        first_arg = sys.argv[1]
        
        # Check if the first argument is a quit command
        if first_arg.lower() in ['quit', 'q']:
            print("Exiting.")
            return
            
        if os.path.isfile(first_arg):
            # Read barcodes from file (one per line)
            try:
                with open(first_arg, 'r') as f:
                    barcodes = [line.strip() for line in f if line.strip()]
                batch_mode(barcodes)
            except Exception as e:
                print(f"❌ Error reading barcode file: {e}")
        else:
            # Process all arguments as barcodes
            batch_mode(sys.argv[1:])
    else:
        # Run in interactive mode
        interactive_mode()
    
    # Update the master inventory file at the end of the run
    update_inventory()

if __name__ == "__main__":
    main()
