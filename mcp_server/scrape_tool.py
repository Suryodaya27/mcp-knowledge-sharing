"""Scrape tool for the MCP server — fetches a URL and stores knowledge chunks."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from scraper.parser import parse_page
from scraper.categorizer import detect_category
from db_client import upsert_topic, insert_concept
from embeddings import get_embedding


def scrape_url(url: str) -> dict:
    """Scrape a single URL and store its content as knowledge chunks.

    Returns summary of what was stored.
    """
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()

    category = detect_category(resp.text, url)
    parsed = parse_page(resp.text, source_url=url, category=category)

    if not parsed["chunks"]:
        return {"url": url, "status": "no_chunks", "topic": None, "concepts_stored": 0}

    topic_id = upsert_topic(
        name=parsed["topic_name"],
        category_slug=parsed["category"],
        source_url=parsed["source_url"],
        description=parsed["description"],
    )

    for chunk in parsed["chunks"]:
        embed_text = f"{parsed['topic_name']} - {chunk['title']}: {chunk['summary']}"
        embedding = get_embedding(embed_text)
        insert_concept(
            topic_id=topic_id,
            chunk_order=chunk["chunk_order"],
            title=chunk["title"],
            summary=chunk["summary"],
            tags=chunk["tags"],
            difficulty=chunk["difficulty"],
            embedding=embedding,
        )

    return {
        "url": url,
        "status": "success",
        "topic": parsed["topic_name"],
        "category": parsed["category"],
        "concepts_stored": len(parsed["chunks"]),
    }
