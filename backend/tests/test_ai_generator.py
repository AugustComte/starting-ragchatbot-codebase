"""
Tests for AIGenerator in ai_generator.py.
Tests the generate_response() method and tool execution handling.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator


class TestGenerateResponseNoTools:
    """Tests for generate_response without tool usage"""

    def test_generate_response_without_tools(self, mock_anthropic_response_no_tool):
        """Test response generation without tools available"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            # Act
            result = generator.generate_response(query="Hello, how are you?")

            # Assert
            assert result == "This is a test response without tool use."
            mock_client.messages.create.assert_called_once()

    def test_generate_response_includes_system_prompt(self, mock_anthropic_response_no_tool):
        """Test that system prompt is included in API call"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            # Act
            generator.generate_response(query="test query")

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "system" in call_kwargs
            assert "AI assistant" in call_kwargs["system"]

    def test_generate_response_with_history(self, mock_anthropic_response_no_tool):
        """Test that conversation history is included when provided"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
            history = "User: Previous question\nAssistant: Previous answer"

            # Act
            generator.generate_response(query="Follow-up question", conversation_history=history)

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "Previous conversation" in call_kwargs["system"]
            assert history in call_kwargs["system"]


class TestGenerateResponseWithTools:
    """Tests for generate_response with tool usage"""

    def test_generate_response_passes_tools(self, mock_anthropic_response_no_tool, mock_tool_manager):
        """Test that tools are passed to API call when provided"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()

            # Act
            generator.generate_response(
                query="test query",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "tools" in call_kwargs
            assert call_kwargs["tools"] == tools

    def test_generate_response_triggers_search_tool(
        self, mock_anthropic_response_with_tool, mock_anthropic_final_response, mock_tool_manager
    ):
        """Test that content query triggers search_course_content tool"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            # First call returns tool_use, second returns final response
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()

            # Act
            result = generator.generate_response(
                query="What was covered in lesson 5 of MCP?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            mock_tool_manager.execute_tool.assert_called_once_with(
                "search_course_content",
                query="MCP lesson 5",
                course_name="MCP"
            )

    def test_generate_response_forces_outline_tool_for_outline_query(
        self, mock_anthropic_response_no_tool, mock_tool_manager
    ):
        """Test that outline keywords force get_course_outline tool"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()

            # Act
            generator.generate_response(
                query="What is the outline of the MCP course?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["tool_choice"] == {"type": "tool", "name": "get_course_outline"}

    def test_generate_response_auto_tool_choice_for_content_query(
        self, mock_anthropic_response_no_tool, mock_tool_manager
    ):
        """Test that content queries use auto tool choice"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")
            tools = mock_tool_manager.get_tool_definitions()

            # Act
            generator.generate_response(
                query="What was covered in lesson 5?",
                tools=tools,
                tool_manager=mock_tool_manager
            )

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["tool_choice"] == {"type": "auto"}


class TestToolLoop:
    """Tests for _run_tool_loop method and sequential tool calling"""

    def test_single_tool_round_calls_tool_manager(
        self, mock_anthropic_response_with_tool, mock_anthropic_final_response, mock_tool_manager
    ):
        """Test that tool manager is called with correct arguments in a single round"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="test",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            mock_tool_manager.execute_tool.assert_called_once()

    def test_single_tool_round_makes_two_api_calls(
        self, mock_anthropic_response_with_tool, mock_anthropic_final_response, mock_tool_manager
    ):
        """Test single tool round: 2 API calls, second includes tools (in-loop continuation)"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            result = generator.generate_response(
                query="test",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            assert mock_client.messages.create.call_count == 2
            second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
            # Second call is an in-loop continuation (rounds_remaining=1), so tools ARE included
            assert "tools" in second_call_kwargs
            # Messages: user query + assistant tool_use + user tool_result
            messages = second_call_kwargs["messages"]
            assert len(messages) == 3
            assert messages[2]["role"] == "user"
            assert result == mock_anthropic_final_response.content[0].text

    def test_outline_returns_result_directly(self, mock_tool_manager):
        """Test that outline tool results bypass second API call"""
        mock_outline_response = MagicMock()
        mock_outline_response.stop_reason = "tool_use"

        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "get_course_outline"
        tool_use_block.id = "tool_456"
        tool_use_block.input = {"course_name": "MCP"}
        mock_outline_response.content = [tool_use_block]

        mock_tool_manager.execute_tool.return_value = """**MCP Introduction Course**

**Course Link:** https://example.com/mcp

**Course Outline:**
- Lesson 1: Introduction
- Lesson 5: Advanced Patterns"""

        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_outline_response
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            result = generator.generate_response(
                query="What is the outline of MCP course?",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            # Outline shortcut: only the initial API call, result returned directly
            assert mock_client.messages.create.call_count == 1
            assert "MCP Introduction Course" in result
            assert "Lesson 1" in result

    def test_two_tool_rounds_makes_three_api_calls(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_response_with_tool_round2,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that two sequential tool rounds result in three total API calls"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,       # round 1: tool_use
                mock_anthropic_response_with_tool_round2, # round 2: tool_use
                mock_anthropic_final_response             # synthesis: end_turn
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            result = generator.generate_response(
                query="Find content similar to lesson 5 of MCP",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            assert mock_client.messages.create.call_count == 3
            assert mock_tool_manager.execute_tool.call_count == 2
            assert result == mock_anthropic_final_response.content[0].text

    def test_two_rounds_third_api_call_has_no_tools(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_response_with_tool_round2,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that the synthesis call after two rounds has no tools"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_response_with_tool_round2,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="test",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            third_call_kwargs = mock_client.messages.create.call_args_list[2][1]
            assert "tools" not in third_call_kwargs

    def test_messages_structure_after_two_rounds(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_response_with_tool_round2,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that message history accumulates correctly across two tool rounds"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_response_with_tool_round2,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="test query",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            # Synthesis call receives the full accumulated history
            third_call_kwargs = mock_client.messages.create.call_args_list[2][1]
            messages = third_call_kwargs["messages"]
            # user, assistant(round1), user(tool_result1), assistant(round2), user(tool_result2)
            assert len(messages) == 5
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"
            assert messages[2]["role"] == "user"
            assert messages[2]["content"][0]["type"] == "tool_result"
            assert messages[3]["role"] == "assistant"
            assert messages[4]["role"] == "user"
            assert messages[4]["content"][0]["type"] == "tool_result"

    def test_max_rounds_cap_stops_after_two_tool_calls(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_response_with_tool_round2,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that MAX_ROUNDS=2 prevents a third tool call even if Claude requests one"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            # Queue four responses — only the first three should be consumed
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,        # round 1
                mock_anthropic_response_with_tool_round2, # round 2 (rounds exhausted after this)
                mock_anthropic_final_response,             # forced synthesis call
                MagicMock()                                # should never be reached
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="test",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            assert mock_client.messages.create.call_count == 3

    def test_tools_included_in_loop_calls_excluded_from_synthesis(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_response_with_tool_round2,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that in-loop calls include tools but the synthesis call does not"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_response_with_tool_round2,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="test",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            call_kwargs_list = mock_client.messages.create.call_args_list
            # Call 1 (generate_response): has tools
            assert "tools" in call_kwargs_list[0][1]
            # Call 2 (loop round 2): has tools
            assert "tools" in call_kwargs_list[1][1]
            # Call 3 (synthesis): no tools
            assert "tools" not in call_kwargs_list[2][1]

    def test_tool_choice_auto_for_round_two(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that the in-loop API call uses auto tool_choice, not forced"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            generator.generate_response(
                query="What is MCP?",
                tools=mock_tool_manager.get_tool_definitions(),
                tool_manager=mock_tool_manager
            )

            # The in-loop call (call #2) should use auto tool_choice
            second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
            assert second_call_kwargs.get("tool_choice") == {"type": "auto"}

    def test_tool_error_triggers_graceful_synthesis(
        self,
        mock_anthropic_response_with_tool,
        mock_anthropic_final_response,
        mock_tool_manager_with_error
    ):
        """Test that a tool execution exception breaks the loop and triggers synthesis"""
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                mock_anthropic_response_with_tool,
                mock_anthropic_final_response
            ]
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            result = generator.generate_response(
                query="test",
                tools=mock_tool_manager_with_error.get_tool_definitions(),
                tool_manager=mock_tool_manager_with_error
            )

            # Error breaks the loop: initial call + synthesis call only
            assert mock_client.messages.create.call_count == 2
            # Synthesis call has no tools
            second_call_kwargs = mock_client.messages.create.call_args_list[1][1]
            assert "tools" not in second_call_kwargs
            # Synthesis call messages include the error as a tool_result
            messages = second_call_kwargs["messages"]
            tool_result_msg = messages[2]
            assert tool_result_msg["role"] == "user"
            assert "failed" in tool_result_msg["content"][0]["content"].lower()
            # Final return is the synthesis text, not a raw exception
            assert result == mock_anthropic_final_response.content[0].text


class TestAPIParameters:
    """Tests for API parameter configuration"""

    def test_base_params_correct(self, mock_anthropic_response_no_tool):
        """Test that base parameters are correctly set"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            # Act
            generator.generate_response(query="test")

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["temperature"] == 0
            assert call_kwargs["max_tokens"] == 800

    def test_messages_format_correct(self, mock_anthropic_response_no_tool):
        """Test that messages are formatted correctly"""
        # Arrange
        with patch('ai_generator.anthropic.Anthropic') as MockClient:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response_no_tool
            MockClient.return_value = mock_client

            generator = AIGenerator(api_key="test-key", model="claude-sonnet-4-20250514")

            # Act
            generator.generate_response(query="What is MCP?")

            # Assert
            call_kwargs = mock_client.messages.create.call_args[1]
            messages = call_kwargs["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert "What is MCP?" in messages[0]["content"]
