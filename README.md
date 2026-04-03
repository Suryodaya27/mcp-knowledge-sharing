# Interview Knowledge Base — Adaptive Learning MCP Server

An AI-powered interview prep system that scrapes technical content, stores it as structured knowledge chunks with vector embeddings, and serves it through an MCP (Model Context Protocol) server with **SM-2 spaced repetition** for optimized learning.

Built with Python, PostgreSQL + pgvector, Ollama embeddings, and FastMCP.

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Web Pages   │────▶│   Scraper    │────▶│  PostgreSQL + pgvector │
│ (any URL)    │     │  + Ollama    │     │  topics / concepts     │
└─────────────┘     └──────────────┘     └──────────┬────────────┘
                                                     │
                                          ┌──────────▼────────────┐
                                          │    MCP Server          │
                                          │  (18 tools)            │
                                          │  search, quiz, teach,  │
                                          │  spaced repetition     │
                                          └──────────┬────────────┘
                                                     │
                                          ┌──────────▼────────────┐
                                          │  AI Assistant (Kiro,   │
                                          │  Claude, etc.)         │
                                          └───────────────────────┘
```

1. **Scrape** any webpage — the parser extracts content, auto-detects the category, splits it into ordered concept chunks, generates vector embeddings via Ollama, and stores everything in PostgreSQL.
2. **Learn** through the MCP server — your AI assistant can search concepts semantically, teach you topics, quiz you at your level, and track your progress.
3. **Spaced repetition** (SM-2 algorithm) schedules reviews right before you'd forget, so quiz tools prioritize topics that are due — not just random picks.

## Prerequisites

- **Python 3.11+**
- **Docker** (for PostgreSQL with pgvector)
- **Ollama** running locally with an embedding model

### Install Ollama & pull the embedding model

```bash
# Install Ollama: https://ollama.com/download
# Then pull the embedding model:
ollama pull nomic-embed-text
```

Verify it's running:
```bash
curl http://localhost:11434/api/embeddings -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

## Setup

### 1. Start PostgreSQL

```bash
cd interview-assistant
docker compose up -d
```

This starts a pgvector-enabled PostgreSQL on port **5433** and runs `db/init.sql` to create the schema.

### 2. Install Python dependencies

```bash
cd interview-assistant
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure environment (optional)

Copy and edit if your setup differs from defaults:

```bash
cp .env.example .env
```

Default values:
| Variable | Default |
|---|---|
| `DATABASE_URL` | `postgresql://interview:interview_pass@localhost:5433/interview_kb` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `EMBEDDING_MODEL` | `nomic-embed-text` |

## Ingesting Content

### Scrape the curated pages

```bash
python -m scraper.main
```

This fetches a curated set of HelloInterview system design pages and stores them as structured knowledge.

### Scrape any URL via the MCP server

Once the server is connected to your AI assistant, just ask:

> "Scrape https://example.com/some-article"

The `scrape` tool fetches the page, auto-detects the category, parses it into chunks, generates embeddings, and stores everything.

## Running the MCP Server

### Standalone (for testing)

```bash
python -m mcp_server.server
```

### Connect to an AI assistant

Add this to your MCP configuration (e.g. `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "interview-kb": {
      "command": "/path/to/interview-assistant/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/interview-assistant",
      "env": {
        "DATABASE_URL": "postgresql://interview:interview_pass@localhost:5433/interview_kb"
      }
    }
  }
}
```

Replace `/path/to/interview-assistant` with the actual path on your machine.

## MCP Tools Reference

### Learning & Teaching
| Tool | Description |
|---|---|
| `teach_me` | Explains a random concept (optionally from a specific topic) |
| `search` | Semantic search across all concepts using vector similarity |
| `topic` | Get a full topic with all concepts in order |
| `next_chunk` | Get the next concept in a topic sequence |
| `random_topic` | Get a random concept, optionally filtered by category/difficulty |
| `related` | Find semantically related concepts |
| `get_concept` | Retrieve a specific concept by ID |

### Quizzing (with Spaced Repetition)
| Tool | Description |
|---|---|
| `quiz_me` | Quiz on the topic most due for review (SM-2). Optionally specify a topic. |
| `quiz_taught` | Quiz only on topics you've already learned |
| `quiz_random` | Quiz on any random topic regardless of progress |
| `answer_result` | Record your answer — updates progress, streak, level, and SM-2 schedule |

### Progress & Discovery
| Tool | Description |
|---|---|
| `my_progress` | View level, accuracy, streak, and next review date per topic |
| `topics` | List all topics with concept counts |
| `categories` | List all knowledge categories |
| `tags` | List all tags with counts |
| `by_tag` | Get concepts filtered by tag |

### Content Ingestion
| Tool | Description |
|---|---|
| `scrape` | Scrape any URL and auto-store as structured knowledge chunks |

## Spaced Repetition (SM-2)

The system uses the SM-2 algorithm (same as Anki/SuperMemo) to schedule reviews:

- **Correct answers** increase the review interval exponentially: 1 day → 6 days → 16 days → 45 days → ...
- **Wrong answers** reset the interval to 1 day and decrease the easiness factor
- The `easiness_factor` (starting at 2.5) adapts per topic based on your performance
- `quiz_me` and `quiz_taught` automatically prioritize topics where `next_review_at` has passed

This means the system surfaces concepts right before you'd forget them, instead of quizzing randomly.

## Example Session

```
You:    teach me
Kiro:   [explains a concept about consistent hashing]

You:    quiz me
Kiro:   What is the main benefit of consistent hashing over simple modular hashing?

You:    [answers]
Kiro:   Correct! Next review for this topic in 6 days. Streak: 2/3 to level up.

You:    scrape https://www.hellointerview.com/learn/system-design/problem-breakdowns/tinder
Kiro:   Scraped "Tinder" — stored 12 concepts under system-design.

You:    quiz taught
Kiro:   [quizzes you on a topic you've already studied, prioritizing ones due for review]
```

## Project Structure

```
interview-assistant/
├── config.py                 # Environment config (DB, Ollama)
├── db_client.py              # PostgreSQL connection + CRUD helpers
├── embeddings.py             # Ollama embedding generation
├── docker-compose.yml        # PostgreSQL + pgvector container
├── pyproject.toml            # Python project config + dependencies
├── db/
│   └── init.sql              # Database schema (tables, indexes, pgvector)
├── scraper/
│   ├── main.py               # CLI scraper for batch ingestion
│   ├── parser.py             # HTML → structured concept chunks
│   ├── categorizer.py        # Auto-detect content category
│   └── tags.py               # Tag extraction + difficulty inference
└── mcp_server/
    ├── server.py             # FastMCP server with all tool definitions
    ├── queries.py            # Database queries + SM-2 spaced repetition logic
    └── scrape_tool.py        # URL scraping tool for the MCP server
```

## Tech Stack

- **Python 3.11+** — core language
- **FastMCP** — Model Context Protocol server framework
- **PostgreSQL 16 + pgvector** — vector storage and semantic search
- **Ollama + nomic-embed-text** — local embedding generation (768-dim vectors)
- **BeautifulSoup4** — HTML parsing for the scraper
- **httpx** — async-capable HTTP client
- **Rich** — CLI output formatting
