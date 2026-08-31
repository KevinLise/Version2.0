import logging
from datetime import datetime
from database.sqlite import db

logger = logging.getLogger(__name__)

ESTIMATED_COST_PER_1K_INPUT = 0.00015
ESTIMATED_COST_PER_1K_OUTPUT = 0.0006


class MetricsService:
    def __init__(self):
        self._counters = {
            "total_queries": 0,
            "successful_queries": 0,
            "human_escalations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "llm_requests": 0,
            "embedding_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_response_time_ms": 0.0,
        }

    async def record_query(
        self,
        user_id: str | None = None,
        request_id: str | None = None,
        relevance_score: float | None = None,
        cache_hit: bool = False,
        llm_called: bool = False,
        escalated: bool = False,
        response_time_ms: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        self._counters["total_queries"] += 1
        self._counters["total_response_time_ms"] += response_time_ms
        self._counters["total_input_tokens"] += input_tokens
        self._counters["total_output_tokens"] += output_tokens

        if cache_hit:
            self._counters["cache_hits"] += 1
        else:
            self._counters["cache_misses"] += 1

        if llm_called:
            self._counters["llm_requests"] += 1

        if escalated:
            self._counters["human_escalations"] += 1

        if not escalated:
            self._counters["successful_queries"] += 1

        estimated_cost = (
            (input_tokens / 1000) * ESTIMATED_COST_PER_1K_INPUT +
            (output_tokens / 1000) * ESTIMATED_COST_PER_1K_OUTPUT
        )

        try:
            conn = await db.connect()
            try:
                await conn.execute(
                    """INSERT INTO metrics
                       (event_type, user_id, request_id, relevance_score, cache_hit,
                        llm_called, escalated, response_time_ms, input_tokens,
                        output_tokens, estimated_cost_usd)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "query",
                        user_id,
                        request_id,
                        relevance_score,
                        1 if cache_hit else 0,
                        1 if llm_called else 0,
                        1 if escalated else 0,
                        response_time_ms,
                        input_tokens,
                        output_tokens,
                        estimated_cost,
                    ),
                )
                await conn.commit()
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Failed to record metrics to DB: {e}")

    async def get_metrics(self) -> dict:
        total = self._counters["total_queries"]
        avg_response_time = (
            self._counters["total_response_time_ms"] / total
            if total > 0
            else 0.0
        )

        estimated_cost = (
            (self._counters["total_input_tokens"] / 1000) * ESTIMATED_COST_PER_1K_INPUT +
            (self._counters["total_output_tokens"] / 1000) * ESTIMATED_COST_PER_1K_OUTPUT
        )

        return {
            "total_queries": total,
            "successful_queries": self._counters["successful_queries"],
            "human_escalations": self._counters["human_escalations"],
            "cache_hits": self._counters["cache_hits"],
            "cache_misses": self._counters["cache_misses"],
            "llm_requests": self._counters["llm_requests"],
            "embedding_requests": self._counters["embedding_requests"],
            "average_response_time_ms": round(avg_response_time, 2),
            "estimated_input_tokens": self._counters["total_input_tokens"],
            "estimated_output_tokens": self._counters["total_output_tokens"],
            "estimated_cost_usd": round(estimated_cost, 6),
        }


metrics_service = MetricsService()
