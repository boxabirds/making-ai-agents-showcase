#!/usr/bin/env python3
"""
Enhanced version: Download organization images from CSV and save them to chat/assets/ directory
This version also tries to extract images from the HTML page itself.
"""

import csv
import requests
from urllib.parse import urlparse, urljoin
from pathlib import Path
import time
import re
from bs4 import BeautifulSoup

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

def extract_images_from_html(url):
    """Extract potential logo/image URLs from the HTML page."""
    images = []
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        # Look for Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(urljoin(base_url, og_image['content']))
        
        # Look for Twitter image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            images.append(urljoin(base_url, twitter_image['content']))
        
        # Look for apple touch icon
        apple_icon = soup.find('link', rel='apple-touch-icon')
        if apple_icon and apple_icon.get('href'):
            images.append(urljoin(base_url, apple_icon['href']))
        
        # Look for favicon link tags
        for rel in ['icon', 'shortcut icon']:
            icon = soup.find('link', rel=rel)
            if icon and icon.get('href'):
                images.append(urljoin(base_url, icon['href']))
        
        # Look for logo in common places
        for tag in soup.find_all(['img', 'image']):
            src = tag.get('src', '')
            alt = tag.get('alt', '').lower()
            class_name = ' '.join(tag.get('class', [])).lower()
            id_name = tag.get('id', '').lower()
            
            if any(keyword in src.lower() + alt + class_name + id_name 
                   for keyword in ['logo', 'brand', 'icon']):
                images.append(urljoin(base_url, src))
        
    except Exception as e:
        print(f"  Error parsing HTML: {e}")
    
    return images

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
            
            # First, extract images from the HTML page
            html_images = extract_images_from_html(org_url)
            
            # Parse the base URL
            parsed = urlparse(org_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Combine HTML-extracted images with standard locations
            urls_to_try = html_images + [
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
            ]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls_to_try:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            # Try each URL
            downloaded = False
            for url in unique_urls:
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