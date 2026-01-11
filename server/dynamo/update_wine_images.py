#!/usr/bin/env python3
"""
Update wine reference label images by searching Vivino via Google Images
Focuses on wine labels only, not full bottles
"""
import os
import sys
import time

# Add parent directory to path to import server modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from server.dynamo.storage import (
    load_wine_references as dynamodb_load_wine_references,
    update_wine_reference as dynamodb_update_wine_reference
)
from server.storage import deserialize_wine_reference, serialize_wine_reference

def search_vivino_label(query):
    """
    Search Google Images specifically for Vivino wine label images
    Focuses on labels only, not full bottles
    """
    # Use the fallback method which will search for Vivino specifically
    return search_vivino_images(query)

def search_vivino_images(query):
    """
    Search Google Images specifically for Vivino wine label images
    Uses site:vivino.com to only get results from Vivino
    Adds 'label' to focus on labels rather than full bottles
    """
    return search_vivino_images_scrape(query)

def search_vivino_images_scrape(query):
    """
    Search Google Images specifically for Vivino wine label images
    Uses site:vivino.com to restrict results to Vivino only
    Focuses on labels by adding 'label' to the search query
    """
    try:
        import requests
        from urllib.parse import quote
        import re
        import json
        
        # Search specifically on Vivino for wine labels
        # Use site:vivino.com to restrict to Vivino only
        # Add 'label' to focus on labels rather than full bottles
        search_query = quote(f'site:vivino.com {query} wine label')
        url = f"https://www.google.com/search?q={search_query}&tbm=isch&safe=active"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text
        
        # Method 1: Look for "ou":"URL" pattern (Google's embedded image data)
        # Prioritize Vivino URLs
        matches = re.findall(r'"ou":"(https?://[^"]+)"', html)
        vivino_urls = []
        other_urls = []
        
        for match in matches[:30]:  # Check first 30 matches
            match_lower = match.lower()
            if ('google' not in match_lower and 'gstatic' not in match_lower and 
                'doubleclick' not in match_lower):
                # Check if it's a Vivino URL
                if 'vivino.com' in match_lower:
                    # Verify it looks like an image URL
                    if any(ext in match_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'image' in match_lower or 'label' in match_lower:
                        vivino_urls.append(match)
                else:
                    # Keep other URLs as backup
                    if any(ext in match_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        other_urls.append(match)
        
        # Prefer Vivino URLs
        if vivino_urls:
            return vivino_urls[0]
        
        # Method 2: Look for AF_initDataCallback which contains image data
        callback_matches = re.findall(r'AF_initDataCallback\([^)]*key:\'ds:1\'[^)]*data:([^,}]+)', html)
        for match in callback_matches:
            try:
                # Try to parse as JSON
                data = json.loads(match)
                # Recursively search for Vivino image URLs in the data structure
                def find_vivino_urls(obj):
                    urls = []
                    if isinstance(obj, dict):
                        for v in obj.values():
                            if isinstance(v, str) and v.startswith('http'):
                                if 'vivino.com' in v.lower():
                                    if any(ext in v.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'image' in v.lower() or 'label' in v.lower():
                                        urls.append(v)
                            result = find_vivino_urls(v)
                            if result:
                                urls.extend(result)
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_vivino_urls(item)
                            if result:
                                urls.extend(result)
                    return urls
                
                urls = find_vivino_urls(data)
                if urls:
                    return urls[0]
            except:
                continue
        
        # Method 3: Look for Vivino image URLs in script tags
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for script in script_matches:
            # Look for Vivino image URLs
            vivino_pattern = r'https?://[^\s"<>\)]*vivino\.com[^\s"<>\)]+\.(?:jpg|jpeg|png|gif|webp)'
            matches = re.findall(vivino_pattern, script, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Method 4: Direct pattern matching for Vivino CDN URLs
        # Vivino typically uses patterns like: https://images.vivino.com/...
        vivino_cdn_pattern = r'https?://[^\s"<>\)]*images\.vivino\.com[^\s"<>\)]+'
        matches = re.findall(vivino_cdn_pattern, html, re.IGNORECASE)
        if matches:
            # Filter for image extensions
            for match in matches:
                if any(ext in match.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'label' in match.lower():
                    return match
            # If no extension, return first match (Vivino CDN URLs might not have extensions)
            return matches[0]
        
        # If no Vivino URLs found, return None (we want Vivino specifically)
        return None
    except Exception as e:
        return None

def build_search_query(wine):
    """Build a search query from wine data"""
    parts = []
    
    if wine.get('name'):
        parts.append(wine['name'])
    if wine.get('producer'):
        parts.append(wine['producer'])
    if wine.get('vintage'):
        parts.append(str(wine['vintage']))
    
    return ' '.join(parts)

def update_wine_images():
    """Update all wine reference label images in DynamoDB"""
    print("Loading wine references from DynamoDB...")
    wine_references = dynamodb_load_wine_references()
    
    if not wine_references:
        print("No wine references found in DynamoDB.")
        return False
    
    print(f"Found {len(wine_references)} wine references")
    print("Starting to update image URLs from Vivino (via Google Images)...")
    print("Searching specifically for wine labels (not full bottles)...")
    print("This may take a while due to rate limiting...\n")
    
    updated_count = 0
    failed_count = 0
    
    for i, wine in enumerate(wine_references, 1):
        wine_id = wine.get('id', 'unknown')
        wine_name = wine.get('name', 'Unknown')
        
        # Skip if already has an image URL
        if wine.get('labelImageUrl'):
            print(f"[{i}/{len(wine_references)}] Skipping {wine_name} (already has image)")
            continue
        
        # Build search query
        search_query = build_search_query(wine)
        print(f"[{i}/{len(wine_references)}] Searching for: {search_query}")
        
        # Search for Vivino label image
        try:
            image_url = search_vivino_label(search_query)
            
            if image_url:
                wine['labelImageUrl'] = image_url
                # Update in DynamoDB
                dynamodb_update_wine_reference(wine)
                print(f"  ✓ Updated: {image_url[:80]}...")
                updated_count += 1
            else:
                print(f"  ✗ No image found")
                failed_count += 1
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:50]}")
            failed_count += 1
        
        # Rate limiting - be respectful
        time.sleep(0.5)  # Wait 0.5 seconds between requests
    
    print(f"\n✓ Complete!")
    print(f"  Updated: {updated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(wine_references)}")
    
    return True

if __name__ == '__main__':
    try:
        success = update_wine_images()
        if not success:
            print("\nFailed to update wine images.")
            exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress...")
        exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
