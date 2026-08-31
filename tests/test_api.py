import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        from main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestMetricsEndpoint:
    def test_metrics_returns_dict(self):
        from main import app

        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "cache_hits" in data
        assert "llm_requests" in data
        assert "human_escalations" in data
        assert "estimated_cost_usd" in data


class TestChatEndpoint:
    def test_chat_empty_message_rejected(self):
        from main import app

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"user_id": "123", "message": ""},
        )
        assert response.status_code == 422

    def test_chat_missing_user_id(self):
        from main import app

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"message": "hello"},
        )
        assert response.status_code == 422

    def test_chat_missing_message(self):
        from main import app

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"user_id": "123"},
        )
        assert response.status_code == 422

    @patch("services.chat_service.chat_service.process_message", new_callable=AsyncMock)
    def test_chat_valid_request(self, mock_process):
        from main import app

        mock_process.return_value = {
            "response": "El curso de inglés B1 cuesta 450.000 COP.",
            "escalated": False,
            "cached": False,
            "relevance_score": 0.91,
            "request_id": "test123",
        }

        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"user_id": "12345", "message": "¿Cuánto cuesta el curso de inglés B1?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "escalated" in data
        assert "cached" in data
        assert "relevance_score" in data
        assert data["escalated"] is False
