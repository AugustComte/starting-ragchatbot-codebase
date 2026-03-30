"""
Tests for RAGSystem in rag_system.py.
Tests the query() method and component orchestration.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRAGSystemQuery:
    """Tests for RAGSystem.query() method"""

    def test_query_returns_response_and_sources(self, test_config, mock_tool_manager):
        """Test that query returns tuple of (response, sources)"""
        # Arrange
        with patch('rag_system.VectorStore') as MockVectorStore, \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            # Configure mocks
            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Test response about MCP"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            mock_session.get_conversation_history.return_value = None
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            response, sources = rag.query("What is MCP?")

            # Assert
            assert response == "Test response about MCP"
            assert isinstance(sources, list)

    def test_query_with_session_uses_history(self, test_config, mock_tool_manager):
        """Test that session history is retrieved and passed to AI"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Response"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            mock_session.get_conversation_history.return_value = "Previous conversation"
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            rag.query("Follow up question", session_id="session-123")

            # Assert
            mock_session.get_conversation_history.assert_called_once_with("session-123")
            mock_ai.generate_response.assert_called_once()
            call_kwargs = mock_ai.generate_response.call_args[1]
            assert call_kwargs["conversation_history"] == "Previous conversation"

    def test_query_resets_sources_after_use(self, test_config, mock_tool_manager):
        """Test that sources are reset after being retrieved"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Response"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            rag.query("Test query")

            # Assert
            mock_tm.get_last_sources.assert_called_once()
            mock_tm.reset_sources.assert_called_once()

    def test_query_passes_tools_to_ai(self, test_config, mock_tool_manager):
        """Test that tool definitions are passed to AI generator"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Response"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            rag.query("Test query")

            # Assert
            call_kwargs = mock_ai.generate_response.call_args[1]
            assert "tools" in call_kwargs
            assert call_kwargs["tools"] == mock_tm.get_tool_definitions()

    def test_query_updates_session_history(self, test_config, mock_tool_manager):
        """Test that conversation history is updated after query"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Response text"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            rag.query("Test query", session_id="session-123")

            # Assert
            mock_session.add_exchange.assert_called_once_with(
                "session-123", "Test query", "Response text"
            )


class TestRAGSystemToolRegistration:
    """Tests for tool registration in RAGSystem"""

    def test_both_tools_registered(self, test_config):
        """Test that both search and outline tools are registered"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator'), \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager'), \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool') as MockSearchTool, \
             patch('rag_system.CourseOutlineTool') as MockOutlineTool:

            mock_tm = MagicMock()
            MockToolManager.return_value = mock_tm

            # Act
            from rag_system import RAGSystem
            rag = RAGSystem(test_config)

            # Assert - register_tool should be called twice
            assert mock_tm.register_tool.call_count == 2

    def test_search_tool_uses_vector_store(self, test_config):
        """Test that search tool is initialized with vector store"""
        # Arrange
        with patch('rag_system.VectorStore') as MockVectorStore, \
             patch('rag_system.AIGenerator'), \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager'), \
             patch('rag_system.ToolManager'), \
             patch('rag_system.CourseSearchTool') as MockSearchTool, \
             patch('rag_system.CourseOutlineTool'):

            mock_vs = MagicMock()
            MockVectorStore.return_value = mock_vs

            # Act
            from rag_system import RAGSystem
            rag = RAGSystem(test_config)

            # Assert
            MockSearchTool.assert_called_once_with(mock_vs)


class TestRAGSystemPromptConstruction:
    """Tests for prompt construction in query method"""

    def test_query_wraps_user_question(self, test_config, mock_tool_manager):
        """Test that user query is wrapped with instructions"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.return_value = "Response"
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act
            rag.query("What is MCP?")

            # Assert
            call_kwargs = mock_ai.generate_response.call_args[1]
            assert "course materials" in call_kwargs["query"].lower()
            assert "What is MCP?" in call_kwargs["query"]


class TestRAGSystemErrorHandling:
    """Tests for error handling in RAGSystem"""

    def test_query_propagates_ai_errors(self, test_config, mock_tool_manager):
        """Test that AI generator errors propagate up"""
        # Arrange
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as MockAIGenerator, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager') as MockSessionManager, \
             patch('rag_system.ToolManager') as MockToolManager, \
             patch('rag_system.CourseSearchTool'), \
             patch('rag_system.CourseOutlineTool'):

            mock_ai = MagicMock()
            mock_ai.generate_response.side_effect = Exception("API error")
            MockAIGenerator.return_value = mock_ai

            mock_tm = mock_tool_manager
            MockToolManager.return_value = mock_tm

            mock_session = MagicMock()
            MockSessionManager.return_value = mock_session

            from rag_system import RAGSystem
            rag = RAGSystem(test_config)
            rag.tool_manager = mock_tm

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                rag.query("Test query")

            assert "API error" in str(exc_info.value)
