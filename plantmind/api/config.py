"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db")))

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS Origins - supports both localhost and production domains
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:3000,http://localhost:8000"
)
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Add wildcard for development if no specific origins configured
if len(CORS_ORIGINS) == 0:
    CORS_ORIGINS = ["*"]

# LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Graph
GRAPH_BACKEND = os.getenv("GRAPH_BACKEND", "networkx")

# Neo4j (optional)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
