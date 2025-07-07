#!/usr/bin/env python3
"""
Test extraction of og:images for a few sample projects.
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def test_single_project(github_url):
    """Test extraction for a single project."""
    print(f"\nTesting: {github_url}")
    
    try:
        # Step 1: Get GitHub page
        response = requests.get(github_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for website link - check different patterns
        website_url = None
        
        # Pattern 1: In the about section
        about_link = soup.find('a', {'rel': 'nofollow'})
        if about_link and 'href' in about_link.attrs:
            href = about_link['href']
            if not href.startswith('https://github.com'):
                website_url = href
                print(f"Found website (pattern 1): {website_url}")
        
        # Pattern 2: Look for span with website icon
        if not website_url:
            website_span = soup.find('span', {'class': 'flex-auto'})
            if website_span:
                link = website_span.find_parent('a')
                if link and 'href' in link.attrs:
                    website_url = link['href']
                    print(f"Found website (pattern 2): {website_url}")
        
        if website_url:
            # Step 2: Get og:image from website
            try:
                web_response = requests.get(website_url, headers=HEADERS, timeout=10)
                web_response.raise_for_status()
                
                web_soup = BeautifulSoup(web_response.text, 'html.parser')
                og_image = web_soup.find('meta', property='og:image')
                
                if og_image and 'content' in og_image.attrs:
                    print(f"Found og:image: {og_image['content']}")
                else:
                    print("No og:image found")
                    
            except Exception as e:
                print(f"Error fetching website: {e}")
        else:
            print("No organization website found")
            
    except Exception as e:
        print(f"Error: {e}")

# Test a few projects
test_projects = [
    "https://github.com/langchain-ai/langgraph-swarm-py",
    "https://github.com/pydantic/pydantic-ai",
    "https://github.com/kortix-ai/suna"
]

for url in test_projects:
    test_single_project(url)