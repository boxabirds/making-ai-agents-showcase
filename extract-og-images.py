#!/usr/bin/env python3
"""
Extract og:images from organization websites linked in GitHub repos.
Updates oss-agent-makers.csv with a new Image column.
"""

import csv
import time
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Headers to appear more like a regular browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_org_website_from_github(github_url):
    """Extract organization website URL from GitHub repo page."""
    try:
        response = requests.get(github_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the website link in the repo header
        # GitHub uses this pattern for external links
        website_link = soup.find('a', {
            'role': 'link',
            'target': '_blank',
            'rel': 'noopener noreferrer nofollow'
        })
        
        if website_link and website_link.get('href'):
            website_url = website_link['href']
            # Ensure it's a full URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            logger.info(f"Found website: {website_url}")
            return website_url
            
    except Exception as e:
        logger.error(f"Error fetching GitHub page {github_url}: {e}")
    
    return None

def get_og_image_from_website(website_url):
    """Extract og:image from a website."""
    try:
        response = requests.get(website_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for og:image meta tag
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            
            # Make relative URLs absolute
            if image_url.startswith('/'):
                parsed = urlparse(website_url)
                image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
            elif not image_url.startswith(('http://', 'https://')):
                image_url = website_url.rstrip('/') + '/' + image_url
                
            logger.info(f"Found og:image: {image_url}")
            return image_url
            
    except Exception as e:
        logger.error(f"Error fetching website {website_url}: {e}")
    
    return None

def get_github_avatar(github_url):
    """Extract GitHub organization/user avatar as fallback."""
    try:
        # Extract owner from GitHub URL
        match = re.match(r'https://github\.com/([^/]+)/', github_url)
        if match:
            owner = match.group(1)
            # GitHub avatar URL pattern
            avatar_url = f"https://github.com/{owner}.png"
            return avatar_url
    except Exception as e:
        logger.error(f"Error extracting GitHub avatar: {e}")
    
    return None

def process_csv():
    """Main function to process the CSV file."""
    input_file = 'oss-agent-makers.csv'
    output_file = 'oss-agent-makers-with-images.csv'
    
    # Read existing data
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Process each row
    for i, row in enumerate(rows):
        project = row['Project']
        github_url = row['Github URL']
        
        logger.info(f"\nProcessing {i+1}/{len(rows)}: {project}")
        
        # Skip if GitHub URL is malformed
        if not github_url.startswith('https://github.com/'):
            logger.warning(f"Skipping invalid GitHub URL: {github_url}")
            row['Image'] = ''
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
        
        # Be respectful with rate limiting
        time.sleep(1)
        
        # Save progress every 10 items
        if (i + 1) % 10 == 0:
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