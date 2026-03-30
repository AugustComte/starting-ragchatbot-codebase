import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    MAX_ROUNDS = 2  # Maximum sequential tool-call rounds per query

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for course information.

Available Tools:
1. **get_course_outline**: Get course structure including title, link, and complete lesson list
2. **search_course_content**: Search course materials for specific content or detailed information

CRITICAL - Tool Selection Rules:
- **ALWAYS use get_course_outline** when the user asks about:
  - "outline" of a course
  - "what lessons" or "how many lessons"
  - "what's in" or "what does [course] cover"
  - "course structure" or "course topics"
  - "list of lessons" or "lesson list"
- **Use search_course_content** ONLY for:
  - Specific content questions (e.g., "what is X?", "explain Y")
  - Detailed explanations from course materials
  - Looking up definitions, concepts, or procedures

Response Protocol for Outline Queries (get_course_outline):
- Output the tool result EXACTLY as returned - do not rephrase or reformat
- The tool returns pre-formatted markdown with title, link, and lesson list
- Do NOT add introductions, summaries, or extra commentary

Response Protocol for Content Queries (search_course_content):
- Synthesize search results into accurate, fact-based responses
- **No meta-commentary**: Provide direct answers only
- Do not mention "based on the search results"

General Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Use appropriate tool first, then answer
- **Sequential tool use**: You may use up to 2 tool calls when the first result provides information needed for a more precise second search. Example: get a course outline to identify a specific lesson title, then search for that topic in another course.
- After all tool use, synthesize the retrieved information into a complete answer without mentioning the number of tools used.

All responses must be concise, educational, and clear.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            # Force outline tool for outline-related queries
            query_lower = query.lower()
            outline_keywords = ["outline", "lesson list", "what lessons", "course structure"]
            is_outline_query = any(keyword in query_lower for keyword in outline_keywords)
            if is_outline_query:
                api_params["tool_choice"] = {"type": "tool", "name": "get_course_outline"}
            else:
                api_params["tool_choice"] = {"type": "auto"}

        # Make initial API call
        response = self.client.messages.create(**api_params)

        # Delegate to tool loop if tool use requested
        if response.stop_reason == "tool_use" and tool_manager:
            return self._run_tool_loop(
                response=response,
                messages=api_params["messages"],
                system_content=system_content,
                tool_manager=tool_manager,
                rounds_remaining=self.MAX_ROUNDS - 1
            )

        return response.content[0].text

    def _run_tool_loop(self, response, messages, system_content, tool_manager, rounds_remaining):
        """
        Execute tool calls and loop until done or rounds exhausted.

        Each iteration executes tools from the current response, appends results
        to the message history, and either makes another tool-capable call (if
        rounds remain) or a final synthesis call (no tools).

        Args:
            response: Current API response with stop_reason "tool_use"
            messages: Accumulated message list (mutated in place)
            system_content: System prompt string, unchanged across rounds
            tool_manager: Manager to execute tools
            rounds_remaining: How many more tool-call rounds are allowed after this one

        Returns:
            Final response text
        """
        while True:
            # Append assistant's tool-use response to message history
            messages.append({"role": "assistant", "content": response.content})

            # Execute all tool calls, collect results
            tool_results = []
            outline_result = None
            error_occurred = False

            for content_block in response.content:
                if content_block.type != "tool_use":
                    continue

                try:
                    result = tool_manager.execute_tool(
                        content_block.name,
                        **content_block.input
                    )
                except Exception as e:
                    result = f"Tool execution failed: {str(e)}"
                    error_occurred = True

                if content_block.name == "get_course_outline":
                    outline_result = result

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": result
                })

                if error_occurred:
                    break

            # Outline shortcut: return pre-formatted result directly
            if outline_result:
                return outline_result

            # Append tool results to message history
            messages.append({"role": "user", "content": tool_results})

            # If rounds exhausted or tool error, make final synthesis call (no tools)
            if rounds_remaining <= 0 or error_occurred:
                final_response = self.client.messages.create(
                    **self.base_params,
                    messages=messages,
                    system=system_content
                )
                return final_response.content[0].text

            # Make next API call with tools still available
            next_response = self.client.messages.create(
                **self.base_params,
                messages=messages,
                system=system_content,
                tools=tool_manager.get_tool_definitions(),
                tool_choice={"type": "auto"}
            )

            # If no further tool use requested, return directly
            if next_response.stop_reason != "tool_use":
                return next_response.content[0].text

            # Continue loop with next tool-use response
            response = next_response
            rounds_remaining -= 1
