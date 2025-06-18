#!/usr/bin/env python3
"""
Download organization images from CSV and save them to chat/assets/ directory
"""

import csv
import requests
from urllib.parse import urlparse
from pathlib import Path
import time

def download_image(url, save_path):
    """Download an image from URL and save it to the specified path."""
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Write the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error downloading: {e}")
        return False

def get_file_extension(url):
    """Get the file extension from URL."""
    # Try to get extension from URL
    path = urlparse(url).path
    if '.' in path:
        ext = path.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']:
            return ext
    
    # Otherwise default to png
    return 'png'

def main():
    # Setup paths
    csv_file = 'oss-agent-makers-with-images.csv'
    assets_dir = Path('chat/assets')
    
    # Create assets directory if it doesn't exist
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Read CSV and process each row
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            project = row.get('Project', '')
            org_url = row.get('Org URL', '')
            
            # Handle None values
            if project is None:
                project = ''
            if org_url is None:
                org_url = ''
                
            project = project.strip()
            org_url = org_url.strip()
            
            # Skip if no project name or org URL
            if not project or not org_url:
                continue
            
            print(f"\nProcessing {project}...")
            print(f"  Org URL: {org_url}")
            
            # Clean project name for filename
            filename_base = project.replace(' ', '_').replace('/', '_')
            
            # Try to download favicon or logo from the org URL
            urls_to_try = []
            
            # Parse the base URL
            parsed = urlparse(org_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Common logo/favicon locations
            urls_to_try.extend([
                f"{base_url}/favicon.ico",
                f"{base_url}/favicon.png",
                f"{base_url}/logo.png",
                f"{base_url}/logo.svg",
                f"{base_url}/images/logo.png",
                f"{base_url}/img/logo.png",
                f"{base_url}/assets/logo.png",
                f"{base_url}/static/logo.png",
                f"{base_url}/apple-touch-icon.png",
                f"{base_url}/android-chrome-192x192.png"
            ])
            
            # Try each URL
            downloaded = False
            for url in urls_to_try:
                try:
                    # Check if URL exists
                    response = requests.head(url, timeout=5, allow_redirects=True, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        ext = get_file_extension(url)
                        save_path = assets_dir / f"{filename_base}.{ext}"
                        
                        print(f"  Found image at: {url}")
                        if download_image(url, save_path):
                            print(f"  ✓ Saved to: {save_path}")
                            downloaded = True
                            break
                except:
                    continue
            
            if not downloaded:
                print(f"  ✗ Could not find downloadable image for {project}")
            
            # Small delay to be respectful
            time.sleep(0.5)
    
    print("\n✅ Download complete!")
    
    # List downloaded files
    print("\nDownloaded files:")
    for file in sorted(assets_dir.glob('*')):
        if file.is_file() and file.name != '.gitkeep':
            print(f"  {file.name}")

if __name__ == "__main__":
    main()