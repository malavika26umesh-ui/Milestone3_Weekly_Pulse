import feedparser
import requests
from datetime import datetime
from typing import List
from ..models import Review, Source

def fetch_app_store_reviews(app_id: str, country: str = "in") -> List[Review]:
    """
    Fetches reviews from the Apple App Store using the RSS feed (paginated up to 10 pages).
    """
    reviews_list = []
    
    # Apple RSS allows up to 10 pages, each with 50 reviews
    for page in range(1, 11):
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                break
                
            # The first entry of the first page is app metadata, skip it if it doesn't have a rating
            for entry in entries:
                if "im:rating" not in entry:
                    continue
                    
                reviews_list.append(Review(
                    review_id=entry.get("id", {}).get("label"),
                    source=Source.APP_STORE,
                    rating=int(entry.get("im:rating", {}).get("label")),
                    title=entry.get("title", {}).get("label"),
                    content=entry.get("content", {}).get("label"),
                    author=entry.get("author", {}).get("name", {}).get("label"),
                    timestamp=datetime.now() # Using current time as RSS JSON lacks precise individual entry timestamps
                ))
        except Exception as e:
            print(f"Error fetching page {page} for App Store: {e}")
            break
            
    return reviews_list
