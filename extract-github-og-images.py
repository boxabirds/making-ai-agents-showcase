#!/usr/bin/env python3
"""
Extract og:image URLs directly from GitHub repository pages.
Overwrites oss-agent-makers-with-images.csv with GitHub's og:image URLs.
"""

import csv
import time
import re
import subprocess
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_github_og_image(github_url):
    """Extract og:image from GitHub repository page."""
    try:
        # Use curl to get the page content
        result = subprocess.run(['curl', '-s', github_url], capture_output=True, text=True)
        html_content = result.stdout
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the og:image meta tag
        # <meta property="og:image" content="https://opengraph.githubassets.com/...">
        og_image_tag = soup.find('meta', property='og:image')
        
        if og_image_tag and og_image_tag.get('content'):
            og_image_url = og_image_tag['content']
            logger.info(f"Found og:image: {og_image_url}")
            return og_image_url
        else:
            logger.warning(f"No og:image found for {github_url}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching {github_url}: {e}")
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
        github_url = row.get('Github URL', '').strip()
        
        logger.info(f"\nProcessing {i+1}/{len(rows)}: {project}")
        
        # Skip if GitHub URL is malformed
        if not github_url or not github_url.startswith('https://github.com/'):
            logger.warning(f"Skipping invalid GitHub URL: {github_url}")
            row['Image'] = ''
            continue
        
        # Get GitHub og:image
        og_image_url = get_github_og_image(github_url)
        
        # Add image URL to row
        row['Image'] = og_image_url or ''
        
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