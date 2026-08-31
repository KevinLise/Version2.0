import pytest
import asyncio
from services.cache_service import CacheService


class TestCacheService:
    def setup_method(self):
        self.cache = CacheService()
        self.cache.enabled = True
        self.cache._memory_cache = {}

    def test_normalize_query(self):
        n1 = self.cache._normalize_query("¿Cuánto cuesta el B1?")
        n2 = self.cache._normalize_query("cuanto cuesta el b1")
        assert n1 == n2

    def test_normalize_removes_punctuation(self):
        result = self.cache._normalize_query("Hello! How are you?")
        assert "!" not in result
        assert "?" not in result

    def test_normalize_lowercases(self):
        result = self.cache._normalize_query("HELLO World")
        assert result == "hello world"

    def test_generate_key_deterministic(self):
        key1 = self.cache._generate_key("test query")
        key2 = self.cache._generate_key("test query")
        assert key1 == key2

    def test_generate_key_different_for_different_queries(self):
        key1 = self.cache._generate_key("query one")
        key2 = self.cache._generate_key("query two")
        assert key1 != key2

    def test_generate_key_same_for_normalized(self):
        key1 = self.cache._generate_key("¿Cuánto cuesta?")
        key2 = self.cache._generate_key("cuanto cuesta")
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        await self.cache.set("test query", "test response", 0.85)
        result = await self.cache.get("test query")
        assert result is not None
        assert result["response"] == "test response"
        assert result["relevance_score"] == 0.85

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        result = await self.cache.get("nonexistent query")
        assert result is None

    @pytest.mark.asyncio
    async def test_disabled_cache(self):
        self.cache.enabled = False
        await self.cache.set("test", "response")
        result = await self.cache.get("test")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_hit(self):
        from datetime import datetime, timezone
        self.cache._memory_cache["testkey"] = {
            "data": {"response": "cached", "relevance_score": 0.9},
            "expires_at": datetime(2099, 1, 1, tzinfo=timezone.utc),
        }
        key = self.cache._generate_key("testkey")
        self.cache._memory_cache[key] = self.cache._memory_cache.pop("testkey")
        result = await self.cache.get("testkey")
        assert result is not None
