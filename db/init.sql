CREATE EXTENSION IF NOT EXISTS vector;

-- Categories: predefined knowledge areas
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO categories (slug, name, description) VALUES
    ('system-design', 'System Design', 'High-level architecture, distributed systems, scalability patterns'),
    ('coding', 'Coding & Algorithms', 'Data structures, algorithms, leetcode-style problem solving'),
    ('low-level-design', 'Low-Level Design', 'OOP, class design, design patterns, SOLID principles'),
    ('behavioral', 'Behavioral', 'Leadership, conflict resolution, STAR method, soft skills'),
    ('databases', 'Databases', 'SQL, NoSQL, indexing, transactions, replication, sharding'),
    ('networking', 'Networking', 'TCP/IP, HTTP, DNS, CDN, load balancing, protocols'),
    ('devops', 'DevOps & Infrastructure', 'CI/CD, containers, Kubernetes, monitoring, cloud services'),
    ('ml-system-design', 'ML System Design', 'ML pipelines, feature engineering, model serving, MLOps'),
    ('security', 'Security', 'Authentication, authorization, encryption, OWASP, threat modeling'),
    ('general', 'General', 'Miscellaneous interview topics that dont fit other categories')
ON CONFLICT (slug) DO NOTHING;

-- Topics: parent grouping for ordered learning
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    source_url TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Concepts: ordered chunks within a topic
CREATE TABLE IF NOT EXISTS concepts (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    chunk_order INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    difficulty TEXT DEFAULT 'intermediate',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(topic_id, chunk_order)
);

CREATE INDEX IF NOT EXISTS idx_topics_category_id ON topics(category_id);
CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);
CREATE INDEX IF NOT EXISTS idx_concepts_topic_id ON concepts(topic_id);
CREATE INDEX IF NOT EXISTS idx_concepts_tags ON concepts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_concepts_difficulty ON concepts(difficulty);
CREATE INDEX IF NOT EXISTS idx_concepts_embedding ON concepts USING hnsw (embedding vector_cosine_ops);

-- User progress with spaced repetition (SM-2)
CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL UNIQUE REFERENCES topics(id) ON DELETE CASCADE,
    current_level INTEGER NOT NULL DEFAULT 1,
    correct_streak INTEGER NOT NULL DEFAULT 0,
    total_attempts INTEGER NOT NULL DEFAULT 0,
    total_correct INTEGER NOT NULL DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    easiness_factor REAL NOT NULL DEFAULT 2.5,
    interval_days REAL NOT NULL DEFAULT 1.0,
    next_review_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
