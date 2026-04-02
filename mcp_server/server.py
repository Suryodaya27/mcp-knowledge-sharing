"""MCP Server exposing interview knowledge base tools."""
import json
from mcp.server.fastmcp import FastMCP
from mcp_server.queries import (
    search_concepts,
    get_topic_concepts,
    get_next_chunk,
    get_random_topic,
    get_related_concepts,
    get_concept_by_id,
    list_topics,
    list_categories,
    list_tags,
    get_concepts_by_tag,
    get_user_progress,
    record_answer,
    get_quiz_for_level,
    get_quiz_taught_only,
    get_quiz_random,
)

mcp = FastMCP(
    "Interview Knowledge Base",
    instructions="Search and retrieve structured interview concepts for system design, coding, and more.",
)


@mcp.tool()
def search(query: str, category: str = "", limit: int = 5) -> str:
    """Semantic search across all concepts in the knowledge base.

    Args:
        query: Natural language query (e.g. "how does consistent hashing work")
        category: Optional category filter (e.g. "system-design")
        limit: Max results (default 5)
    """
    results = search_concepts(query, category=category, limit=limit)
    return json.dumps(results, indent=2)


@mcp.tool()
def topic(topic_name: str) -> str:
    """Get a full topic with all its concepts in sequential order.

    Args:
        topic_name: Topic name or partial match (e.g. "Caching", "Delivery")
    """
    result = get_topic_concepts(topic_name)
    return json.dumps(result, indent=2) if result else '{"error": "Topic not found"}'


@mcp.tool()
def next_chunk(topic_name: str, current_order: int) -> str:
    """Get the next concept in a topic sequence (for sequential learning).

    Args:
        topic_name: The topic name
        current_order: The chunk_order of the current concept
    """
    result = get_next_chunk(topic_name, current_order)
    return json.dumps(result, indent=2) if result else '{"info": "No more chunks — topic complete!"}'


@mcp.tool()
def random_topic(category: str = "", difficulty: str = "") -> str:
    """Get a random concept for surprise learning or quiz generation.

    Args:
        category: Optional filter (e.g. "system-design")
        difficulty: Optional filter (e.g. "beginner", "intermediate", "advanced")
    """
    result = get_random_topic(category=category, difficulty=difficulty)
    return json.dumps(result, indent=2) if result else '{"error": "No concepts found"}'


@mcp.tool()
def related(concept_id: int, limit: int = 5) -> str:
    """Find concepts related to a given one (by semantic similarity).

    Args:
        concept_id: The ID of the reference concept
        limit: Max related results
    """
    results = get_related_concepts(concept_id, limit=limit)
    return json.dumps(results, indent=2)


@mcp.tool()
def get_concept(concept_id: int) -> str:
    """Retrieve a specific concept by its ID.

    Args:
        concept_id: The unique concept ID
    """
    result = get_concept_by_id(concept_id)
    return json.dumps(result, indent=2) if result else '{"error": "Concept not found"}'


@mcp.tool()
def topics(category: str = "") -> str:
    """List all topics with concept counts (table of contents).

    Args:
        category: Optional category filter
    """
    return json.dumps(list_topics(category), indent=2)


@mcp.tool()
def tags() -> str:
    """List all tags used across concepts with counts."""
    return json.dumps(list_tags(), indent=2)


@mcp.tool()
def categories() -> str:
    """List all available knowledge categories with topic counts."""
    return json.dumps(list_categories(), indent=2)


@mcp.tool()
def by_tag(tag: str, limit: int = 10) -> str:
    """Get concepts filtered by a specific tag.

    Args:
        tag: Tag to filter by (e.g. "caching", "database")
        limit: Max results
    """
    return json.dumps(get_concepts_by_tag(tag, limit=limit), indent=2)


@mcp.tool()
def quiz_me(topic_name: str = "") -> str:
    """Generate a short quiz question matched to the user's current level for a topic.

    Picks the least-practiced topic if none specified. Questions get harder as the user levels up.

    Args:
        topic_name: Optional topic name to quiz on. If empty, picks least-practiced topic.
    """
    # Resolve topic_id from name if given
    topic_id = None
    if topic_name:
        from mcp_server.queries import get_topic_concepts
        t = get_topic_concepts(topic_name)
        if t:
            topic_id = t["id"]

    result = get_quiz_for_level(topic_id=topic_id)
    if not result:
        return '{"error": "No concepts available"}'
    return json.dumps({
        "instruction": f"User is at level {result['user_level_name']}. Generate a SHORT, focused question (1-2 sentences). For beginner: ask 'what is X?' or 'name one benefit of X'. For intermediate: ask 'how does X work?' or 'compare X vs Y'. For advanced: ask about tradeoffs, edge cases, or design decisions. Keep it concise.",
        "concept": result,
    }, indent=2)


@mcp.tool()
def quiz_taught(topic_name: str = "") -> str:
    """Quiz the user only on topics they have already learned (have progress on).

    Great for reinforcement. Only picks from topics with existing user_progress entries.

    Args:
        topic_name: Optional topic name to narrow down. If empty, picks a random taught topic.
    """
    if topic_name:
        t = get_topic_concepts(topic_name)
        if t:
            result = get_quiz_for_level(topic_id=t["id"])
            if result:
                return json.dumps({
                    "instruction": f"User is at level {result['user_level_name']}. Generate a SHORT, focused question (1-2 sentences). For beginner: ask 'what is X?' or 'name one benefit of X'. For intermediate: ask 'how does X work?' or 'compare X vs Y'. For advanced: ask about tradeoffs, edge cases, or design decisions. Keep it concise.",
                    "concept": result,
                }, indent=2)
    result = get_quiz_taught_only()
    if not result:
        return '{"error": "No taught topics found yet. Use teach_me first to learn some concepts!"}'
    return json.dumps({
        "instruction": f"User is at level {result['user_level_name']}. Generate a SHORT, focused question (1-2 sentences). For beginner: ask 'what is X?' or 'name one benefit of X'. For intermediate: ask 'how does X work?' or 'compare X vs Y'. For advanced: ask about tradeoffs, edge cases, or design decisions. Keep it concise.",
        "concept": result,
    }, indent=2)


@mcp.tool()
def quiz_random() -> str:
    """Quiz the user on a completely random topic from the knowledge base.

    Picks any concept at random regardless of whether the user has studied it before.
    Good for discovering new topics and testing breadth of knowledge.
    """
    result = get_quiz_random()
    if not result:
        return '{"error": "No concepts available in the knowledge base"}'
    return json.dumps({
        "instruction": f"User is at level {result['user_level_name']}. Generate a SHORT, focused question (1-2 sentences). For beginner: ask 'what is X?' or 'name one benefit of X'. For intermediate: ask 'how does X work?' or 'compare X vs Y'. For advanced: ask about tradeoffs, edge cases, or design decisions. Keep it concise.",
        "concept": result,
    }, indent=2)


@mcp.tool()
def answer_result(topic_id: int, is_correct: bool) -> str:
    """Record whether the user answered correctly and update their progress.

    Levels up after 3 correct answers in a row. Resets streak on wrong answer.

    Args:
        topic_id: The topic ID the question was about
        is_correct: Whether the user answered correctly
    """
    result = record_answer(topic_id, is_correct)
    return json.dumps(result, indent=2)


@mcp.tool()
def my_progress() -> str:
    """Show the user's learning progress across all topics.

    Returns level, accuracy, streak, and last practiced time per topic.
    """
    results = get_user_progress()
    return json.dumps(results, indent=2)


@mcp.tool()
def teach_me(topic_name: str = "") -> str:
    """Explain a random concept from the knowledge base.

    If topic_name is given, picks from that topic. Otherwise picks any random concept.

    Args:
        topic_name: Optional topic to learn about
    """
    if topic_name:
        t = get_topic_concepts(topic_name)
        if t and t.get("concepts"):
            import random
            concept = random.choice(t["concepts"])
            concept["topic"] = t["name"]
            return json.dumps({
                "instruction": "Explain this concept clearly and concisely to the user. Use simple language, give a real-world analogy if helpful, and end with a key takeaway.",
                "concept": concept,
            }, indent=2)
    # Random concept
    result = get_random_topic()
    if not result:
        return '{"error": "No concepts in the knowledge base yet"}'
    return json.dumps({
        "instruction": "Explain this concept clearly and concisely to the user. Use simple language, give a real-world analogy if helpful, and end with a key takeaway.",
        "concept": result,
    }, indent=2)


@mcp.tool()
def scrape(url: str) -> str:
    """Scrape a URL and store its content as knowledge chunks in the database.

    Fetches the page, auto-detects category, splits into ordered concepts,
    generates embeddings, and stores everything.

    Args:
        url: The URL to scrape (e.g. "https://www.hellointerview.com/learn/system-design/problem-breakdowns/uber")
    """
    from mcp_server.scrape_tool import scrape_url
    try:
        result = scrape_url(url)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "url": url}, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
