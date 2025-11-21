import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Content, Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Men's Club Training Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or "Unknown"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Seed minimal curated content if empty (MVP)
SEED_CONTENT: List[Content] = [
    Content(
        title="Seneca on the Shortness of Life",
        section="ESSENTIAL FOUNDATIONS",
        sender="Seneca",
        topic_tag="Stoicism",
        difficulty="Medium",
        time_estimate="6 min",
        words=120,
        text=(
            "It is not that we have a short time to live, but that we waste a great deal of it. "
            "Life is long enough, and a sufficiently generous amount has been given to us for the highest achievements "
            "if it were all well invested."
        ),
        context="You feel rushed and scattered. This resets your frame to ownership of time."
    ),
    Content(
        title="Voss: Tactical Empathy",
        section="THE BOARDROOM",
        sender="Chris Voss",
        topic_tag="Negotiation",
        difficulty="Hard",
        time_estimate="8 min",
        words=140,
        text=(
            "Tactical empathy is understanding the feelings and mindset of another in the moment and also hearing "
            "what is behind those feelings so you increase your influence in all the moments that follow."
        ),
        context="You're entering a tough conversation. Prime to listen and label before asserting."
    ),
]

@app.post("/api/seed")
def seed_content():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["content"].count_documents({})
    if existing > 0:
        return {"seeded": False, "message": "Content already exists"}
    for item in SEED_CONTENT:
        create_document("content", item)
    return {"seeded": True, "count": len(SEED_CONTENT)}

# Public: list content items (basic feed)
@app.get("/api/content")
def list_content(limit: int = 50):
    docs = get_documents("content", {}, limit)
    def to_dict(d):
        d = {**d}
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        return d
    return [to_dict(d) for d in docs]

@app.get("/api/content/{content_id}")
def get_content(content_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["content"].find_one({"_id": ObjectId(content_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid content id")
    if not doc:
        raise HTTPException(status_code=404, detail="Content not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

class ReflectionIn(BaseModel):
    content_id: str
    words_typed: int
    duration_sec: int
    reflection: str

@app.post("/api/session")
def complete_session(payload: ReflectionIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        _ = db["content"].find_one({"_id": ObjectId(payload.content_id)})
        if not _:
            raise HTTPException(status_code=404, detail="Content not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid content id")

    session = Session(
        user_id=None,
        content_id=payload.content_id,
        words_typed=payload.words_typed,
        duration_sec=payload.duration_sec,
        reflection=payload.reflection,
    )
    sid = create_document("session", session)

    db["user"].update_one(
        {"handle": "anon"},
        {"$inc": {"xp": payload.words_typed}, "$setOnInsert": {"rank": "Initiate", "streak": 0}},
        upsert=True,
    )

    return {"session_id": sid, "ok": True}

@app.get("/api/profile")
def get_profile():
    prof = db["user"].find_one({"handle": "anon"}) or {"handle": "anon", "rank": "Initiate", "xp": 0, "streak": 0}
    if "_id" in prof:
        prof["id"] = str(prof.pop("_id"))
    xp = prof.get("xp", 0)
    rank = "Initiate" if xp < 5000 else ("Strategist" if xp < 20000 else "Commander")
    prof["rank"] = rank
    return prof

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
