import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
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
- **One tool call per query maximum**

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
        
        # Prepare API call parameters efficiently
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

        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools

        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()

        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})

        # Execute all tool calls and collect results
        tool_results = []
        outline_result = None  # Track if outline tool was used

        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name,
                    **content_block.input
                )

                # If outline tool was used, return its result directly
                if content_block.name == "get_course_outline":
                    outline_result = tool_result

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })

        # For outline queries, return the formatted result directly
        if outline_result:
            return outline_result

        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }

        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text