"""Auto-detect category from page content and URL."""

# Keywords mapped to category slugs — ordered by specificity
CATEGORY_SIGNALS = {
    "ml-system-design": [
        "ml system design", "machine learning", "feature engineering", "model serving",
        "training pipeline", "mlops", "recommendation system", "embeddings model",
        "feature store", "inference", "neural network",
    ],
    "low-level-design": [
        "low-level design", "object-oriented", "class diagram", "design pattern",
        "solid principles", "factory pattern", "singleton", "observer pattern",
        "strategy pattern", "uml", "oop design",
    ],
    "behavioral": [
        "behavioral", "star method", "tell me about a time", "leadership",
        "conflict resolution", "teamwork", "communication skills", "career growth",
        "manager round", "culture fit",
    ],
    "security": [
        "authentication", "authorization", "oauth", "jwt", "encryption",
        "owasp", "xss", "csrf", "sql injection", "threat model", "zero trust",
    ],
    "databases": [
        "database internals", "b-tree", "lsm tree", "transaction isolation",
        "acid properties", "mvcc", "write-ahead log", "query optimizer",
    ],
    "networking": [
        "tcp/ip", "osi model", "dns resolution", "tls handshake", "http/2",
        "bgp", "network layer", "socket programming",
    ],
    "devops": [
        "ci/cd", "kubernetes", "docker", "terraform", "ansible",
        "monitoring", "prometheus", "grafana", "deployment pipeline",
    ],
    "coding": [
        "leetcode", "algorithm", "data structure", "dynamic programming",
        "binary search", "graph traversal", "sorting", "time complexity",
        "big o", "recursion", "sliding window", "two pointer",
    ],
    "system-design": [
        "system design", "distributed system", "scalability", "load balancer",
        "microservice", "api gateway", "message queue", "caching layer",
        "high availability", "cap theorem", "consistent hashing",
        "design a", "design an",
    ],
}


def detect_category(text: str, url: str = "") -> str:
    """Auto-detect the best category from page content and URL.

    Returns the category slug (e.g. 'system-design').
    """
    combined = f"{url} {text}".lower()

    scores = {}
    for slug, keywords in CATEGORY_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[slug] = score

    if not scores:
        return "general"

    return max(scores, key=scores.get)
