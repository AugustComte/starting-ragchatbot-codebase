"""
Tests for CourseSearchTool and CourseOutlineTool in search_tools.py.
Tests the execute() method and result formatting.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_tools import CourseSearchTool, CourseOutlineTool, ToolManager
from vector_store import SearchResults


class TestCourseSearchToolExecute:
    """Tests for CourseSearchTool.execute() method"""

    def test_execute_returns_formatted_results(self, mock_vector_store, sample_search_results):
        """Test that execute returns properly formatted results"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Act
        result = tool.execute(query="lesson 5 content")

        # Assert
        assert "[MCP Introduction Course - Lesson 5]" in result
        mock_vector_store.search.assert_called_once_with(
            query="lesson 5 content",
            course_name=None,
            lesson_number=None
        )

    def test_execute_with_course_filter(self, mock_vector_store, sample_search_results):
        """Test that course_name filter is passed to vector store"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Act
        result = tool.execute(query="MCP patterns", course_name="MCP")

        # Assert
        mock_vector_store.search.assert_called_once_with(
            query="MCP patterns",
            course_name="MCP",
            lesson_number=None
        )

    def test_execute_with_lesson_filter(self, mock_vector_store, sample_search_results):
        """Test that lesson_number filter is passed to vector store"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Act
        result = tool.execute(query="content", course_name="MCP", lesson_number=5)

        # Assert
        mock_vector_store.search.assert_called_once_with(
            query="content",
            course_name="MCP",
            lesson_number=5
        )

    def test_execute_course_not_found(self, mock_vector_store, error_search_results):
        """Test that error message is returned when course not found"""
        # Arrange
        mock_vector_store.search.return_value = error_search_results
        tool = CourseSearchTool(mock_vector_store)

        # Act
        result = tool.execute(query="anything", course_name="nonexistent")

        # Assert
        assert "No course found matching 'nonexistent'" in result

    def test_execute_no_results(self, mock_empty_vector_store):
        """Test that appropriate message is returned when no results found"""
        # Arrange
        tool = CourseSearchTool(mock_empty_vector_store)

        # Act
        result = tool.execute(query="completely irrelevant query")

        # Assert
        assert "No relevant content found" in result

    def test_execute_no_results_with_filters(self, mock_empty_vector_store):
        """Test no results message includes filter context"""
        # Arrange
        tool = CourseSearchTool(mock_empty_vector_store)

        # Act
        result = tool.execute(query="test", course_name="Test Course", lesson_number=99)

        # Assert
        assert "No relevant content found" in result
        assert "course 'Test Course'" in result
        assert "lesson 99" in result

    def test_execute_search_error(self, mock_vector_store):
        """Test that ChromaDB errors are handled gracefully"""
        # Arrange
        mock_vector_store.search.return_value = SearchResults(
            documents=[], metadata=[], distances=[],
            error="Search error: Connection failed"
        )
        tool = CourseSearchTool(mock_vector_store)

        # Act
        result = tool.execute(query="test")

        # Assert
        assert "Search error" in result

    def test_format_results_tracks_sources(self, mock_vector_store, sample_search_results):
        """Test that sources are tracked in last_sources after search"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson-5"
        tool = CourseSearchTool(mock_vector_store)

        # Act
        tool.execute(query="lesson 5")

        # Assert
        assert len(tool.last_sources) > 0
        assert tool.last_sources[0]["text"] == "MCP Introduction Course - Lesson 5"

    def test_format_results_gets_lesson_link(self, mock_vector_store, sample_search_results):
        """Test that lesson links are fetched from vector store"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson-5"
        tool = CourseSearchTool(mock_vector_store)

        # Act
        tool.execute(query="lesson 5")

        # Assert
        mock_vector_store.get_lesson_link.assert_called()
        assert tool.last_sources[0]["link"] == "https://example.com/lesson-5"


class TestCourseOutlineToolExecute:
    """Tests for CourseOutlineTool.execute() method"""

    def test_execute_returns_outline(self, mock_vector_store, mock_catalog_results):
        """Test that execute returns formatted course outline"""
        # Arrange
        mock_vector_store.course_catalog.query.return_value = mock_catalog_results
        mock_vector_store.course_catalog.get.return_value = {
            'ids': ['MCP Introduction Course'],
            'metadatas': [mock_catalog_results['metadatas'][0][0]]
        }
        tool = CourseOutlineTool(mock_vector_store)

        # Act
        result = tool.execute(course_name="MCP")

        # Assert
        assert "MCP Introduction Course" in result
        assert "Lesson" in result

    def test_execute_course_not_found(self, mock_empty_vector_store):
        """Test error when course not found"""
        # Arrange
        mock_empty_vector_store.course_catalog.query.return_value = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]],
            'ids': [[]]
        }
        tool = CourseOutlineTool(mock_empty_vector_store)

        # Act
        result = tool.execute(course_name="nonexistent")

        # Assert
        assert "No course found" in result

    def test_execute_tracks_sources(self, mock_vector_store, mock_catalog_results):
        """Test that sources are tracked for outline queries"""
        # Arrange
        mock_vector_store.course_catalog.query.return_value = mock_catalog_results
        mock_vector_store.course_catalog.get.return_value = {
            'ids': ['MCP Introduction Course'],
            'metadatas': [mock_catalog_results['metadatas'][0][0]]
        }
        tool = CourseOutlineTool(mock_vector_store)

        # Act
        tool.execute(course_name="MCP")

        # Assert
        assert len(tool.last_sources) == 1
        assert "MCP Introduction Course" in tool.last_sources[0]["text"]


class TestToolManager:
    """Tests for ToolManager class"""

    def test_register_tool(self, mock_vector_store):
        """Test that tools can be registered"""
        # Arrange
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)

        # Act
        manager.register_tool(tool)

        # Assert
        assert "search_course_content" in manager.tools

    def test_get_tool_definitions(self, mock_vector_store):
        """Test that tool definitions are returned correctly"""
        # Arrange
        manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        outline_tool = CourseOutlineTool(mock_vector_store)
        manager.register_tool(search_tool)
        manager.register_tool(outline_tool)

        # Act
        definitions = manager.get_tool_definitions()

        # Assert
        assert len(definitions) == 2
        tool_names = [d["name"] for d in definitions]
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_execute_tool(self, mock_vector_store, sample_search_results):
        """Test that execute_tool routes to correct tool"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Act
        result = manager.execute_tool("search_course_content", query="test")

        # Assert
        assert "[MCP Introduction Course" in result

    def test_execute_tool_not_found(self):
        """Test error when tool not found"""
        # Arrange
        manager = ToolManager()

        # Act
        result = manager.execute_tool("nonexistent_tool", query="test")

        # Assert
        assert "Tool 'nonexistent_tool' not found" in result

    def test_get_last_sources(self, mock_vector_store, sample_search_results):
        """Test that get_last_sources returns sources from last search"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com"
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute a search first
        manager.execute_tool("search_course_content", query="test")

        # Act
        sources = manager.get_last_sources()

        # Assert
        assert len(sources) > 0

    def test_reset_sources(self, mock_vector_store, sample_search_results):
        """Test that reset_sources clears sources from all tools"""
        # Arrange
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com"
        manager = ToolManager()
        tool = CourseSearchTool(mock_vector_store)
        manager.register_tool(tool)

        # Execute a search first
        manager.execute_tool("search_course_content", query="test")
        assert len(manager.get_last_sources()) > 0

        # Act
        manager.reset_sources()

        # Assert
        assert len(manager.get_last_sources()) == 0


class TestToolDefinitions:
    """Tests for tool definition schemas"""

    def test_search_tool_definition_schema(self, mock_vector_store):
        """Test search tool has correct schema"""
        # Arrange
        tool = CourseSearchTool(mock_vector_store)

        # Act
        definition = tool.get_tool_definition()

        # Assert
        assert definition["name"] == "search_course_content"
        assert "query" in definition["input_schema"]["properties"]
        assert "course_name" in definition["input_schema"]["properties"]
        assert "lesson_number" in definition["input_schema"]["properties"]
        assert definition["input_schema"]["required"] == ["query"]

    def test_outline_tool_definition_schema(self, mock_vector_store):
        """Test outline tool has correct schema"""
        # Arrange
        tool = CourseOutlineTool(mock_vector_store)

        # Act
        definition = tool.get_tool_definition()

        # Assert
        assert definition["name"] == "get_course_outline"
        assert "course_name" in definition["input_schema"]["properties"]
        assert definition["input_schema"]["required"] == ["course_name"]
