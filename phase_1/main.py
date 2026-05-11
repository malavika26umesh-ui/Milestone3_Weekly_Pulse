import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from dotenv import load_dotenv
from .models import Review, ProductConfig
from .ingestion import fetch_app_store_reviews, fetch_play_store_reviews

load_dotenv()

# Pre-configured products for easy testing
PRODUCTS = {
    "groww": ProductConfig(
        name="Groww",
        app_store_id="1404871703",
        play_store_id="com.nextbillion.groww"
    ),
    "indmoney": ProductConfig(
        name="INDMoney",
        app_store_id="1424386551",
        play_store_id="com.indwealth"
    )
}

def save_reviews(reviews: List[Review], product_name: str) -> str:
    os.makedirs("data", exist_ok=True)
    filename = f"data/{product_name.lower()}_reviews_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Convert reviews to dict for JSON serialization
    data = [review.model_dump(mode='json') for review in reviews]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"Successfully saved {len(reviews)} reviews to {filename}")
    return filename

def run_ingestion(product_key: str, weeks: int = 8) -> Optional[str]:
    product_key = product_key.lower()
    if product_key not in PRODUCTS:
        print(f"Product {product_key} not found in config.")
        return None

    config = PRODUCTS[product_key]
    all_reviews = []
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    
    # 1. Fetch App Store
    if config.app_store_id:
        print(f"Fetching App Store reviews for {config.name}...")
        app_reviews = fetch_app_store_reviews(config.app_store_id, config.country)
        # Filter by date
        app_reviews = [r for r in app_reviews if r.timestamp >= cutoff_date]
        all_reviews.extend(app_reviews)
        print(f"Fetched {len(app_reviews)} reviews from App Store.")

    # 2. Fetch Play Store
    if config.play_store_id:
        print(f"Fetching Play Store reviews for {config.name}...")
        play_reviews = fetch_play_store_reviews(config.play_store_id, config.country)
        # Filter by date
        play_reviews = [r for r in play_reviews if r.timestamp >= cutoff_date]
        all_reviews.extend(play_reviews)
        print(f"Fetched {len(play_reviews)} reviews from Play Store.")

    # 3. Apply Filters
    from .filters import apply_filters
    print(f"Applying filters (No emojis, Strict English, min 4 words)...")
    before_count = len(all_reviews)
    all_reviews = apply_filters(all_reviews)
    after_count = len(all_reviews)
    print(f"Filters removed {before_count - after_count} reviews. {after_count} remain.")

    # 4. Save
    if all_reviews:
        return save_reviews(all_reviews, config.name)
    else:
        print("No reviews found for the specified period.")
        return None

if __name__ == "__main__":
    import sys
    product = sys.argv[1] if len(sys.argv) > 1 else "groww"
    run_ingestion(product)
