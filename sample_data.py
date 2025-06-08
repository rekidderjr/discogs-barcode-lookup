#!/usr/bin/env python3
"""
Sample Data Generator for Barcode Tool

This script creates a small sample SQLite database with some hardcoded entries
for testing the barcode lookup functionality without downloading the full Discogs data.
"""

import os
import sqlite3

# Get the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "data", "discogs_barcodes.db")

# Sample data with some popular albums
SAMPLE_DATA = [
    {
        "id": 1234567,
        "barcode": "075596082921",
        "title": "Unplugged",
        "artist": "Eric Clapton",
        "year": 1992,
        "country": "US",
        "format": "CD, Album",
        "label": "Reprise Records, Warner Bros. Records",
        "genre": "Rock, Blues",
        "catno": "9 45024-2"
    },
    {
        "id": 2345678,
        "barcode": "075678235320",
        "title": "Jagged Little Pill",
        "artist": "Alanis Morissette",
        "year": 1995,
        "country": "US",
        "format": "CD, Album",
        "label": "Maverick, Reprise Records",
        "genre": "Rock, Pop Rock",
        "catno": "9 45901-2"
    },
    {
        "id": 3456789,
        "barcode": "731453429529",
        "title": "Supernatural",
        "artist": "Santana",
        "year": 1999,
        "country": "US",
        "format": "CD, Album",
        "label": "Arista",
        "genre": "Latin Rock, Pop Rock",
        "catno": "19080-2"
    },
    {
        "id": 4567890,
        "barcode": "074646938423",
        "title": "Thriller",
        "artist": "Michael Jackson",
        "year": 1982,
        "country": "US",
        "format": "CD, Album, Reissue",
        "label": "Epic, Sony Music",
        "genre": "Pop, Funk, Soul",
        "catno": "EK 65802"
    },
    {
        "id": 5678901,
        "barcode": "720642442524",
        "title": "Nevermind",
        "artist": "Nirvana",
        "year": 1991,
        "country": "US",
        "format": "CD, Album",
        "label": "DGC, Geffen Records",
        "genre": "Rock, Grunge",
        "catno": "DGCD-24425"
    }
]

def create_sample_database():
    """Create a sample SQLite database with hardcoded entries."""
    print("🔧 Creating sample database...")
    
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
    
    # Clear existing data
    cursor.execute("DELETE FROM releases")
    
    # Insert sample data
    for entry in SAMPLE_DATA:
        cursor.execute('''
        INSERT INTO releases 
        (id, barcode, title, artist, year, country, format, label, genre, catno)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry["id"],
            entry["barcode"],
            entry["title"],
            entry["artist"],
            entry["year"],
            entry["country"],
            entry["format"],
            entry["label"],
            entry["genre"],
            entry["catno"]
        ))
    
    conn.commit()
    conn.close()
    
    print("✅ Sample database created with the following entries:")
    for entry in SAMPLE_DATA:
        print(f"  • {entry['artist']} - {entry['title']} (Barcode: {entry['barcode']})")
    
    print("\nYou can now use barcode_lookup.py to look up these barcodes.")

if __name__ == "__main__":
    create_sample_database()
