"""Database client for topics and concepts."""
import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from config import DATABASE_URL


def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    return conn


def get_category_id(slug: str) -> int:
    """Get category ID by slug, fallback to 'general'."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE slug = %s", (slug,))
            row = cur.fetchone()
            if row:
                return row[0]
            # Fallback to general
            cur.execute("SELECT id FROM categories WHERE slug = 'general'")
            return cur.fetchone()[0]
    finally:
        conn.close()


def upsert_topic(name: str, category_slug: str, source_url: str = None, description: str = None) -> int:
    """Insert or get a topic, return its ID."""
    category_id = get_category_id(category_slug)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO topics (name, category_id, source_url, description)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (name) DO UPDATE SET
                       source_url = COALESCE(EXCLUDED.source_url, topics.source_url),
                       description = COALESCE(EXCLUDED.description, topics.description)
                   RETURNING id""",
                (name, category_id, source_url, description),
            )
            conn.commit()
            return cur.fetchone()[0]
    finally:
        conn.close()


def insert_concept(topic_id: int, chunk_order: int, title: str, summary: str,
                   tags: list[str], difficulty: str, embedding: list[float] | None = None) -> int | None:
    """Insert a single concept chunk."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO concepts (topic_id, chunk_order, title, summary, tags, difficulty, embedding)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (topic_id, chunk_order) DO UPDATE SET
                       title = EXCLUDED.title,
                       summary = EXCLUDED.summary,
                       tags = EXCLUDED.tags,
                       difficulty = EXCLUDED.difficulty,
                       embedding = EXCLUDED.embedding
                   RETURNING id""",
                (topic_id, chunk_order, title, summary, tags, difficulty, embedding),
            )
            conn.commit()
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()
