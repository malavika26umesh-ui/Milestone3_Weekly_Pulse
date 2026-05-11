import emoji
import re
from langdetect import detect, DetectorFactory
from typing import List
from .models import Review
import nltk
from nltk.corpus import words

# Ensure consistent results from langdetect
DetectorFactory.seed = 0

# Download words corpus if not already present
try:
    ENGLISH_WORDS = set(w.lower() for w in words.words())
except:
    nltk.download('words')
    ENGLISH_WORDS = set(w.lower() for w in words.words())

# Add domain-specific and brand words that are allowed
ALLOWED_WORDS = {
    "groww", "grow", "zerodha", "zeroda", "kite", "sip", "kyc", "mcx", 
    "nifty", "sensex", "sebi", "demat", "bse", "nse", "upstox", "angelone",
    "paytm", "indmoney", "kuvera", "groww's", "ios", "ipad", "android", "app"
}
ENGLISH_WORDS.update(ALLOWED_WORDS)

def has_emoji(text: str) -> bool:
    """Returns True if the text contains any emojis."""
    return emoji.emoji_count(text) > 0

def is_strictly_english(text: str, threshold: float = 0.9) -> bool:
    """
    Returns True if the text is almost entirely English/Allowed words.
    """
    if not text.strip():
        return False
        
    # 1. Basic language detection (as a first pass)
    try:
        if detect(text) != 'en':
            return False
    except:
        return False
        
    # 2. Word-level check (filtering out Hinglish/other languages)
    # Remove punctuation and split into words
    text_words = re.findall(r'\b[a-z]+\b', text.lower())
    if not text_words:
        return False
        
    english_count = sum(1 for w in text_words if w in ENGLISH_WORDS)
    ratio = english_count / len(text_words)
    
    return ratio >= threshold

def has_minimum_words(text: str, min_words: int = 4) -> bool:
    """Returns True if the text has at least 4 words."""
    # Using re.findall to count actual words (ignoring punctuation)
    return len(re.findall(r'\b\w+\b', text)) >= min_words

def apply_filters(reviews: List[Review]) -> List[Review]:
    """
    Applies the requested filters:
    1. Remove reviews with emojis.
    2. Remove reviews with non-English words (very strict check).
    3. Remove reviews with less than 4 words.
    """
    filtered_reviews = []
    
    for r in reviews:
        content = r.content
        
        # Filter 1: No emojis
        if has_emoji(content):
            continue
            
        # Filter 2: Strict English check
        if not is_strictly_english(content):
            continue
            
        # Filter 3: Min 4 words
        if not has_minimum_words(content, 4):
            continue
            
        filtered_reviews.append(r)
        
    return filtered_reviews
