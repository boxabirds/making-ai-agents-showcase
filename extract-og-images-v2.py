#!/usr/bin/env python3
"""
Extract og:images from organization websites linked in GitHub repos.
Updates oss-agent-makers.csv with a new Image column.
"""

import csv
import time
import re
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Headers to appear more like a regular browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

def get_org_website_from_github(github_url):
    """Extract organization website URL from GitHub repo page."""
    try:
        # Use curl to get the page content (often more reliable than requests for GitHub)
        import subprocess
        result = subprocess.run(['curl', '-s', github_url], capture_output=True, text=True)
        html_content = result.stdout
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the website link with the specific pattern mentioned
        # Pattern: <a title="https://www.suna.so" role="link" target="_blank" rel="noopener noreferrer nofollow" class="text-bold" href="https://www.suna.so">
        website_links = soup.find_all('a', {
            'role': 'link',
            'target': '_blank',
            'class': 'text-bold'
        })
        
        for link in website_links:
            href = link.get('href', '')
            title = link.get('title', '')
            # Check if this is an external link (not GitHub)
            if href and not href.startswith(('https://github.com', '/')) and ('http' in href):
                logger.info(f"Found website: {href}")
                return href
        
        # Alternative: Look for links with rel="noopener noreferrer"
        alt_links = soup.find_all('a', {'rel': re.compile('noopener.*noreferrer')})
        for link in alt_links:
            href = link.get('href', '')
            if href and not href.startswith(('https://github.com', '/')) and ('http' in href):
                logger.info(f"Found website (alt pattern): {href}")
                return href
            
    except Exception as e:
        logger.error(f"Error fetching GitHub page {github_url}: {e}")
    
    return None

def get_og_image_from_website(website_url):
    """Extract og:image from a website."""
    try:
        response = requests.get(website_url, headers=HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for og:image meta tag
        og_image = soup.find('meta', property='og:image')
        if not og_image:
            # Try alternative attribute name
            og_image = soup.find('meta', attrs={'name': 'og:image'})
        
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            
            # Make relative URLs absolute
            image_url = urljoin(website_url, image_url)
                
            logger.info(f"Found og:image: {image_url}")
            return image_url
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching website {website_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error for {website_url}: {e}")
    
    return None

def get_github_avatar(github_url):
    """Extract GitHub organization/user avatar as fallback."""
    try:
        # Extract owner from GitHub URL
        match = re.match(r'https://github\.com/([^/]+)/', github_url)
        if match:
            owner = match.group(1)
            # GitHub avatar URL pattern (high quality)
            avatar_url = f"https://github.com/{owner}.png?size=400"
            return avatar_url
    except Exception as e:
        logger.error(f"Error extracting GitHub avatar: {e}")
    
    return None

def process_csv():
    """Main function to process the CSV file."""
    input_file = 'oss-agent-makers.csv'
    output_file = 'oss-agent-makers-with-images.csv'
    progress_file = 'og-extraction-progress.json'
    
    # Load progress if exists
    progress = {}
    try:
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    except:
        pass
    
    # Read existing data
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Process each row
    for i, row in enumerate(rows):
        project = row['Project']
        github_url = row.get('Github URL', '').strip()
        
        logger.info(f"\nProcessing {i+1}/{len(rows)}: {project}")
        
        # Skip if already processed
        if project in progress:
            row['Image'] = progress[project]
            logger.info(f"Already processed, using cached result")
            continue
        
        # Skip if GitHub URL is malformed
        if not github_url or not github_url.startswith('https://github.com/'):
            logger.warning(f"Skipping invalid GitHub URL: {github_url}")
            row['Image'] = ''
            progress[project] = ''
            continue
        
        # Try to get organization website
        org_website = get_org_website_from_github(github_url)
        
        image_url = None
        
        # If we found an org website, try to get og:image
        if org_website:
            image_url = get_og_image_from_website(org_website)
        
        # Fallback to GitHub avatar
        if not image_url:
            logger.info("Falling back to GitHub avatar")
            image_url = get_github_avatar(github_url)
        
        # Add image URL to row
        row['Image'] = image_url or ''
        progress[project] = row['Image']
        
        # Save progress
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        # Be respectful with rate limiting
        time.sleep(2)
        
        # Save CSV progress every 5 items
        if (i + 1) % 5 == 0:
            save_progress(rows, output_file)
    
    # Final save
    save_progress(rows, output_file)
    logger.info(f"\nCompleted! Results saved to {output_file}")

def save_progress(rows, output_file):
    """Save current progress to CSV."""
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=['Project', 'Github URL', 'Image'])
            writer.writeheader()
            writer.writerows(rows)
    logger.info(f"Progress saved to {output_file}")

if __name__ == "__main__":
    process_csv()