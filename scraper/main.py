"""Main scraper: fetches pages and stores topics + concept chunks."""
import httpx
from rich.console import Console
from rich.progress import track

from scraper.parser import parse_page
from scraper.categorizer import detect_category
from db_client import upsert_topic, insert_concept
from embeddings import get_embedding

console = Console()

# Curated list of HelloInterview system design pages
PAGES = [
    "https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery",
    "https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts",
    "https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies",
    "https://www.hellointerview.com/learn/system-design/in-a-hurry/patterns",
    "https://www.hellointerview.com/learn/system-design/in-a-hurry/how-to-prepare",
    "https://www.hellointerview.com/learn/low-level-design/in-a-hurry/delivery",
    "https://www.hellointerview.com/learn/ml-system-design/in-a-hurry/delivery",
]


def scrape_and_store(urls: list[str] | None = None):
    """Scrape pages and store as topics with ordered concept chunks.
    
    Category is auto-detected from page content — no need to specify it.
    """
    urls = urls or PAGES
    total_concepts = 0

    console.print(f"[bold green]Scraping {len(urls)} pages...[/]")

    for url in track(urls, description="Fetching pages"):
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()

            # Auto-detect category from content + URL
            category = detect_category(resp.text, url)

            parsed = parse_page(resp.text, source_url=url, category=category)

            if not parsed["chunks"]:
                console.print(f"  [yellow]{url}[/] → no chunks extracted")
                continue

            # Create/get topic
            topic_id = upsert_topic(
                name=parsed["topic_name"],
                category_slug=parsed["category"],
                source_url=parsed["source_url"],
                description=parsed["description"],
            )

            # Insert each chunk with embedding
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

            total_concepts += len(parsed["chunks"])
            console.print(f"  [dim]{url}[/] → [{category}] '{parsed['topic_name']}' with {len(parsed['chunks'])} concepts")

        except Exception as e:
            console.print(f"  [red]Error: {url} — {e}[/]")

    console.print(f"\n[bold green]Done! Stored {total_concepts} concepts.[/]")


def main():
    scrape_and_store()


if __name__ == "__main__":
    main()
