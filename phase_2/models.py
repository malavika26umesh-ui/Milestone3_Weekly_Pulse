from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class Source(str, Enum):
    APP_STORE = "app_store"
    PLAY_STORE = "play_store"

class Review(BaseModel):
    review_id: str
    source: Source
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    content: str
    author: str
    timestamp: datetime

class ProductConfig(BaseModel):
    name: str
    app_store_id: Optional[str] = None
    play_store_id: Optional[str] = None
    country: str = "in"
