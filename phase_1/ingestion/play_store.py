from google_play_scraper import reviews, Sort
from typing import List
from ..models import Review, Source
from datetime import datetime

def fetch_play_store_reviews(app_id: str, country: str = "in", count: int = 10000) -> List[Review]:
    """
    Fetches reviews from the Google Play Store using google-play-scraper.
    """
    result, _ = reviews(
        app_id,
        lang='en', # Default to English
        country=country,
        sort=Sort.NEWEST,
        count=count
    )
    
    parsed_reviews = []
    for item in result:
        try:
            parsed_reviews.append(Review(
                review_id=item.get("reviewId"),
                source=Source.PLAY_STORE,
                rating=item.get("score"),
                title=None, # Play store reviews often don't have titles in the same way
                content=item.get("content"),
                author=item.get("userName"),
                timestamp=item.get("at")
            ))
        except Exception as e:
            print(f"Error parsing Play Store review: {e}")
            
    return parsed_reviews
