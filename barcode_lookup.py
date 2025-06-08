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
import curses
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
        artist = result['artist']
        # Keep only the first artist (before any comma)
        if ',' in artist:
            artist = artist.split(',')[0].strip()
            
        metadata = {
            'barcode': barcode,
            'discogs_id': result['id'],
            'discogs_url': f"https://www.discogs.com/release/{result['id']}",
            'title': result['title'],
            'artist': artist,
            'year': result['year'],
            'country': result['country'],
            'formats': result['format'].split(', ') if result['format'] else [],
            'labels': result['label'].split(', ') if result['label'] else [],
            'genres': result['genre'].split(', ') if result['genre'] else [],
            'catno': result['catno'],
            'path': ''  # Added path field
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

def find_all_albums_in_database(barcode):
    """
    Find all albums with the given barcode in the barcode database.
    
    Args:
        barcode: The barcode to search for
        
    Returns:
        List of album entries or empty list if not found
    """
    database = load_barcode_database()
    
    matching_albums = []
    
    # Check if this exact barcode exists
    if barcode in database:
        matching_albums.append(database[barcode])
    
    # Also check for partial matches (e.g., if barcode has extra digits)
    for db_barcode, album_data in database.items():
        if barcode in db_barcode or db_barcode in barcode:
            if album_data not in matching_albums:  # Avoid duplicates
                matching_albums.append(album_data)
    
    return matching_albums

def select_album_menu(matching_albums):
    """
    Display a menu to select from multiple matching albums.
    
    Args:
        matching_albums: List of album data dictionaries
        
    Returns:
        Selected album data or None if cancelled
    """
    if not matching_albums:
        return None
    
    if len(matching_albums) == 1:
        return matching_albums[0]
    
    def _show_menu(stdscr):
        curses.curs_set(0)  # Hide cursor
        current_row = 0
        
        # Get screen dimensions
        max_y, max_x = stdscr.getmaxyx()
        
        # Calculate menu dimensions
        menu_height = min(len(matching_albums) + 4, max_y - 2)
        menu_width = max_x - 4
        start_y = (max_y - menu_height) // 2
        start_x = 2
        
        # Create menu window
        menu_win = curses.newwin(menu_height, menu_width, start_y, start_x)
        menu_win.keypad(True)
        
        # Draw menu
        while True:
            menu_win.clear()
            menu_win.box()
            menu_win.addstr(1, 2, "Multiple albums found with this barcode. Select one:")
            
            # Display albums
            for i, album_data in enumerate(matching_albums):
                # Highlight the current selection
                if i == current_row:
                    menu_win.attron(curses.A_REVERSE)
                
                # Format album info
                album_info = f"{album_data.get('artist', 'Unknown')} - {album_data.get('album', 'Unknown')} ({album_data.get('year', 'Unknown')})"
                
                # Truncate if too long
                if len(album_info) > menu_width - 6:
                    album_info = album_info[:menu_width - 9] + "..."
                
                # Display album info
                if i < menu_height - 4:  # Ensure we don't go beyond window bounds
                    menu_win.addstr(i + 2, 2, album_info)
                
                if i == current_row:
                    menu_win.attroff(curses.A_REVERSE)
            
            # Add instructions
            menu_win.addstr(menu_height - 1, 2, "Use arrow keys to navigate, Enter to select, Esc to cancel")
            
            # Update the window
            menu_win.refresh()
            
            # Get user input
            key = menu_win.getch()
            
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(matching_albums) - 1:
                current_row += 1
            elif key == 10:  # Enter key
                return current_row
            elif key == 27:  # Escape key
                return -1
    
    try:
        selected = curses.wrapper(_show_menu)
        if selected >= 0:
            return matching_albums[selected]
        return None
    except Exception as e:
        print(f"Error displaying menu: {e}")
        # Fallback to simple selection
        print("\nMultiple albums found with this barcode:")
        for i, album_data in enumerate(matching_albums):
            print(f"{i+1}. {album_data.get('artist', 'Unknown')} - {album_data.get('album', 'Unknown')} ({album_data.get('year', 'Unknown')})")
        
        try:
            choice = int(input("\nSelect album number (0 to cancel): "))
            if 1 <= choice <= len(matching_albums):
                return matching_albums[choice-1]
        except (ValueError, IndexError):
            pass
        
        return None

def associate_barcode_with_album(barcode, metadata, artist=None, album=None, path=None):
    """
    Associate a barcode with an album in the database.
    
    Args:
        barcode: The barcode string
        metadata: The metadata from the local database
        artist: Optional artist name override
        album: Optional album name override
        path: Optional path to the album
    """
    database = load_barcode_database()
    
    # Use provided artist/album or extract from metadata
    artist_name = artist or metadata.get('artist', '')
    # Keep only the first artist (before any comma)
    if ',' in artist_name:
        artist_name = artist_name.split(',')[0].strip()
        
    album_name = album or metadata.get('title', '')
    album_path = path or metadata.get('path', '')
    
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
        'path': album_path,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add to database
    database[barcode] = entry
    save_barcode_database(database)
    
    print(f"✅ Associated barcode {barcode} with {artist_name} - {album_name}")

def interactive_mode():
    """Run the barcode lookup tool in interactive mode."""
    print("=== Barcode Lookup Tool ===")
    print("Enter 'quit' or 'q' to exit and save progress")
    
    while True:
        barcode = input("\nScan or enter barcode [or q for quit]: ").strip()
        if barcode.lower() in ['quit', 'q']:
            print("Saving progress...")
            print("Done! Exiting.")
            break
        
        if not barcode:
            print("Please enter a valid barcode")
            continue
        
        # First check if the album already exists in our database
        matching_albums = find_all_albums_in_database(barcode)
        
        if matching_albums:
            # Yellow color for duplicate
            print(f"\033[93m[DUPLICATE] Found {len(matching_albums)} album(s) with this barcode\033[0m")
            
            # Let user select from matching albums
            selected = select_album_menu(matching_albums)
            
            if selected:
                print(f"Selected: {selected.get('artist')} - {selected.get('album')} ({selected.get('year')})")
                
                # Display the selected album details
                print("\n=== Album Information ===")
                for key, value in selected.items():
                    if key != "timestamp":  # Skip the timestamp
                        print(f"{key}: {value}")
                
                continue
            else:
                print("No album selected.")
                
                # Ask if user wants to continue with database lookup
                lookup_db = input("\nLook up in Discogs database? (y/n): ").strip().lower()
                if lookup_db != 'y':
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
                    path = input("Enter album path (optional): ").strip()
                    associate_barcode_with_album(barcode, metadata, artist, album, path)
                else:
                    print("Skipping this barcode.")
            else:
                # Ask if user wants to associate this barcode with the album
                associate = input("Associate this barcode with the album? (y/n): ").strip().lower()
                if associate == 'y':
                    path = input("Enter album path (optional): ").strip()
                    associate_barcode_with_album(barcode, metadata, path=path)
        else:
            print("No album information found for this barcode.")
            
            # Ask if user wants to manually associate this barcode
            associate = input("\nManually associate this barcode with an album? (y/n): ").strip().lower()
            if associate == 'y':
                artist = input("Enter artist name: ").strip()
                album = input("Enter album name: ").strip()
                path = input("Enter album path (optional): ").strip()
                
                # Create minimal metadata
                minimal_metadata = {
                    'artist': artist,
                    'title': album,
                    'path': path
                }
                
                associate_barcode_with_album(barcode, minimal_metadata, artist, album, path)

def main():
    # Create data directory if it doesn't exist
    os.makedirs(os.path.join(SCRIPT_DIR, "data"), exist_ok=True)
    
    # Check if barcode was provided as command line argument
    if len(sys.argv) > 1:
        barcode = sys.argv[1]
        if barcode.lower() in ['quit', 'q']:
            print("Exiting.")
            return
        
        # First check if the album already exists in our database
        matching_albums = find_all_albums_in_database(barcode)
        
        if matching_albums:
            # Yellow color for duplicate
            print(f"\033[93m[DUPLICATE] Found {len(matching_albums)} album(s) with this barcode\033[0m")
            
            # Let user select from matching albums
            selected = select_album_menu(matching_albums)
            
            if selected:
                print(f"Selected: {selected.get('artist')} - {selected.get('album')} ({selected.get('year')})")
                
                # Pretty print the selected album details
                print(json.dumps(selected, indent=2))
                return
            else:
                print("No album selected.")
                
                # Ask if user wants to continue with database lookup
                lookup_db = input("\nLook up in Discogs database? (y/n): ").strip().lower()
                if lookup_db != 'y':
                    return
            
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
                    path = input("Enter album path (optional): ").strip()
                    associate_barcode_with_album(barcode, metadata, artist, album, path)
                else:
                    print("Skipping this barcode.")
            else:
                # Ask if user wants to associate this barcode with the album
                associate = input("Associate this barcode with the album? (y/n): ").strip().lower()
                if associate == 'y':
                    path = input("Enter album path (optional): ").strip()
                    associate_barcode_with_album(barcode, metadata, path=path)
    else:
        # Run in interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
