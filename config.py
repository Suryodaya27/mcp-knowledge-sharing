import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://interview:interview_pass@localhost:5433/interview_kb")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIM = 768
