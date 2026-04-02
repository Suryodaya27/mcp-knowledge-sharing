"""Tag extraction and difficulty inference for knowledge chunks."""
import re

# Common interview/system-design keywords to detect as tags
TAG_KEYWORDS = {
    "caching": ["cache", "caching", "redis", "memcached", "cdn"],
    "database": ["database", "sql", "nosql", "postgres", "mysql", "dynamodb", "cassandra", "mongodb"],
    "scaling": ["scaling", "horizontal", "vertical", "sharding", "partitioning", "replication"],
    "messaging": ["queue", "kafka", "rabbitmq", "pub/sub", "pubsub", "event-driven", "message broker"],
    "api-design": ["api", "rest", "graphql", "grpc", "endpoint", "webhook"],
    "load-balancing": ["load balancer", "load balancing", "round robin", "consistent hashing"],
    "consistency": ["consistency", "cap theorem", "eventual consistency", "strong consistency", "consensus"],
    "availability": ["availability", "failover", "redundancy", "fault tolerance", "disaster recovery"],
    "networking": ["dns", "tcp", "http", "websocket", "cdn", "proxy", "reverse proxy"],
    "storage": ["blob", "s3", "object storage", "file system", "block storage"],
    "search": ["search", "elasticsearch", "full-text", "indexing", "inverted index"],
    "rate-limiting": ["rate limit", "throttling", "token bucket", "leaky bucket"],
    "monitoring": ["monitoring", "logging", "metrics", "alerting", "observability", "tracing"],
    "microservices": ["microservice", "service mesh", "api gateway", "service discovery"],
    "real-time": ["real-time", "realtime", "websocket", "sse", "long polling", "streaming"],
    "security": ["authentication", "authorization", "oauth", "jwt", "encryption", "tls"],
}

DIFFICULTY_SIGNALS = {
    "advanced": ["trade-off", "at scale", "distributed", "consensus", "linearizable", "vector clock",
                 "crdt", "raft", "paxos", "gossip protocol", "bloom filter"],
    "beginner": ["what is", "introduction", "getting started", "basics", "overview", "simple"],
}


def extract_tags(content: str, category: str) -> list[str]:
    """Extract relevant tags from content text."""
    content_lower = content.lower()
    tags = [category]
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)
    return list(set(tags))


def infer_difficulty(content: str) -> str:
    """Infer difficulty level from content."""
    content_lower = content.lower()
    for level, signals in DIFFICULTY_SIGNALS.items():
        if any(s in content_lower for s in signals):
            return level
    return "intermediate"
