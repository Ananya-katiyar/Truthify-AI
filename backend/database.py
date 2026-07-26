"""
Member 4 (Backend Engineer) owns this file.

Uses MongoDB (via motor, async driver). If your team prefers PostgreSQL
instead, swap this for SQLAlchemy + asyncpg -- the route files only call
`get_db()` and use collection-style methods, so keep that interface if you
change the underlying DB.

TODO for Member 4:
- Move MONGO_URI into a real .env file (see .env.example at project root)
- Add indexes on `created_at` and `risk_level` for the dashboard queries
"""

import os

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "misinfo_system")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


def get_db():
    return db
