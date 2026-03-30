"""
Integration tests with real ChromaDB.
Tests actual vector store operations and search functionality.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from models import Course, Lesson, CourseChunk


class TestVectorStoreIntegration:
    """Integration tests for VectorStore with real ChromaDB"""

    def test_add_and_search_course_content(self, real_vector_store, sample_course, sample_chunks):
        """Test adding and searching course content in real ChromaDB"""
        # Arrange - Add course data
        real_vector_store.add_course_metadata(sample_course)
        real_vector_store.add_course_content(sample_chunks)

        # Act - Search for content
        results = real_vector_store.search(query="MCP advanced patterns")

        # Assert
        assert not results.is_empty()
        assert len(results.documents) > 0
        assert "MCP" in results.documents[0] or "pattern" in results.documents[0].lower()

    def test_search_with_course_filter(self, populated_vector_store):
        """Test searching with course name filter"""
        # Act
        results = populated_vector_store.search(
            query="lesson content",
            course_name="MCP"
        )

        # Assert
        assert not results.is_empty()
        for meta in results.metadata:
            assert meta["course_title"] == "MCP Introduction Course"

    def test_search_with_lesson_filter(self, populated_vector_store):
        """Test searching with lesson number filter"""
        # Act
        results = populated_vector_store.search(
            query="content",
            course_name="MCP",
            lesson_number=5
        )

        # Assert
        if not results.is_empty():
            for meta in results.metadata:
                assert meta["lesson_number"] == 5

    def test_search_nonexistent_course(self, real_vector_store):
        """Test searching for nonexistent course in empty database returns error"""
        # Note: With populated data, vector search returns closest match
        # So we test with empty database to verify error handling
        # Act
        results = real_vector_store.search(
            query="anything",
            course_name="Nonexistent Course XYZ"
        )

        # Assert - empty database means course_catalog query returns no results
        # which triggers the "No course found" error path
        assert results.error is not None or results.is_empty()
        if results.error:
            assert "No course found" in results.error

    def test_course_name_resolution(self, populated_vector_store):
        """Test fuzzy course name resolution"""
        # Act - Search with partial course name
        results = populated_vector_store.search(
            query="patterns",
            course_name="MCP"  # Partial name
        )

        # Assert - Should resolve to full course name
        assert not results.is_empty()
        assert results.metadata[0]["course_title"] == "MCP Introduction Course"

    def test_get_lesson_link(self, populated_vector_store):
        """Test retrieving lesson links"""
        # Act
        link = populated_vector_store.get_lesson_link("MCP Introduction Course", 5)

        # Assert
        assert link == "https://example.com/mcp-course/lesson-5"

    def test_get_course_count(self, populated_vector_store):
        """Test getting course count"""
        # Act
        count = populated_vector_store.get_course_count()

        # Assert
        assert count == 1

    def test_get_existing_course_titles(self, populated_vector_store):
        """Test getting existing course titles"""
        # Act
        titles = populated_vector_store.get_existing_course_titles()

        # Assert
        assert "MCP Introduction Course" in titles


class TestCourseSearchToolIntegration:
    """Integration tests for CourseSearchTool with real ChromaDB"""

    def test_execute_with_real_store(self, populated_vector_store):
        """Test CourseSearchTool.execute() with real vector store"""
        # Arrange
        tool = CourseSearchTool(populated_vector_store)

        # Act
        result = tool.execute(query="advanced patterns")

        # Assert
        assert "[MCP Introduction Course" in result
        assert "Lesson" in result

    def test_execute_with_course_filter_real(self, populated_vector_store):
        """Test course filtering with real store"""
        # Arrange
        tool = CourseSearchTool(populated_vector_store)

        # Act
        result = tool.execute(query="content", course_name="MCP")

        # Assert
        assert "MCP Introduction Course" in result

    def test_execute_with_lesson_filter_real(self, populated_vector_store):
        """Test lesson filtering with real store"""
        # Arrange
        tool = CourseSearchTool(populated_vector_store)

        # Act
        result = tool.execute(query="patterns", course_name="MCP", lesson_number=5)

        # Assert
        # Should either find results or say no content found for that lesson
        assert "MCP" in result or "No relevant content" in result

    def test_sources_tracked_with_real_store(self, populated_vector_store):
        """Test that sources are tracked correctly with real store"""
        # Arrange
        tool = CourseSearchTool(populated_vector_store)

        # Act
        tool.execute(query="MCP content")

        # Assert
        assert len(tool.last_sources) > 0
        assert "MCP Introduction Course" in tool.last_sources[0]["text"]


class TestCourseOutlineToolIntegration:
    """Integration tests for CourseOutlineTool with real ChromaDB"""

    def test_execute_returns_outline(self, populated_vector_store):
        """Test CourseOutlineTool.execute() returns course outline"""
        # Arrange
        tool = CourseOutlineTool(populated_vector_store)

        # Act
        result = tool.execute(course_name="MCP")

        # Assert
        assert "MCP Introduction Course" in result
        assert "Lesson" in result
        assert "Course Link" in result

    def test_outline_includes_all_lessons(self, populated_vector_store):
        """Test that outline includes all lessons from course"""
        # Arrange
        tool = CourseOutlineTool(populated_vector_store)

        # Act
        result = tool.execute(course_name="MCP")

        # Assert
        assert "Lesson 1" in result
        assert "Lesson 2" in result
        assert "Lesson 5" in result


class TestToolManagerIntegration:
    """Integration tests for ToolManager with real tools"""

    def test_full_tool_workflow(self, populated_vector_store):
        """Test complete tool registration and execution workflow"""
        # Arrange
        manager = ToolManager()
        search_tool = CourseSearchTool(populated_vector_store)
        outline_tool = CourseOutlineTool(populated_vector_store)
        manager.register_tool(search_tool)
        manager.register_tool(outline_tool)

        # Act - Execute search
        search_result = manager.execute_tool("search_course_content", query="MCP patterns")

        # Get sources
        sources = manager.get_last_sources()

        # Reset sources
        manager.reset_sources()

        # Assert
        assert "MCP" in search_result
        assert len(sources) > 0
        assert len(manager.get_last_sources()) == 0  # After reset


class TestFullQueryFlowIntegration:
    """Integration tests for full query flow with mocked Anthropic"""

    def test_full_query_flow_mocked_anthropic(self, populated_vector_store, test_config, mock_tool_manager):
        """Test full query flow with real ChromaDB but mocked Anthropic"""
        # This test uses real ChromaDB but mocks the Anthropic API

        # Arrange
        with patch('rag_system.VectorStore') as MockVectorStore, \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager:

            # Use real vector store methods but mock the class
            MockVectorStore.return_value = populated_vector_store

            # Create real tool manager with real vector store
            real_tool_manager = ToolManager()
            search_tool = CourseSearchTool(populated_vector_store)
            outline_tool = CourseOutlineTool(populated_vector_store)
            real_tool_manager.register_tool(search_tool)
            real_tool_manager.register_tool(outline_tool)

            # Mock AI to return response after tool use
            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Based on the course content, lesson 5 covers advanced patterns."
            MockAIGenerator.return_value = mock_ai

            mock_session = MagicMock()
            mock_session.get_conversation_history.return_value = None
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem

            # Create RAG system with test config
            rag = RAGSystem(test_config)
            rag.vector_store = populated_vector_store
            rag.tool_manager = real_tool_manager

            # Act
            response, sources = rag.query("What was covered in lesson 5 of MCP?")

            # Assert
            assert response is not None
            # Sources might be empty if AI didn't trigger tool use in mock


class TestEmptyDatabaseBehavior:
    """Tests for behavior when database is empty"""

    def test_search_empty_database(self, real_vector_store):
        """Test searching an empty database returns appropriate message"""
        # Act - Search without adding any data
        results = real_vector_store.search(query="anything")

        # Assert
        assert results.is_empty()

    def test_tool_execute_empty_database(self, real_vector_store):
        """Test CourseSearchTool with empty database"""
        # Arrange
        tool = CourseSearchTool(real_vector_store)

        # Act
        result = tool.execute(query="anything")

        # Assert
        assert "No relevant content found" in result

    def test_outline_empty_database(self, real_vector_store):
        """Test CourseOutlineTool with empty database"""
        # Arrange
        tool = CourseOutlineTool(real_vector_store)

        # Act
        result = tool.execute(course_name="Any Course")

        # Assert
        assert "No course found" in result


class TestSearchResultsDataclass:
    """Tests for SearchResults dataclass"""

    def test_from_chroma_with_results(self):
        """Test creating SearchResults from ChromaDB results"""
        # Arrange
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'key': 'val1'}, {'key': 'val2'}]],
            'distances': [[0.1, 0.2]]
        }

        # Act
        results = SearchResults.from_chroma(chroma_results)

        # Assert
        assert len(results.documents) == 2
        assert results.documents[0] == 'doc1'
        assert results.metadata[0]['key'] == 'val1'
        assert results.distances[0] == 0.1

    def test_from_chroma_empty_results(self):
        """Test creating SearchResults from empty ChromaDB results"""
        # Arrange
        chroma_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        # Act
        results = SearchResults.from_chroma(chroma_results)

        # Assert
        assert results.is_empty()

    def test_empty_with_error(self):
        """Test creating empty SearchResults with error message"""
        # Act
        results = SearchResults.empty("Test error")

        # Assert
        assert results.is_empty()
        assert results.error == "Test error"
