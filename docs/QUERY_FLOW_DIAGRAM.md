# Query Processing Flow Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                              FRONTEND (script.js)                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                      │
                    ┌─────────────────┴──────────────────┐
                    │  1. User types query & clicks send │
                    │     sendMessage() triggered        │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │  2. Display user message in chat   │
                    │     Show loading animation          │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │  3. POST /api/query                 │
                    │     { query, session_id }           │
                    └─────────────────┬──────────────────┘
                                      │
                                      │ HTTP Request
                                      ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          BACKEND - FastAPI (app.py)                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                      │
                    ┌─────────────────▼──────────────────┐
                    │  4. @app.post("/api/query")        │
                    │     Validate QueryRequest          │
                    │     Create session if needed       │
                    └─────────────────┬──────────────────┘
                                      │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        RAG SYSTEM (rag_system.py)                          ┃
┃                                                                             ┃
┃   ┌─────────────────────────────────────────────────────────────────┐    ┃
┃   │  5. RAGSystem.query()                                            │    ┃
┃   │     - Get conversation history (SessionManager)                  │    ┃
┃   │     - Build prompt: "Answer this question..."                    │    ┃
┃   └────────────────────────────┬────────────────────────────────────┘    ┃
┃                                 │                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                  │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      AI GENERATOR (ai_generator.py)                        ┃
┃                                                                             ┃
┃   ┌─────────────────────────────────────────────────────────────────┐    ┃
┃   │  6. AIGenerator.generate_response()                              │    ┃
┃   │     - Build system prompt + history                              │    ┃
┃   │     - Include tool definitions                                   │    ┃
┃   │     - Call Claude API with tool_choice: "auto"                   │    ┃
┃   └────────────────────────────┬────────────────────────────────────┘    ┃
┃                                 │                                          ┃
┃                    ┌────────────┴────────────┐                            ┃
┃                    │   Claude decides...      │                            ┃
┃                    └──┬──────────────────┬───┘                            ┃
┃                       │                  │                                 ┃
┃         ┌─────────────▼─────────┐   ┌───▼──────────────────┐             ┃
┃         │  PATH A: Use Tool      │   │  PATH B: Direct      │             ┃
┃         │  (search needed)       │   │  (general knowledge) │             ┃
┃         └─────────────┬──────────┘   └───┬──────────────────┘             ┃
┗━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                        │                  │
         ┌──────────────▼──────────┐       │
         │     PATH A CONTINUES     │       │
         └──────────────┬──────────┘       │
                        │                  │
┏━━━━━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━┓│
┃  TOOL EXECUTION (search_tools.py)       ┃│
┃                                          ┃│
┃  ┌────────────────────────────────────┐ ┃│
┃  │ 7. ToolManager.execute_tool()      │ ┃│
┃  │    CourseSearchTool.execute()      │ ┃│
┃  │    - query: "what is..."           │ ┃│
┃  │    - course_name: "MCP" (optional) │ ┃│
┃  │    - lesson_number: 1 (optional)   │ ┃│
┃  └───────────────┬────────────────────┘ ┃│
┗━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━┛│
                   │                       │
┏━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━┓│
┃  VECTOR STORE (vector_store.py)        ┃│
┃                                         ┃│
┃  ┌───────────────────────────────────┐ ┃│
┃  │ 8. VectorStore.search()           │ ┃│
┃  │                                    │ ┃│
┃  │  Step 1: Resolve course name      │ ┃│
┃  │  ┌──────────────────────────────┐ │ ┃│
┃  │  │ course_catalog.query()       │ │ ┃│
┃  │  │ "MCP" → finds full course    │ │ ┃│
┃  │  │ title via semantic search    │ │ ┃│
┃  │  └──────────────────────────────┘ │ ┃│
┃  │                                    │ ┃│
┃  │  Step 2: Build filter             │ ┃│
┃  │  ┌──────────────────────────────┐ │ ┃│
┃  │  │ { course_title: "...",       │ │ ┃│
┃  │  │   lesson_number: 1 }         │ │ ┃│
┃  │  └──────────────────────────────┘ │ ┃│
┃  │                                    │ ┃│
┃  │  Step 3: Search content           │ ┃│
┃  │  ┌──────────────────────────────┐ │ ┃│
┃  │  │ course_content.query()       │ │ ┃│
┃  │  │ - Query embeddings           │ │ ┃│
┃  │  │ - Apply filters              │ │ ┃│
┃  │  │ - Return top N results       │ │ ┃│
┃  │  └──────────────────────────────┘ │ ┃│
┃  └───────────────┬───────────────────┘ ┃│
┃                  │                      ┃│
┃  ┌───────────────▼───────────────────┐ ┃│
┃  │ 9. Return SearchResults            │ ┃│
┃  │    - documents: [text chunks]      │ ┃│
┃  │    - metadata: [course, lesson]    │ ┃│
┃  │    - distances: [relevance scores] │ ┃│
┃  └───────────────┬───────────────────┘ ┃│
┗━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━┛│
                   │                      │
         ┌─────────▼──────────┐           │
         │ 10. Format Results  │           │
         │  CourseSearchTool   │           │
         │  adds headers:      │           │
         │  "[Course - Lesson]"│           │
         │  Stores sources     │           │
         └─────────┬───────────┘           │
                   │                       │
         ┌─────────▼──────────┐            │
         │ 11. Return to      │            │
         │  Claude API with   │            │
         │  tool results      │            │
         └─────────┬───────────┘           │
                   │                       │
┏━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━┓│
┃  AI GENERATOR - Final Response          ┃│
┃                                          ┃│
┃  ┌────────────────────────────────────┐ ┃│
┃  │ 12. Claude synthesizes answer      │ ┃│
┃  │     using search results           │ ┃│
┃  │     Returns final text             │ ┃│
┃  └───────────────┬────────────────────┘ ┃│
┗━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━┛│
                   │                       │
                   └───────────────────────┤
                                           │
                   ┌───────────────────────▼──────────┐
                   │  Both paths converge here         │
                   │  response_text is ready           │
                   └───────────────────────┬──────────┘
                                           │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      RAG SYSTEM - Response Assembly                        ┃
┃                                                                             ┃
┃   ┌─────────────────────────────────────────────────────────────────┐    ┃
┃   │ 13. Get sources from ToolManager                                 │    ┃
┃   │     Reset sources for next query                                 │    ┃
┃   │     Update SessionManager with conversation                      │    ┃
┃   │     Return (response_text, sources_list)                         │    ┃
┃   └────────────────────────────┬────────────────────────────────────┘    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                  │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          BACKEND - FastAPI Response                        ┃
┃                                                                             ┃
┃   ┌─────────────────────────────────────────────────────────────────┐    ┃
┃   │ 14. Package QueryResponse                                        │    ┃
┃   │     {                                                            │    ┃
┃   │       "answer": "response text",                                 │    ┃
┃   │       "sources": ["Course A - Lesson 1", ...],                   │    ┃
┃   │       "session_id": "session_1"                                  │    ┃
┃   │     }                                                            │    ┃
┃   └────────────────────────────┬────────────────────────────────────┘    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                                  │
                                  │ HTTP Response (JSON)
                                  ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                              FRONTEND - Display                            ┃
┃                                                                             ┃
┃   ┌─────────────────────────────────────────────────────────────────┐    ┃
┃   │ 15. Receive response                                             │    ┃
┃   │     - Store session_id                                           │    ┃
┃   │     - Remove loading animation                                   │    ┃
┃   │     - Render markdown answer                                     │    ┃
┃   │     - Display sources in collapsible section                     │    ┃
┃   │     - Scroll chat to bottom                                      │    ┃
┃   │     - Re-enable input                                            │    ┃
┃   └─────────────────────────────────────────────────────────────────┘    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


═══════════════════════════════════════════════════════════════════════════

KEY COMPONENTS:

📂 ChromaDB Collections:
   ├─ course_catalog    → Course metadata (titles, instructors, lessons)
   └─ course_content    → Text chunks with embeddings

🔧 Tool-Based Architecture:
   - Claude autonomously decides: Search vs General Knowledge
   - PATH A: Searches vector store for course content
   - PATH B: Answers directly from training data

💾 Session Management:
   - Maintains conversation history (last N exchanges)
   - Enables contextual follow-up questions

🎯 Smart Search Features:
   - Fuzzy course name matching (semantic search)
   - Optional lesson filtering
   - Contextual chunk formatting

═══════════════════════════════════════════════════════════════════════════
```

## Simplified Flow

```
User Input
    ↓
Frontend (script.js)
    ↓
POST /api/query
    ↓
FastAPI Endpoint (app.py)
    ↓
RAGSystem.query() (rag_system.py)
    ↓
AIGenerator.generate_response() (ai_generator.py)
    ↓
Claude API Call (with tools)
    ↓
    ├─→ [PATH A: Tool Use]
    │       ↓
    │   ToolManager → CourseSearchTool
    │       ↓
    │   VectorStore.search() → ChromaDB
    │       ↓
    │   Format Results + Store Sources
    │       ↓
    │   Return to Claude API
    │       ↓
    │   Claude synthesizes final answer
    │
    └─→ [PATH B: Direct Answer]
            ↓
        Claude responds from knowledge

    ↓
Response + Sources
    ↓
Update Session History
    ↓
Return JSON to Frontend
    ↓
Display in Chat UI
```
