"""Database queries for the MCP server."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_client import get_conn
from embeddings import get_embedding


def _row_to_dict(row, columns):
    return dict(zip(columns, row))


def search_concepts(query: str, category: str = "", limit: int = 5) -> list[dict]:
    """Semantic search across all concepts."""
    embedding = get_embedding(query)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            where = "WHERE c.embedding IS NOT NULL"
            params = [embedding, embedding]
            if category:
                where += " AND cat.slug = %s"
                params.append(category)
            params.append(limit)
            cur.execute(
                f"""SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                           t.name AS topic, cat.slug AS category, cat.name AS category_name,
                           1 - (c.embedding <=> %s::vector) AS score
                    FROM concepts c
                    JOIN topics t ON c.topic_id = t.id
                    JOIN categories cat ON t.category_id = cat.id
                    {where}
                    ORDER BY c.embedding <=> %s::vector
                    LIMIT %s""",
                params,
            )
            cols = ["id", "title", "summary", "tags", "difficulty", "chunk_order",
                    "topic", "category", "category_name", "score"]
            return [_row_to_dict(row, cols) for row in cur.fetchall()]
    finally:
        conn.close()


def get_topic_concepts(topic_name: str) -> dict | None:
    """Get a topic with all its concepts in order."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.id, t.name, cat.slug AS category, t.source_url, t.description
                   FROM topics t
                   JOIN categories cat ON t.category_id = cat.id
                   WHERE t.name ILIKE %s""",
                (f"%{topic_name}%",),
            )
            topic_row = cur.fetchone()
            if not topic_row:
                return None
            topic = _row_to_dict(topic_row, ["id", "name", "category", "source_url", "description"])

            cur.execute(
                """SELECT id, chunk_order, title, summary, tags, difficulty
                   FROM concepts WHERE topic_id = %s ORDER BY chunk_order""",
                (topic["id"],),
            )
            cols = ["id", "chunk_order", "title", "summary", "tags", "difficulty"]
            topic["concepts"] = [_row_to_dict(row, cols) for row in cur.fetchall()]
            return topic
    finally:
        conn.close()


def get_next_chunk(topic_name: str, current_order: int) -> dict | None:
    """Get the next concept chunk in a topic sequence."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.chunk_order, c.title, c.summary, c.tags, c.difficulty,
                          t.name AS topic
                   FROM concepts c
                   JOIN topics t ON c.topic_id = t.id
                   WHERE t.name ILIKE %s AND c.chunk_order > %s
                   ORDER BY c.chunk_order
                   LIMIT 1""",
                (f"%{topic_name}%", current_order),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(row, ["id", "chunk_order", "title", "summary", "tags", "difficulty", "topic"])
    finally:
        conn.close()


def get_random_topic(category: str = "", difficulty: str = "") -> dict | None:
    """Get a random concept."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            conditions = []
            params = []
            if category:
                conditions.append("cat.slug = %s")
                params.append(category)
            if difficulty:
                conditions.append("c.difficulty = %s")
                params.append(difficulty)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cur.execute(
                f"""SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                           t.name AS topic, cat.slug AS category
                    FROM concepts c
                    JOIN topics t ON c.topic_id = t.id
                    JOIN categories cat ON t.category_id = cat.id
                    {where} ORDER BY RANDOM() LIMIT 1""",
                params,
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(row, ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic", "category"])
    finally:
        conn.close()


def get_related_concepts(concept_id: int, limit: int = 5) -> list[dict]:
    """Find related concepts by vector similarity."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT embedding FROM concepts WHERE id = %s", (concept_id,))
            row = cur.fetchone()
            if not row or row[0] is None:
                return []
            embedding = row[0]
            cur.execute(
                """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                          t.name AS topic, 1 - (c.embedding <=> %s::vector) AS score
                   FROM concepts c JOIN topics t ON c.topic_id = t.id
                   WHERE c.id != %s AND c.embedding IS NOT NULL
                   ORDER BY c.embedding <=> %s::vector
                   LIMIT %s""",
                (embedding, concept_id, embedding, limit),
            )
            cols = ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic", "score"]
            return [_row_to_dict(row, cols) for row in cur.fetchall()]
    finally:
        conn.close()


def get_concept_by_id(concept_id: int) -> dict | None:
    """Get a specific concept by ID."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.chunk_order, c.title, c.summary, c.tags, c.difficulty,
                          t.name AS topic, cat.slug AS category, t.source_url
                   FROM concepts c
                   JOIN topics t ON c.topic_id = t.id
                   JOIN categories cat ON t.category_id = cat.id
                   WHERE c.id = %s""",
                (concept_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(row, ["id", "chunk_order", "title", "summary", "tags", "difficulty", "topic", "category", "source_url"])
    finally:
        conn.close()


def list_topics(category: str = "") -> list[dict]:
    """List all topics with concept counts."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            where = "WHERE cat.slug = %s" if category else ""
            params = [category] if category else []
            cur.execute(
                f"""SELECT t.id, t.name, cat.slug AS category, t.description, COUNT(c.id) AS concept_count
                    FROM topics t
                    JOIN categories cat ON t.category_id = cat.id
                    LEFT JOIN concepts c ON c.topic_id = t.id
                    {where}
                    GROUP BY t.id, cat.slug ORDER BY t.name""",
                params,
            )
            return [_row_to_dict(row, ["id", "name", "category", "description", "concept_count"]) for row in cur.fetchall()]
    finally:
        conn.close()


def list_categories() -> list[dict]:
    """List all available categories."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT cat.slug, cat.name, cat.description, COUNT(t.id) AS topic_count
                   FROM categories cat
                   LEFT JOIN topics t ON t.category_id = cat.id
                   GROUP BY cat.id ORDER BY cat.name"""
            )
            return [_row_to_dict(row, ["slug", "name", "description", "topic_count"]) for row in cur.fetchall()]
    finally:
        conn.close()


def list_tags() -> list[dict]:
    """List all tags with counts."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT tag, COUNT(*) as count
                   FROM concepts, UNNEST(tags) AS tag
                   GROUP BY tag ORDER BY count DESC"""
            )
            return [{"tag": row[0], "count": row[1]} for row in cur.fetchall()]
    finally:
        conn.close()


def get_concepts_by_tag(tag: str, limit: int = 10) -> list[dict]:
    """Get concepts that have a specific tag."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                          t.name AS topic
                   FROM concepts c JOIN topics t ON c.topic_id = t.id
                   WHERE %s = ANY(c.tags)
                   ORDER BY t.name, c.chunk_order
                   LIMIT %s""",
                (tag, limit),
            )
            cols = ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic"]
            return [_row_to_dict(row, cols) for row in cur.fetchall()]
    finally:
        conn.close()


# --- User Progress ---

LEVEL_NAMES = {1: "beginner", 2: "intermediate", 3: "advanced"}
STREAK_TO_LEVEL_UP = 3  # correct answers in a row to level up


def get_user_progress() -> list[dict]:
    """Get progress across all topics."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT t.id, t.name, cat.slug AS category,
                          COALESCE(up.current_level, 1) AS level,
                          COALESCE(up.correct_streak, 0) AS streak,
                          COALESCE(up.total_attempts, 0) AS attempts,
                          COALESCE(up.total_correct, 0) AS correct,
                          up.last_practiced_at,
                          COUNT(c.id) AS total_concepts
                   FROM topics t
                   JOIN categories cat ON t.category_id = cat.id
                   LEFT JOIN user_progress up ON up.topic_id = t.id
                   LEFT JOIN concepts c ON c.topic_id = t.id
                   GROUP BY t.id, t.name, cat.slug, up.current_level, up.correct_streak,
                            up.total_attempts, up.total_correct, up.last_practiced_at
                   ORDER BY t.name"""
            )
            cols = ["topic_id", "topic", "category", "level", "streak", "attempts", "correct", "last_practiced", "total_concepts"]
            rows = [_row_to_dict(row, cols) for row in cur.fetchall()]
            for r in rows:
                r["level_name"] = LEVEL_NAMES.get(r["level"], "advanced")
                r["accuracy"] = round(r["correct"] / r["attempts"] * 100, 1) if r["attempts"] > 0 else 0
                if r["last_practiced"]:
                    r["last_practiced"] = r["last_practiced"].isoformat()
            return rows
    finally:
        conn.close()


def record_answer(topic_id: int, is_correct: bool) -> dict:
    """Record an answer and update progress. Returns updated progress."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Upsert progress
            cur.execute(
                """INSERT INTO user_progress (topic_id, current_level, correct_streak, total_attempts, total_correct, last_practiced_at)
                   VALUES (%s, 1, 0, 0, 0, NOW())
                   ON CONFLICT (topic_id) DO NOTHING""",
                (topic_id,),
            )
            conn.commit()

            if is_correct:
                cur.execute(
                    """UPDATE user_progress
                       SET correct_streak = correct_streak + 1,
                           total_attempts = total_attempts + 1,
                           total_correct = total_correct + 1,
                           last_practiced_at = NOW()
                       WHERE topic_id = %s
                       RETURNING correct_streak, current_level""",
                    (topic_id,),
                )
                row = cur.fetchone()
                streak, level = row[0], row[1]
                # Level up if streak threshold met and not already max
                if streak >= STREAK_TO_LEVEL_UP and level < 3:
                    cur.execute(
                        """UPDATE user_progress
                           SET current_level = current_level + 1, correct_streak = 0
                           WHERE topic_id = %s""",
                        (topic_id,),
                    )
            else:
                cur.execute(
                    """UPDATE user_progress
                       SET correct_streak = 0,
                           total_attempts = total_attempts + 1,
                           last_practiced_at = NOW()
                       WHERE topic_id = %s""",
                    (topic_id,),
                )
            conn.commit()

            # Return updated state
            cur.execute(
                """SELECT up.current_level, up.correct_streak, up.total_attempts, up.total_correct,
                          t.name AS topic
                   FROM user_progress up
                   JOIN topics t ON up.topic_id = t.id
                   WHERE up.topic_id = %s""",
                (topic_id,),
            )
            row = cur.fetchone()
            result = _row_to_dict(row, ["level", "streak", "attempts", "correct", "topic"])
            result["level_name"] = LEVEL_NAMES.get(result["level"], "advanced")
            result["accuracy"] = round(result["correct"] / result["attempts"] * 100, 1) if result["attempts"] > 0 else 0
            result["leveled_up"] = is_correct and result["streak"] == 0 and result["level"] > 1
            return result
    finally:
        conn.close()


def get_quiz_taught_only() -> dict | None:
    """Get a quiz concept only from topics the user has already been taught (has progress)."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Pick a random topic that has user_progress entries
            cur.execute(
                """SELECT t.id, COALESCE(up.current_level, 1) AS level
                   FROM topics t
                   JOIN user_progress up ON up.topic_id = t.id
                   ORDER BY RANDOM()
                   LIMIT 1"""
            )
            row = cur.fetchone()
            if not row:
                return None
            topic_id, level = row[0], row[1]
            level_name = LEVEL_NAMES.get(level, "advanced")

            # Try matching difficulty first, fallback to any concept from that topic
            cur.execute(
                """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                          t.name AS topic, t.id AS topic_id
                   FROM concepts c JOIN topics t ON c.topic_id = t.id
                   WHERE c.topic_id = %s AND c.difficulty = %s
                   ORDER BY RANDOM() LIMIT 1""",
                (topic_id, level_name),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                              t.name AS topic, t.id AS topic_id
                       FROM concepts c JOIN topics t ON c.topic_id = t.id
                       WHERE c.topic_id = %s
                       ORDER BY RANDOM() LIMIT 1""",
                    (topic_id,),
                )
                row = cur.fetchone()
            if not row:
                return None
            result = _row_to_dict(row, ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic", "topic_id"])
            result["user_level"] = level
            result["user_level_name"] = level_name
            return result
    finally:
        conn.close()


def get_quiz_random() -> dict | None:
    """Get a quiz concept from any random topic, regardless of user progress."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                          t.name AS topic, t.id AS topic_id
                   FROM concepts c JOIN topics t ON c.topic_id = t.id
                   ORDER BY RANDOM() LIMIT 1"""
            )
            row = cur.fetchone()
            if not row:
                return None
            result = _row_to_dict(row, ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic", "topic_id"])
            # Check if user has progress on this topic
            cur.execute("SELECT current_level FROM user_progress WHERE topic_id = %s", (result["topic_id"],))
            prow = cur.fetchone()
            result["user_level"] = prow[0] if prow else 1
            result["user_level_name"] = LEVEL_NAMES.get(result["user_level"], "advanced")
            return result
    finally:
        conn.close()


def get_quiz_for_level(topic_id: int = None) -> dict | None:
    """Get a concept matching the user's current level for a topic.
    If no topic_id, picks the least-practiced topic."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if topic_id:
                # Get user's level for this topic
                cur.execute("SELECT current_level FROM user_progress WHERE topic_id = %s", (topic_id,))
                row = cur.fetchone()
                level = row[0] if row else 1
            else:
                # Pick least-practiced topic
                cur.execute(
                    """SELECT t.id, COALESCE(up.current_level, 1) AS level
                       FROM topics t
                       LEFT JOIN user_progress up ON up.topic_id = t.id
                       ORDER BY up.last_practiced_at ASC NULLS FIRST, RANDOM()
                       LIMIT 1"""
                )
                row = cur.fetchone()
                if not row:
                    return None
                topic_id, level = row[0], row[1]

            level_name = LEVEL_NAMES.get(level, "advanced")
            # Try to find a concept at the user's level, fallback to any
            cur.execute(
                """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                          t.name AS topic, t.id AS topic_id
                   FROM concepts c JOIN topics t ON c.topic_id = t.id
                   WHERE c.topic_id = %s AND c.difficulty = %s
                   ORDER BY RANDOM() LIMIT 1""",
                (topic_id, level_name),
            )
            row = cur.fetchone()
            if not row:
                # Fallback: any concept from this topic
                cur.execute(
                    """SELECT c.id, c.title, c.summary, c.tags, c.difficulty, c.chunk_order,
                              t.name AS topic, t.id AS topic_id
                       FROM concepts c JOIN topics t ON c.topic_id = t.id
                       WHERE c.topic_id = %s
                       ORDER BY RANDOM() LIMIT 1""",
                    (topic_id,),
                )
                row = cur.fetchone()
            if not row:
                return None
            result = _row_to_dict(row, ["id", "title", "summary", "tags", "difficulty", "chunk_order", "topic", "topic_id"])
            result["user_level"] = level
            result["user_level_name"] = level_name
            return result
    finally:
        conn.close()
