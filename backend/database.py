"""
Truthify-AI Expanded Storage Architecture.

Provides database abstractions for:
1. analyses: full historical record of evaluated claims, media, and risk verdicts.
2. verified_facts: dynamic knowledge base of verified claims (auto-ingested from internet searches + user contributions).
3. trusted_sources: directory of trusted domains, fact checkers, health organizations, and news agencies.
4. media_records: uploaded images, videos, and PDFs with extracted OCR/transcripts and metadata.

Works seamlessly with MongoDB (motor) when running with Docker/Mongo,
and transparently persists to local JSON data store when running locally without MongoDB.
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "misinfo_system")

LOCAL_STORE_PATH = Path(__file__).resolve().parent / "data_store.json"

_storage = None

# Default trusted sources seed
DEFAULT_TRUSTED_SOURCES = [
    {"domain": "reuters.com", "name": "Reuters News & Fact Check", "category": "news_agency", "trust_score": 0.98, "is_active": True},
    {"domain": "apnews.com", "name": "Associated Press (AP) Fact Check", "category": "news_agency", "trust_score": 0.98, "is_active": True},
    {"domain": "factcheck.org", "name": "FactCheck.org (Annenberg Public Policy)", "category": "fact_checker", "trust_score": 0.96, "is_active": True},
    {"domain": "snopes.com", "name": "Snopes Fact Check", "category": "fact_checker", "trust_score": 0.95, "is_active": True},
    {"domain": "politifact.com", "name": "PolitiFact (Poynter Institute)", "category": "fact_checker", "trust_score": 0.95, "is_active": True},
    {"domain": "who.int", "name": "World Health Organization (WHO)", "category": "health_authority", "trust_score": 0.99, "is_active": True},
    {"domain": "cdc.gov", "name": "Centers for Disease Control and Prevention (CDC)", "category": "health_authority", "trust_score": 0.99, "is_active": True},
    {"domain": "afp.com", "name": "Agence France-Presse (AFP Fact Check)", "category": "news_agency", "trust_score": 0.96, "is_active": True},
    {"domain": "nature.com", "name": "Nature Scientific Journal", "category": "scientific_authority", "trust_score": 0.99, "is_active": True},
    {"domain": "en.wikipedia.org", "name": "Wikipedia Neutral Encyclopedia", "category": "encyclopedia", "trust_score": 0.88, "is_active": True},
    {"domain": "nasa.gov", "name": "NASA Earth Science & Climate", "category": "scientific_authority", "trust_score": 0.99, "is_active": True},
]

# Initial verified facts seed
DEFAULT_VERIFIED_FACTS = [
    {
        "fact_id": "fact-seed-001",
        "claim": "MMR vaccine causes autism in children",
        "verdict": "debunked_as_false",
        "explanation": "Extensive international clinical studies involving millions of children over 25+ years have proven no causal link between the MMR vaccine and autism. The 1998 Wakefield paper was formally retracted for fraud.",
        "source_name": "World Health Organization (WHO)",
        "source_url": "https://www.who.int/groups/global-advisory-committee-on-vaccine-safety/topics/mmr-vaccines-and-autism",
        "domain": "who.int",
        "topic": "health",
        "trust_score": 0.99,
        "auto_ingested": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    },
    {
        "fact_id": "fact-seed-002",
        "claim": "5G mobile network radiation damages human DNA or causes COVID-19",
        "verdict": "debunked_as_false",
        "explanation": "5G operates using non-ionizing radio frequencies with insufficient energy to damage DNA or biological cells, and viruses cannot travel on radio waves.",
        "source_name": "Reuters Fact Check",
        "source_url": "https://www.reuters.com/fact-check",
        "domain": "reuters.com",
        "topic": "technology",
        "trust_score": 0.98,
        "auto_ingested": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    },
    {
        "fact_id": "fact-seed-003",
        "claim": "Global average surface temperature has increased by approximately 1.1 degrees Celsius since the pre-industrial baseline",
        "verdict": "confirmed_true",
        "explanation": "Global ground station and satellite measurements confirmed by NASA, NOAA, and the IPCC document an approximately 1.1C warming trend driven by greenhouse gas emissions.",
        "source_name": "NASA Global Climate Change",
        "source_url": "https://climate.nasa.gov",
        "domain": "nasa.gov",
        "topic": "environment",
        "trust_score": 0.99,
        "auto_ingested": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    },
    {
        "fact_id": "fact-seed-004",
        "claim": "Electronic voting machines in federal elections undergo physical audits, logic tests, and paper trail verification",
        "verdict": "confirmed_true",
        "explanation": "Certified voting systems utilize pre-election logic and accuracy testing, bipartisan chain of custody, and post-election hand-count audits of voter-verified paper audit trails.",
        "source_name": "FactCheck.org",
        "source_url": "https://www.factcheck.org",
        "domain": "factcheck.org",
        "topic": "elections",
        "trust_score": 0.96,
        "auto_ingested": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
]


class PersistentStorage:
    """
    Robust disk-persisted database storage supporting analyses,
    verified_facts, trusted_sources, and media_records.
    """

    def __init__(self, file_path: Path = LOCAL_STORE_PATH):
        self.file_path = file_path
        self._analyses: list[dict] = []
        self._verified_facts: list[dict] = []
        self._trusted_sources: list[dict] = []
        self._media_records: list[dict] = []
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._analyses = data.get("analyses", [])
                    self._verified_facts = data.get("verified_facts", [])
                    self._trusted_sources = data.get("trusted_sources", [])
                    self._media_records = data.get("media_records", [])
                    logger.info(f"Loaded persistent storage: {len(self._analyses)} analyses, {len(self._verified_facts)} facts, {len(self._trusted_sources)} sources.")
                    return
            except Exception as e:
                logger.warning(f"Error reading persistent storage: {e}. Reinitializing defaults.")

        # Initialize with defaults
        self._analyses = []
        self._verified_facts = list(DEFAULT_VERIFIED_FACTS)
        self._trusted_sources = list(DEFAULT_TRUSTED_SOURCES)
        self._media_records = []
        self._save()

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "analyses": self._analyses,
                    "verified_facts": self._verified_facts,
                    "trusted_sources": self._trusted_sources,
                    "media_records": self._media_records,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist storage to disk: {e}")

    # --- Analyses ---
    async def insert_analysis(self, doc: dict):
        doc = dict(doc)
        if "created_at" not in doc:
            doc["created_at"] = datetime.utcnow().isoformat()
        self._analyses.insert(0, doc)
        self._save()

    async def find_analyses(self, query: dict = None, sort_field: str = "created_at",
                            sort_dir: int = -1, limit: int = 50) -> list[dict]:
        results = self._analyses
        if query:
            results = [
                doc for doc in results
                if all(doc.get(k) == v for k, v in query.items())
            ]
        try:
            results = sorted(results, key=lambda x: x.get(sort_field, ""), reverse=(sort_dir == -1))
        except (TypeError, KeyError):
            pass
        return results[:limit]

    async def find_one(self, query: dict) -> dict | None:
        for doc in self._analyses:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    async def update_one(self, query: dict, update: dict):
        for doc in self._analyses:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                self._save()
                return True
        return False

    async def count(self, query: dict = None) -> int:
        if not query:
            return len(self._analyses)
        return len([d for d in self._analyses if all(d.get(k) == v for k, v in query.items())])

    # --- Verified Facts (Database Expansion) ---
    async def insert_fact(self, fact_doc: dict):
        doc = dict(fact_doc)
        if "fact_id" not in doc:
            doc["fact_id"] = f"fact-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        if "created_at" not in doc:
            doc["created_at"] = now
        doc["updated_at"] = now

        # Deduplicate by claim text
        for idx, existing in enumerate(self._verified_facts):
            if existing.get("claim", "").lower().strip() == doc.get("claim", "").lower().strip():
                self._verified_facts[idx].update(doc)
                self._save()
                return self._verified_facts[idx]

        self._verified_facts.insert(0, doc)
        self._save()
        return doc

    async def find_facts(self, topic: Optional[str] = None, verdict: Optional[str] = None,
                         search: Optional[str] = None, limit: int = 50) -> list[dict]:
        results = self._verified_facts
        if topic:
            results = [f for f in results if f.get("topic", "").lower() == topic.lower()]
        if verdict:
            results = [f for f in results if f.get("verdict", "").lower() == verdict.lower()]
        if search:
            q = search.lower()
            results = [
                f for f in results
                if q in f.get("claim", "").lower() or q in f.get("explanation", "").lower() or q in f.get("source_name", "").lower()
            ]
        return results[:limit]

    async def find_fact_by_id(self, fact_id: str) -> dict | None:
        for f in self._verified_facts:
            if f.get("fact_id") == fact_id:
                return dict(f)
        return None

    async def delete_fact(self, fact_id: str) -> bool:
        initial = len(self._verified_facts)
        self._verified_facts = [f for f in self._verified_facts if f.get("fact_id") != fact_id]
        if len(self._verified_facts) < initial:
            self._save()
            return True
        return False

    async def count_facts(self, query: dict = None) -> int:
        if not query:
            return len(self._verified_facts)
        return len([f for f in self._verified_facts if all(f.get(k) == v for k, v in query.items())])

    # --- Trusted Sources ---
    async def find_trusted_sources(self) -> list[dict]:
        return self._trusted_sources

    async def insert_trusted_source(self, source_doc: dict):
        doc = dict(source_doc)
        domain = doc.get("domain", "").lower()
        for idx, s in enumerate(self._trusted_sources):
            if s.get("domain", "").lower() == domain:
                self._trusted_sources[idx].update(doc)
                self._save()
                return self._trusted_sources[idx]

        doc["created_at"] = datetime.utcnow().isoformat()
        self._trusted_sources.append(doc)
        self._save()
        return doc

    async def delete_trusted_source(self, domain: str) -> bool:
        domain = domain.lower()
        initial = len(self._trusted_sources)
        self._trusted_sources = [s for s in self._trusted_sources if s.get("domain", "").lower() != domain]
        if len(self._trusted_sources) < initial:
            self._save()
            return True
        return False

    # --- Media Records ---
    async def insert_media(self, media_doc: dict):
        doc = dict(media_doc)
        if "media_id" not in doc:
            doc["media_id"] = f"media-{uuid.uuid4().hex[:8]}"
        doc["created_at"] = datetime.utcnow().isoformat()
        self._media_records.insert(0, doc)
        self._save()
        return doc

    async def list_media(self, limit: int = 50) -> list[dict]:
        return self._media_records[:limit]

    # --- Database Overview Stats ---
    async def get_overview(self) -> dict:
        topic_counts = {}
        for f in self._verified_facts:
            top = f.get("topic", "general").lower()
            topic_counts[top] = topic_counts.get(top, 0) + 1

        source_counts = {}
        for f in self._verified_facts:
            src = f.get("source_name", "Unknown")
            source_counts[src] = source_counts.get(src, 0) + 1

        return {
            "storage_mode": "persistent_json_store",
            "total_analyses": len(self._analyses),
            "total_verified_facts": len(self._verified_facts),
            "total_trusted_sources": len(self._trusted_sources),
            "total_media_records": len(self._media_records),
            "topics_breakdown": topic_counts,
            "sources_breakdown": source_counts,
        }


class MongoStorage:
    """MongoDB-backed storage using motor async driver with automatic fallback to PersistentStorage."""

    def __init__(self, db, client):
        self._db = db
        self._client = client
        self._fallback = PersistentStorage()
        self._use_fallback = False

    async def insert_analysis(self, doc: dict):
        if self._use_fallback:
            return await self._fallback.insert_analysis(doc)
        try:
            await self._db.analyses.insert_one(doc)
        except Exception as e:
            logger.warning(f"MongoDB write failed ({e}), switching to fallback.")
            self._use_fallback = True
            await self._fallback.insert_analysis(doc)

    async def find_analyses(self, query: dict = None, sort_field: str = "created_at",
                            sort_dir: int = -1, limit: int = 50) -> list[dict]:
        if self._use_fallback:
            return await self._fallback.find_analyses(query, sort_field, sort_dir, limit)
        try:
            cursor = self._db.analyses.find(query or {}).sort(sort_field, sort_dir).limit(limit)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.warning(f"MongoDB query failed ({e}), switching to fallback.")
            self._use_fallback = True
            return await self._fallback.find_analyses(query, sort_field, sort_dir, limit)

    async def find_one(self, query: dict) -> dict | None:
        if self._use_fallback:
            return await self._fallback.find_one(query)
        try:
            return await self._db.analyses.find_one(query)
        except Exception as e:
            logger.warning(f"MongoDB find_one failed ({e}), switching to fallback.")
            self._use_fallback = True
            return await self._fallback.find_one(query)

    async def update_one(self, query: dict, update: dict):
        if self._use_fallback:
            return await self._fallback.update_one(query, update)
        try:
            await self._db.analyses.update_one(query, update)
            return True
        except Exception as e:
            logger.warning(f"MongoDB update failed ({e}), switching to fallback.")
            self._use_fallback = True
            return await self._fallback.update_one(query, update)

    async def count(self, query: dict = None) -> int:
        if self._use_fallback:
            return await self._fallback.count(query)
        try:
            return await self._db.analyses.count_documents(query or {})
        except Exception as e:
            logger.warning(f"MongoDB count failed ({e}), switching to fallback.")
            self._use_fallback = True
            return await self._fallback.count(query)

    # --- Delegated / Fallback expanded methods ---
    async def insert_fact(self, fact_doc: dict):
        if self._use_fallback:
            return await self._fallback.insert_fact(fact_doc)
        try:
            doc = dict(fact_doc)
            if "fact_id" not in doc:
                doc["fact_id"] = f"fact-{uuid.uuid4().hex[:8]}"
            await self._db.verified_facts.replace_one({"claim": doc["claim"]}, doc, upsert=True)
            return doc
        except Exception as e:
            self._use_fallback = True
            return await self._fallback.insert_fact(fact_doc)

    async def find_facts(self, topic: Optional[str] = None, verdict: Optional[str] = None,
                         search: Optional[str] = None, limit: int = 50) -> list[dict]:
        if self._use_fallback:
            return await self._fallback.find_facts(topic, verdict, search, limit)
        try:
            q = {}
            if topic:
                q["topic"] = topic
            if verdict:
                q["verdict"] = verdict
            if search:
                q["$or"] = [
                    {"claim": {"$regex": search, "$options": "i"}},
                    {"explanation": {"$regex": search, "$options": "i"}}
                ]
            cursor = self._db.verified_facts.find(q).limit(limit)
            return [d async for d in cursor]
        except Exception:
            self._use_fallback = True
            return await self._fallback.find_facts(topic, verdict, search, limit)

    async def find_fact_by_id(self, fact_id: str) -> dict | None:
        if self._use_fallback:
            return await self._fallback.find_fact_by_id(fact_id)
        try:
            return await self._db.verified_facts.find_one({"fact_id": fact_id})
        except Exception:
            self._use_fallback = True
            return await self._fallback.find_fact_by_id(fact_id)

    async def delete_fact(self, fact_id: str) -> bool:
        if self._use_fallback:
            return await self._fallback.delete_fact(fact_id)
        try:
            res = await self._db.verified_facts.delete_one({"fact_id": fact_id})
            return res.deleted_count > 0
        except Exception:
            self._use_fallback = True
            return await self._fallback.delete_fact(fact_id)

    async def find_trusted_sources(self) -> list[dict]:
        if self._use_fallback:
            return await self._fallback.find_trusted_sources()
        try:
            cursor = self._db.trusted_sources.find({})
            sources = [d async for d in cursor]
            return sources or await self._fallback.find_trusted_sources()
        except Exception:
            self._use_fallback = True
            return await self._fallback.find_trusted_sources()

    async def insert_trusted_source(self, source_doc: dict):
        if self._use_fallback:
            return await self._fallback.insert_trusted_source(source_doc)
        try:
            doc = dict(source_doc)
            await self._db.trusted_sources.replace_one({"domain": doc["domain"]}, doc, upsert=True)
            return doc
        except Exception:
            self._use_fallback = True
            return await self._fallback.insert_trusted_source(source_doc)

    async def delete_trusted_source(self, domain: str) -> bool:
        if self._use_fallback:
            return await self._fallback.delete_trusted_source(domain)
        try:
            res = await self._db.trusted_sources.delete_one({"domain": domain})
            return res.deleted_count > 0
        except Exception:
            self._use_fallback = True
            return await self._fallback.delete_trusted_source(domain)

    async def insert_media(self, media_doc: dict):
        return await self._fallback.insert_media(media_doc)

    async def list_media(self, limit: int = 50) -> list[dict]:
        return await self._fallback.list_media(limit)

    async def get_overview(self) -> dict:
        return await self._fallback.get_overview()


def get_storage():
    """Get the active storage backend."""
    global _storage
    if _storage is not None:
        return _storage

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=1200)
        db = client[DB_NAME]
        _storage = MongoStorage(db, client)
    except Exception as e:
        logger.warning(f"MongoDB driver initialization failed ({e}). Using persistent storage.")
        _storage = PersistentStorage()

    return _storage


def get_db():
    return get_storage()
