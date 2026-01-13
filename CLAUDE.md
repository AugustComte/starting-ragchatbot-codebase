# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Course Materials RAG (Retrieval-Augmented Generation) system built with FastAPI, ChromaDB, and Anthropic's Claude. The system processes educational course documents, stores them as vector embeddings, and provides an AI-powered Q&A interface for querying course content.

## Core Commands

### Running the Application
```bash
# Quick start (creates docs/ directory and starts server)
./run.sh

# Manual start from backend directory
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Development Setup
```bash
# Install dependencies
uv sync

# Set up environment variables
# Create .env file with: ANTHROPIC_API_KEY=your_key_here
```

### Accessing the Application
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Important: Package Manager
**Always use `uv` to run commands and manage dependencies. Do NOT use `pip` directly.** This project uses uv as its package manager for faster, more reliable dependency management.

**Always use `uv run` to execute Python files.** For example:
- `uv run python script.py` instead of `python script.py`
- `uv run pytest` instead of `pytest`

## Architecture

### Data Flow
1. **Document Ingestion** → Course documents (PDF, DOCX, TXT) placed in `docs/` folder
2. **Processing** → `DocumentProcessor` extracts course metadata and chunks content
3. **Vector Storage** → `VectorStore` stores embeddings in ChromaDB (two collections: `course_catalog` for metadata, `course_content` for text chunks)
4. **Query Processing** → `RAGSystem` orchestrates search via tool-based approach where Claude uses `CourseSearchTool` to retrieve relevant content
5. **Response Generation** → `AIGenerator` synthesizes answers using retrieved context

### Component Responsibilities

**RAGSystem** (`rag_system.py`) - Main orchestrator that coordinates all components
- Manages document ingestion workflow
- Routes queries through AI generator with tool access
- Prevents duplicate course processing via title tracking

**VectorStore** (`vector_store.py`) - ChromaDB interface with dual-collection architecture
- `course_catalog`: Stores course-level metadata (title, instructor, lessons) for semantic course name resolution
- `course_content`: Stores chunked lesson content for semantic search
- Provides unified search interface with fuzzy course name matching and lesson filtering

**DocumentProcessor** (`document_processor.py`) - Parses structured course documents
- Expected format: Course metadata (title, link, instructor) in first 3 lines, followed by "Lesson N: Title" markers
- Chunks text using sentence-based splitting with configurable overlap (800 chars, 100 char overlap)
- Adds contextual prefixes to chunks (e.g., "Course X Lesson Y content: ...")

**AIGenerator** (`ai_generator.py`) - Claude API wrapper with tool-calling support
- Uses `claude-sonnet-4-20250514` model with temperature=0, max_tokens=800
- Implements two-phase tool execution: initial request → tool execution → final response
- System prompt emphasizes: one search per query, concise responses, no meta-commentary

**ToolManager/CourseSearchTool** (`search_tools.py`) - Tool-based search interface for Claude
- Claude autonomously decides when to search vs. use general knowledge
- Supports flexible filtering: query-only, course filter, or course+lesson filter
- Tracks sources from searches to display in UI

**SessionManager** (`session_manager.py`) - Lightweight conversation memory
- Maintains last N message pairs (configurable via MAX_HISTORY=2 in config)
- Used for conversational context, not for long-term memory

### Document Format
Course documents must follow this structure:
```
Course Title: [course name]
Course Link: [url]
Course Instructor: [name]

Lesson 0: Introduction
Lesson Link: [url]
[lesson content]

Lesson 1: Next Topic
Lesson Link: [url]
[lesson content]
```

### Configuration
Key settings in `backend/config.py`:
- `CHUNK_SIZE`: 800 (characters per chunk)
- `CHUNK_OVERLAP`: 100 (overlap between chunks)
- `MAX_RESULTS`: 5 (search results returned)
- `MAX_HISTORY`: 2 (conversation exchanges remembered)
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2

### Key Design Patterns

**Duplicate Prevention**: `RAGSystem.add_course_folder()` checks existing course titles before processing to avoid re-indexing

**Smart Course Resolution**: Vector search on course_catalog allows fuzzy matching (e.g., "MCP" finds "MCP Introduction Course")

**Tool-Based Architecture**: Claude autonomously decides when to use search tool vs. answering from general knowledge, enabling a more natural conversational flow

**Stateless API**: FastAPI endpoints are stateless; session state managed in-memory via SessionManager (sessions are non-persistent across server restarts)

## Frontend
Simple HTML/CSS/JS interface (`frontend/` directory) served as static files by FastAPI. Features session-based conversations and source citations from search results.

## Database
ChromaDB stores data in `backend/chroma_db/` directory (persistent on disk). Course titles serve as unique IDs in the catalog collection.
