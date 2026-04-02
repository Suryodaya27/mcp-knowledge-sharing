"""Parse HelloInterview-style pages into topics and concept chunks."""
from bs4 import BeautifulSoup
from scraper.tags import extract_tags, infer_difficulty


def parse_page(html: str, source_url: str, category: str = "system-design") -> dict:
    """Parse an HTML page into a topic with ordered concept chunks.

    Returns:
        {
            "topic_name": str,
            "category": str,
            "source_url": str,
            "description": str,
            "chunks": [
                {"chunk_order": 1, "title": str, "summary": str, "tags": [], "difficulty": str},
                ...
            ]
        }
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup.find_all(["nav", "footer", "script", "style", "header"]):
        tag.decompose()

    # Get page/topic title
    page_title = soup.find("h1")
    topic_name = page_title.get_text(strip=True) if page_title else "Untitled"

    # Get first paragraph as topic description
    first_p = soup.find("p")
    description = first_p.get_text(strip=True)[:500] if first_p else ""

    chunks = []
    current_heading = topic_name
    current_content_parts = []
    chunk_order = 0

    def flush_chunk():
        nonlocal chunk_order
        if current_content_parts:
            content = "\n".join(current_content_parts).strip()
            if len(content) > 50:
                chunk_order += 1
                chunks.append({
                    "chunk_order": chunk_order,
                    "title": current_heading,
                    "summary": content,
                    "tags": extract_tags(content, category),
                    "difficulty": infer_difficulty(content),
                })

    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return {"topic_name": topic_name, "category": category,
                "source_url": source_url, "description": description, "chunks": []}

    for element in main.find_all(["h2", "h3", "p", "ul", "ol", "pre", "blockquote", "table"]):
        tag_name = element.name

        if tag_name in ("h2", "h3"):
            flush_chunk()
            current_heading = element.get_text(strip=True)
            current_content_parts = []
        elif tag_name in ("p", "blockquote"):
            text = element.get_text(strip=True)
            if text:
                current_content_parts.append(text)
        elif tag_name in ("ul", "ol"):
            for li in element.find_all("li"):
                current_content_parts.append(f"- {li.get_text(strip=True)}")
        elif tag_name == "pre":
            current_content_parts.append(f"```\n{element.get_text()}\n```")
        elif tag_name == "table":
            current_content_parts.append(element.get_text(separator=" | ", strip=True))

    flush_chunk()

    return {
        "topic_name": topic_name,
        "category": category,
        "source_url": source_url,
        "description": description,
        "chunks": chunks,
    }
