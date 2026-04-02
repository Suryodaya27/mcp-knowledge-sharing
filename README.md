# Interview Learning Assistant

Personal interview knowledge base with MCP server for AI-powered learning.

## Architecture

```
Scraper → Postgres + pgvector → MCP Server → LLM (Kiro)
```

- **Scraper**: Fetches pages from HelloInterview (or any structured site), parses into knowledge chunks
- **Database**: Postgres with pgvector for semantic search via embeddings
- **MCP Server**: Exposes tools for search, retrieval, quizzing, and exploration
- **LLM**: Calls MCP tools to teach you interactively

## Setup

### 1. Start Postgres

```bash
cd interview-assistant
docker compose up -d
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Set environment variables

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### 4. Scrape content

```bash
python -m scraper.main
```

### 5. Configure MCP in Kiro

Copy `mcp.json` to `.kiro/settings/mcp.json` and update the `OPENAI_API_KEY`.

## MCP Tools

| Tool | Description |
|------|-------------|
| `search` | Semantic search across all knowledge chunks |
| `random_topic` | Get a random concept for surprise learning |
| `related` | Find concepts related to a given chunk |
| `get_chunk` | Retrieve a specific chunk by ID |
| `categories` | List all knowledge categories |
| `tags` | List all tags with counts |
| `by_tag` | Filter chunks by tag |
| `quiz_me` | Generate a quiz from a random chunk |

## Adding More Content

Add URLs to `scraper/main.py` PAGES list, or create custom parsers for other sites.
