"""
API endpoint tests for the RAG chatbot FastAPI application.
Uses the test_client fixture from conftest.py (minimal inline app, no static files).
Covers: POST /api/query, GET /api/courses, POST /api/clear-session
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestQueryEndpoint:
    """Tests for POST /api/query"""

    def test_query_with_existing_session(self, test_client):
        response = test_client.post(
            "/api/query",
            json={"query": "What is MCP?", "session_id": "existing-session-456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing-session-456"
        assert "answer" in data
        assert isinstance(data["sources"], list)

    def test_query_without_session_creates_one(self, test_client):
        response = test_client.post("/api/query", json={"query": "What is MCP?"})
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"

    def test_query_response_shape(self, test_client):
        response = test_client.post(
            "/api/query",
            json={"query": "What is MCP?", "session_id": "s1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0
        for source in data["sources"]:
            assert "text" in source

    def test_query_sources_include_link(self, test_client):
        response = test_client.post(
            "/api/query",
            json={"query": "What is MCP?", "session_id": "s1"},
        )
        data = response.json()
        assert data["sources"][0]["link"] == "https://example.com/mcp-course/lesson-1"

    def test_query_missing_query_field_returns_422(self, test_client):
        response = test_client.post("/api/query", json={"session_id": "s1"})
        assert response.status_code == 422

    def test_query_empty_body_returns_422(self, test_client):
        response = test_client.post("/api/query", json={})
        assert response.status_code == 422

    def test_query_rag_error_returns_500(self, test_client, mock_rag_system):
        mock_rag_system.query.side_effect = Exception("RAG system failure")
        response = test_client.post(
            "/api/query",
            json={"query": "What is MCP?", "session_id": "s1"},
        )
        assert response.status_code == 500
        assert "RAG system failure" in response.json()["detail"]
        mock_rag_system.query.side_effect = None  # reset for subsequent tests


class TestCoursesEndpoint:
    """Tests for GET /api/courses"""

    def test_get_courses_returns_200(self, test_client):
        response = test_client.get("/api/courses")
        assert response.status_code == 200

    def test_get_courses_response_shape(self, test_client):
        data = test_client.get("/api/courses").json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["course_titles"], list)

    def test_get_courses_correct_values(self, test_client):
        data = test_client.get("/api/courses").json()
        assert data["total_courses"] == 2
        assert "MCP Introduction Course" in data["course_titles"]
        assert "FastAPI Basics" in data["course_titles"]

    def test_get_courses_empty_catalog(self, test_client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }
        data = test_client.get("/api/courses").json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_get_courses_analytics_error_returns_500(self, test_client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = Exception("DB error")
        response = test_client.get("/api/courses")
        assert response.status_code == 500
        mock_rag_system.get_course_analytics.side_effect = None


class TestClearSessionEndpoint:
    """Tests for POST /api/clear-session"""

    def test_clear_session_success(self, test_client):
        response = test_client.post(
            "/api/clear-session", json={"session_id": "session-123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session-123" in data["message"]

    def test_clear_session_calls_manager(self, test_client, mock_rag_system):
        test_client.post("/api/clear-session", json={"session_id": "session-abc"})
        mock_rag_system.session_manager.clear_session.assert_called_with("session-abc")

    def test_clear_session_missing_id_returns_422(self, test_client):
        response = test_client.post("/api/clear-session", json={})
        assert response.status_code == 422

    def test_clear_session_error_returns_500(self, test_client, mock_rag_system):
        mock_rag_system.session_manager.clear_session.side_effect = Exception(
            "Session not found"
        )
        response = test_client.post(
            "/api/clear-session", json={"session_id": "bad-session"}
        )
        assert response.status_code == 500
        assert "Session not found" in response.json()["detail"]
        mock_rag_system.session_manager.clear_session.side_effect = None
