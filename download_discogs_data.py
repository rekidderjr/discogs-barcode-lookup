#!/usr/bin/env python3
"""
Accelerated Discogs Data Downloader for Music Collection Manager

This script downloads the Discogs data dumps using multipart downloads
for faster and more reliable transfers.
"""

import os
import sys
import requests
import hashlib
import concurrent.futures
import threading
from tqdm import tqdm

# Base URL for Discogs data dumps
BASE_URL = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2025/"

# Files to download - we'll focus on just the releases file for now
FILES = [
    "discogs_20250601_releases.xml.gz"
]

# Local directory to store the files
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Number of concurrent download chunks
NUM_CHUNKS = 8

# Size of each chunk in bytes (50MB)
CHUNK_SIZE = 50 * 1024 * 1024

class MultipartDownloader:
    def __init__(self, url, output_path, num_chunks=8):
        self.url = url
        self.output_path = output_path
        self.num_chunks = num_chunks
        self.file_size = 0
        self.lock = threading.Lock()
        self.progress_bar = None
        
    def get_file_size(self):
        """Get the size of the file to download."""
        response = requests.head(self.url)
        self.file_size = int(response.headers.get('content-length', 0))
        return self.file_size
        
    def download_chunk(self, start, end, chunk_number):
        """Download a specific chunk of the file."""
        headers = {'Range': f'bytes={start}-{end}'}
        response = requests.get(self.url, headers=headers, stream=True)
        
        # Create a temporary file for this chunk
        chunk_file = f"{self.output_path}.part{chunk_number}"
        
        with open(chunk_file, 'wb') as f:
            for data in response.iter_content(1024 * 1024):  # 1MB buffer
                if data:
                    f.write(data)
                    with self.lock:
                        self.progress_bar.update(len(data))
        
        return chunk_file
        
    def download(self):
        """Download the file in multiple parts and combine them."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Get file size
        file_size = self.get_file_size()
        
        # Check if file already exists and has the correct size
        if os.path.exists(self.output_path) and os.path.getsize(self.output_path) == file_size:
            print(f"✅ {os.path.basename(self.output_path)} already downloaded (size match)")
            return True
            
        # Calculate chunk sizes
        chunk_size = file_size // self.num_chunks
        chunks = []
        
        for i in range(self.num_chunks):
            start = i * chunk_size
            end = (i + 1) * chunk_size - 1 if i < self.num_chunks - 1 else file_size - 1
            chunks.append((start, end, i))
            
        # Create progress bar
        self.progress_bar = tqdm(
            desc=f"Downloading {os.path.basename(self.url)}",
            total=file_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            file=sys.stdout
        )
        
        # Download chunks in parallel
        chunk_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_chunks) as executor:
            futures = [executor.submit(self.download_chunk, start, end, i) for start, end, i in chunks]
            for future in concurrent.futures.as_completed(futures):
                chunk_files.append(future.result())
                
        self.progress_bar.close()
        
        # Combine chunks
        print(f"Combining chunks into {self.output_path}...")
        with open(self.output_path, 'wb') as outfile:
            for chunk_file in sorted(chunk_files):
                with open(chunk_file, 'rb') as infile:
                    outfile.write(infile.read())
                    
        # Remove chunk files
        for chunk_file in chunk_files:
            os.remove(chunk_file)
            
        print(f"✅ Downloaded {os.path.basename(self.output_path)}")
        return True

def main():
    # Create the data directory
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Download the releases file with multipart download
    for file_name in FILES:
        file_url = BASE_URL + file_name
        file_path = os.path.join(DATA_DIR, file_name)
        
        print(f"\n📥 Processing {file_name}...")
        
        # Use multipart downloader
        downloader = MultipartDownloader(file_url, file_path, NUM_CHUNKS)
        downloader.download()
    
    print("\n✅ Download complete.")
    print(f"📁 Data files are stored in the '{DATA_DIR}' directory.")
    print("\nNext step: Process the data with process_discogs_data.py")

if __name__ == "__main__":
    main()
