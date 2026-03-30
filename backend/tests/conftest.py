"""
Shared test fixtures for RAG chatbot tests.
Provides both mocked fixtures for unit tests and real ChromaDB fixtures for integration tests.
"""
import pytest
import tempfile
import shutil
import sys
import os
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vector_store import SearchResults
from models import Course, Lesson, CourseChunk


# ============================================
# Sample Test Data
# ============================================

@pytest.fixture
def sample_course() -> Course:
    """Sample course for testing"""
    return Course(
        title="MCP Introduction Course",
        course_link="https://example.com/mcp-course",
        instructor="Test Instructor",
        lessons=[
            Lesson(
                lesson_number=1,
                title="What is MCP?",
                lesson_link="https://example.com/mcp-course/lesson-1"
            ),
            Lesson(
                lesson_number=2,
                title="MCP Architecture",
                lesson_link="https://example.com/mcp-course/lesson-2"
            ),
            Lesson(
                lesson_number=5,
                title="Advanced MCP Patterns",
                lesson_link="https://example.com/mcp-course/lesson-5"
            ),
        ]
    )


# Sample lesson content for creating chunks
SAMPLE_LESSON_CONTENT = {
    1: "MCP stands for Model Context Protocol. It allows AI models to access external tools.",
    2: "MCP uses a client-server architecture with JSON-RPC for communication.",
    5: "Lesson 5 covers advanced patterns including tool chaining and context management."
}


@pytest.fixture
def sample_chunks(sample_course) -> List[CourseChunk]:
    """Sample course chunks for testing"""
    chunks = []
    for i, lesson in enumerate(sample_course.lessons):
        lesson_content = SAMPLE_LESSON_CONTENT.get(lesson.lesson_number, "Default content")
        chunks.append(CourseChunk(
            course_title=sample_course.title,
            lesson_number=lesson.lesson_number,
            content=f"Course {sample_course.title} Lesson {lesson.lesson_number} content: {lesson_content}",
            chunk_index=i
        ))
    return chunks


@pytest.fixture
def sample_search_results() -> SearchResults:
    """Sample search results with metadata"""
    return SearchResults(
        documents=[
            "Course MCP Introduction Course Lesson 5 content: Lesson 5 covers advanced patterns including tool chaining and context management.",
            "Course MCP Introduction Course Lesson 2 content: MCP uses a client-server architecture with JSON-RPC for communication."
        ],
        metadata=[
            {"course_title": "MCP Introduction Course", "lesson_number": 5, "chunk_index": 2},
            {"course_title": "MCP Introduction Course", "lesson_number": 2, "chunk_index": 1}
        ],
        distances=[0.2, 0.4]
    )


@pytest.fixture
def empty_search_results() -> SearchResults:
    """Empty search results for testing no-match scenarios"""
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results() -> SearchResults:
    """Search results with error for testing error handling"""
    return SearchResults(documents=[], metadata=[], distances=[], error="No course found matching 'nonexistent'")


# ============================================
# Mock Fixtures for Unit Tests
# ============================================

@pytest.fixture
def mock_chroma_results():
    """Mock ChromaDB query results format"""
    return {
        'documents': [[
            "Course MCP Introduction Course Lesson 5 content: Lesson 5 covers advanced patterns.",
            "Course MCP Introduction Course Lesson 2 content: MCP architecture overview."
        ]],
        'metadatas': [[
            {"course_title": "MCP Introduction Course", "lesson_number": 5, "chunk_index": 2},
            {"course_title": "MCP Introduction Course", "lesson_number": 2, "chunk_index": 1}
        ]],
        'distances': [[0.2, 0.4]],
        'ids': [['id1', 'id2']]
    }


@pytest.fixture
def mock_catalog_results():
    """Mock ChromaDB catalog query results for course resolution"""
    return {
        'documents': [["MCP Introduction Course"]],
        'metadatas': [[{
            "title": "MCP Introduction Course",
            "instructor": "Test Instructor",
            "course_link": "https://example.com/mcp-course",
            "lessons_json": '[{"lesson_number": 1, "lesson_title": "What is MCP?", "lesson_link": "https://example.com/mcp-course/lesson-1"}, {"lesson_number": 5, "lesson_title": "Advanced MCP Patterns", "lesson_link": "https://example.com/mcp-course/lesson-5"}]',
            "lesson_count": 2
        }]],
        'distances': [[0.1]],
        'ids': [["MCP Introduction Course"]]
    }


@pytest.fixture
def mock_vector_store(mock_chroma_results, mock_catalog_results):
    """Mock VectorStore for unit testing"""
    mock_store = MagicMock()

    # Mock course_content collection
    mock_store.course_content.query.return_value = mock_chroma_results

    # Mock course_catalog collection
    mock_store.course_catalog.query.return_value = mock_catalog_results
    mock_store.course_catalog.get.return_value = {
        'ids': ['MCP Introduction Course'],
        'metadatas': [mock_catalog_results['metadatas'][0][0]]
    }

    # Mock search method
    mock_store.search.return_value = SearchResults.from_chroma(mock_chroma_results)

    # Mock get_lesson_link
    mock_store.get_lesson_link.return_value = "https://example.com/mcp-course/lesson-5"

    # Mock max_results
    mock_store.max_results = 5

    return mock_store


@pytest.fixture
def mock_empty_vector_store():
    """Mock VectorStore that returns empty results"""
    mock_store = MagicMock()

    empty_results = {
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]],
        'ids': [[]]
    }

    mock_store.course_content.query.return_value = empty_results
    mock_store.course_catalog.query.return_value = empty_results
    mock_store.search.return_value = SearchResults(documents=[], metadata=[], distances=[])
    mock_store.max_results = 5

    return mock_store


@pytest.fixture
def mock_anthropic_response_no_tool():
    """Mock Anthropic response without tool use"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [MagicMock(type="text", text="This is a test response without tool use.")]
    return mock_response


@pytest.fixture
def mock_anthropic_response_with_tool():
    """Mock Anthropic response with tool use"""
    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"

    # Create tool use block
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = "search_course_content"
    tool_use_block.id = "tool_123"
    tool_use_block.input = {"query": "MCP lesson 5", "course_name": "MCP"}

    mock_response.content = [tool_use_block]
    return mock_response


@pytest.fixture
def mock_anthropic_final_response():
    """Mock final Anthropic response after tool execution"""
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [MagicMock(type="text", text="Based on the course content, lesson 5 covers advanced MCP patterns.")]
    return mock_response


@pytest.fixture
def mock_anthropic_response_with_tool_round2():
    """Mock Anthropic response with tool use for round 2 (search after seeing outline)"""
    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"

    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = "search_course_content"
    tool_use_block.id = "tool_456"
    tool_use_block.input = {"query": "Advanced MCP patterns", "course_name": "MCP"}

    mock_response.content = [tool_use_block]
    return mock_response


@pytest.fixture
def mock_tool_manager_with_error():
    """Mock ToolManager where execute_tool raises an exception"""
    mock_tm = MagicMock()
    mock_tm.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for content in courses",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    ]
    mock_tm.execute_tool.side_effect = Exception("Database connection failed")
    return mock_tm


@pytest.fixture
def mock_anthropic_client(mock_anthropic_response_no_tool):
    """Mock Anthropic client for unit testing"""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_anthropic_response_no_tool
    return mock_client


# ============================================
# Real ChromaDB Fixtures for Integration Tests
# ============================================

@pytest.fixture
def temp_chroma_path():
    """Create a temporary directory for ChromaDB"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def real_vector_store(temp_chroma_path):
    """Real VectorStore instance with temporary ChromaDB for integration tests"""
    from vector_store import VectorStore

    store = VectorStore(
        chroma_path=temp_chroma_path,
        embedding_model="all-MiniLM-L6-v2",
        max_results=5
    )
    return store


@pytest.fixture
def populated_vector_store(real_vector_store, sample_course, sample_chunks):
    """Real VectorStore populated with test data"""
    # Add course metadata
    real_vector_store.add_course_metadata(sample_course)

    # Add course content chunks
    real_vector_store.add_course_content(sample_chunks)

    return real_vector_store


# ============================================
# Config Fixtures
# ============================================

@pytest.fixture
def test_config():
    """Test configuration"""
    @dataclass
    class TestConfig:
        ANTHROPIC_API_KEY: str = "test-api-key"
        ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
        EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        CHUNK_SIZE: int = 800
        CHUNK_OVERLAP: int = 100
        MAX_RESULTS: int = 5
        MAX_HISTORY: int = 2
        CHROMA_PATH: str = "./test_chroma_db"

    return TestConfig()


# ============================================
# Tool Manager Fixtures
# ============================================

@pytest.fixture
def mock_tool_manager():
    """Mock ToolManager for testing"""
    mock_tm = MagicMock()
    mock_tm.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for content in courses",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "course_name": {"type": "string"},
                    "lesson_number": {"type": "integer"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_course_outline",
            "description": "Get course outline",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_name": {"type": "string"}
                },
                "required": ["course_name"]
            }
        }
    ]
    mock_tm.execute_tool.return_value = "[MCP Introduction Course - Lesson 5]\nLesson 5 covers advanced patterns."
    mock_tm.get_last_sources.return_value = [{"text": "MCP Introduction Course - Lesson 5", "link": "https://example.com"}]
    mock_tm.reset_sources.return_value = None

    return mock_tm
