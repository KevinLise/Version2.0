import re
import time
import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
import aiosqlite
from config.settings import settings
from database.sqlite import db


class CacheService:
    def __init__(self):
        self.enabled = settings.cache_enabled
        self.ttl_seconds = settings.cache_ttl_seconds
        self._memory_cache: dict[str, dict] = {}

    def _normalize_query(self, query: str) -> str:
        normalized = query.lower().strip()
        normalized = unicodedata.normalize("NFD", normalized)
        normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        normalized = re.sub(r"[^\w\s]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _generate_key(self, query: str) -> str:
        normalized = self._normalize_query(query)
        return hashlib.sha256(normalized.encode()).hexdigest()

    async def get(self, query: str) -> dict | None:
        if not self.enabled:
            return None

        key = self._generate_key(query)

        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if datetime.now(timezone.utc) < entry["expires_at"]:
                return entry["data"]
            else:
                del self._memory_cache[key]

        try:
            conn = await db.connect()
            try:
                cursor = await conn.execute(
                    "SELECT response, relevance_score, expires_at FROM cache WHERE cache_key = ?",
                    (key,),
                )
                row = await cursor.fetchone()
                if row:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                    if datetime.now(timezone.utc) < expires_at:
                        return {
                            "response": row["response"],
                            "relevance_score": row["relevance_score"],
                        }
                    else:
                        await conn.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
                        await conn.commit()
            finally:
                await conn.close()
        except Exception:
            pass

        return None

    async def set(
        self,
        query: str,
        response: str,
        relevance_score: float | None = None,
    ) -> None:
        if not self.enabled:
            return

        key = self._generate_key(query)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds)

        self._memory_cache[key] = {
            "data": {
                "response": response,
                "relevance_score": relevance_score,
            },
            "expires_at": expires_at,
        }

        try:
            conn = await db.connect()
            try:
                await conn.execute(
                    """INSERT OR REPLACE INTO cache (cache_key, response, relevance_score, expires_at)
                       VALUES (?, ?, ?, ?)""",
                    (key, response, relevance_score, expires_at.isoformat()),
                )
                await conn.commit()
            finally:
                await conn.close()
        except Exception:
            pass

    async def clear_expired(self) -> int:
        count = 0
        now = datetime.now(timezone.utc)

        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v["expires_at"] <= now
        ]
        for k in expired_keys:
            del self._memory_cache[k]
            count += 1

        try:
            conn = await db.connect()
            try:
                cursor = await conn.execute(
                    "DELETE FROM cache WHERE expires_at <= ?",
                    (now.isoformat(),),
                )
                count += cursor.rowcount
                await conn.commit()
            finally:
                await conn.close()
        except Exception:
            pass

        return count


cache_service = CacheService()
