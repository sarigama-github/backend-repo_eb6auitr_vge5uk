"""
Database Schemas for the Men's Club Training App

Each Pydantic model name maps to a MongoDB collection using the lowercase class name.
- User -> "user"
- Content -> "content"
- Session -> "session"

"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    handle: str = Field(..., description="Public handle")
    rank: str = Field("Initiate", description="Current rank title")
    xp: int = Field(0, ge=0, description="Total XP (words typed)")
    streak: int = Field(0, ge=0, description="Current daily streak in days")

class Content(BaseModel):
    title: str = Field(..., description="Display title e.g., 'Seneca on Shortness of Life'")
    section: str = Field(..., description="Track name e.g., 'ESSENTIAL FOUNDATIONS'")
    sender: str = Field(..., description="Source/Author e.g., 'Seneca'")
    topic_tag: str = Field(..., description="Topic tag e.g., 'Stoicism'")
    difficulty: str = Field(..., description="Difficulty e.g., 'Medium' | 'Hard'")
    time_estimate: str = Field(..., description="Quick estimate like '6 min'")
    words: int = Field(..., ge=1, description="Word count of the passage")
    text: str = Field(..., description="The passage to retype")
    context: str = Field(..., description="Short priming context shown before typing")

class Session(BaseModel):
    user_id: Optional[str] = Field(None, description="User id as string; optional for anon MVP")
    content_id: str = Field(..., description="ID of content that was typed")
    words_typed: int = Field(..., ge=0)
    duration_sec: int = Field(..., ge=0)
    reflection: str = Field(..., description="User's applied reflection")
    created_at: Optional[datetime] = None
