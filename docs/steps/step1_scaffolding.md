# Step 1 — Project Scaffolding & Environment Setup

## Objective
Create a clean, runnable monorepo skeleton with FastAPI backend, React frontend, NetworkX graph, and ChromaDB vector store — all booting and connecting before any feature code is written.

---

## 1.1 Create Directory Structure

Create the following directory tree under `d:\hackathon projects\PlantMind ET\`:

```
plantmind/
├── ingestion/
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── ocr_processor.py
│   ├── pid_detector.py
│   ├── csv_parser.py
│   ├── ner_extractor.py
│   └── pipeline.py
├── graph/
│   ├── __init__.py
│   ├── schema.py
│   ├── graph_store.py
│   └── queries.py
├── agents/
│   ├── __init__.py
│   ├── rag_copilot.py
│   ├── rca_agent.py
│   ├── compliance_agent.py
│   └── lessons_learned_agent.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── query.py
│   │   ├── ingest.py
│   │   ├── agents.py
│   │   └── graph.py
│   └── config.py
├── web/
│   └── (React app — created via Vite in step 1.5)
├── data/
│   └── sample_docs/
│       ├── maintenance/
│       ├── safety_procedures/
│       ├── inspection_forms/
│       ├── pid_drawings/
│       └── regulatory/
├── docs/
│   └── steps/
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_graph.py
│   └── test_agents.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Commands to create directories:
```bash
cd "d:\hackathon projects\PlantMind ET"

# Backend directories
mkdir -p plantmind/ingestion
mkdir -p plantmind/graph
mkdir -p plantmind/agents
mkdir -p plantmind/api/routes
mkdir -p plantmind/data/sample_docs/maintenance
mkdir -p plantmind/data/sample_docs/safety_procedures
mkdir -p plantmind/data/sample_docs/inspection_forms
mkdir -p plantmind/data/sample_docs/pid_drawings
mkdir -p plantmind/data/sample_docs/regulatory
mkdir -p plantmind/tests
```

---

## 1.2 Create `requirements.txt`

**File:** `plantmind/requirements.txt`

```txt
# Core API
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-dotenv==1.0.1
pydantic==2.9.0

# Document Processing
PyMuPDF==1.24.0
pytesseract==0.3.13
Pillow==10.4.0
python-multipart==0.0.9

# Knowledge Graph
networkx==3.3

# Vector Database
chromadb==0.5.0

# LLM & Embeddings
google-generativeai==0.8.0
langchain==0.3.0
langchain-google-genai==2.0.0
langchain-community==0.3.0

# Data Processing
pandas==2.2.0
numpy==1.26.0

# Utilities
httpx==0.27.0
pyyaml==6.0.1

# Testing
pytest==8.3.0
pytest-asyncio==0.24.0
```

---

## 1.3 Create `.env.example`

**File:** `plantmind/.env.example`

```env
# Google Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Server Config
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_db

# Graph Config (networkx = in-memory, neo4j = requires Neo4j server)
GRAPH_BACKEND=networkx

# Optional: Neo4j (only if GRAPH_BACKEND=neo4j)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Logging
LOG_LEVEL=INFO
```

---

## 1.4 Create Backend Boilerplate

### 1.4.1 `plantmind/api/config.py`

```python
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
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

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
```

### 1.4.2 `plantmind/api/main.py`

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import CORS_ORIGINS, API_HOST, API_PORT
from api.routes import query, ingest, agents, graph

app = FastAPI(
    title="PlantMind API",
    description="Unified Asset & Operations Brain — AI platform for industrial knowledge management",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
app.include_router(graph.router, prefix="/api/v1", tags=["Graph"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "PlantMind API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint that verifies all subsystems."""
    from graph.graph_store import get_graph_store
    from chromadb import Client as ChromaClient
    
    checks = {
        "api": "healthy",
        "graph": "unknown",
        "vector_db": "unknown",
    }
    
    try:
        store = get_graph_store()
        node_count = store.graph.number_of_nodes()
        checks["graph"] = f"healthy ({node_count} nodes)"
    except Exception as e:
        checks["graph"] = f"error: {str(e)}"
    
    try:
        import chromadb
        client = chromadb.Client()
        checks["vector_db"] = "healthy"
    except Exception as e:
        checks["vector_db"] = f"error: {str(e)}"
    
    overall = "healthy" if all("healthy" in str(v) for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=int(API_PORT), reload=True)
```

### 1.4.3 Route stubs — create all four route files

**File:** `plantmind/api/routes/__init__.py`
```python
"""API route modules."""
```

**File:** `plantmind/api/routes/query.py`
```python
"""Query endpoint — RAG copilot chat interface."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    agent_type: str = "copilot"  # copilot, rca, compliance, lessons_learned


class Citation(BaseModel):
    doc_id: str
    doc_title: str
    chunk_text: str
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    citations: list[Citation]
    graph_entities: list[dict]
    session_id: str


@router.post("/query", response_model=QueryResponse)
async def query_copilot(request: QueryRequest):
    """Send a natural language question to the RAG copilot."""
    # Stub — will be implemented in Step 5
    return QueryResponse(
        answer="PlantMind is initializing. Query system will be available after Step 5.",
        confidence=0.0,
        citations=[],
        graph_entities=[],
        session_id=request.session_id or "stub-session",
    )
```

**File:** `plantmind/api/routes/ingest.py`
```python
"""Document ingestion endpoints."""

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class IngestResponse(BaseModel):
    doc_id: str
    doc_type: str
    entities_extracted: int
    relationships_extracted: int
    chunks_created: int
    status: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = None,
):
    """Ingest a single document into the knowledge graph."""
    # Stub — will be implemented in Step 3
    return IngestResponse(
        doc_id="stub",
        doc_type=doc_type or "unknown",
        entities_extracted=0,
        relationships_extracted=0,
        chunks_created=0,
        status="stub — not yet implemented",
    )


@router.post("/ingest/batch")
async def ingest_batch():
    """Ingest all documents in the sample_docs directory."""
    # Stub — will be implemented in Step 3
    return {"status": "stub", "documents_processed": 0}
```

**File:** `plantmind/api/routes/agents.py`
```python
"""Specialist agent endpoints (RCA, Compliance, Lessons-Learned)."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class RCARequest(BaseModel):
    equipment_tag: str


class ComplianceRequest(BaseModel):
    regulation_id: Optional[str] = None


class LessonsRequest(BaseModel):
    equipment_type: Optional[str] = None
    failure_mode: Optional[str] = None


@router.post("/agents/rca")
async def run_rca_agent(request: RCARequest):
    """Run root cause analysis for an equipment tag."""
    # Stub — will be implemented in Step 6
    return {"status": "stub", "equipment_tag": request.equipment_tag}


@router.post("/agents/compliance")
async def run_compliance_agent(request: ComplianceRequest):
    """Run compliance gap analysis."""
    # Stub — will be implemented in Step 6
    return {"status": "stub"}


@router.post("/agents/lessons")
async def run_lessons_agent(request: LessonsRequest):
    """Run lessons-learned pattern detection."""
    # Stub — will be implemented in Step 6
    return {"status": "stub"}
```

**File:** `plantmind/api/routes/graph.py`
```python
"""Knowledge graph query and visualization endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/graph/nodes")
async def get_graph_nodes(node_type: str = None, limit: int = 100):
    """Get nodes from the knowledge graph, optionally filtered by type."""
    # Stub — will be implemented in Step 4
    return {"nodes": [], "total": 0}


@router.get("/graph/relationships")
async def get_graph_relationships(source_id: str = None, limit: int = 100):
    """Get relationships from the knowledge graph."""
    # Stub — will be implemented in Step 4
    return {"relationships": [], "total": 0}


@router.get("/graph/export")
async def export_graph_for_viz():
    """Export the full graph in a format suitable for force-directed visualization."""
    # Stub — will be implemented in Step 4
    return {"nodes": [], "edges": []}
```

### 1.4.4 Graph store boilerplate

**File:** `plantmind/graph/__init__.py`
```python
"""Knowledge graph module."""
```

**File:** `plantmind/graph/graph_store.py`
```python
"""Graph store abstraction — NetworkX implementation."""

import networkx as nx
from typing import Optional

_graph_store: Optional["GraphStore"] = None


class GraphStore:
    """Wrapper around NetworkX directed graph for the PlantMind knowledge graph."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, node_type: str, **properties):
        """Add a node with type and arbitrary properties."""
        self.graph.add_node(node_id, node_type=node_type, **properties)

    def add_relationship(self, source_id: str, target_id: str, rel_type: str, **properties):
        """Add a directed relationship between two nodes."""
        self.graph.add_edge(source_id, target_id, rel_type=rel_type, **properties)

    def get_node(self, node_id: str) -> Optional[dict]:
        """Get a node's properties by ID."""
        if node_id in self.graph.nodes:
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def get_neighbors(self, node_id: str, rel_type: str = None) -> list[dict]:
        """Get all neighbors of a node, optionally filtered by relationship type."""
        neighbors = []
        for _, target, data in self.graph.out_edges(node_id, data=True):
            if rel_type is None or data.get("rel_type") == rel_type:
                neighbors.append({"id": target, "rel_type": data.get("rel_type"), **self.graph.nodes[target]})
        for source, _, data in self.graph.in_edges(node_id, data=True):
            if rel_type is None or data.get("rel_type") == rel_type:
                neighbors.append({"id": source, "rel_type": data.get("rel_type"), **self.graph.nodes[source]})
        return neighbors

    def query_by_type(self, node_type: str) -> list[dict]:
        """Get all nodes of a given type."""
        return [
            {"id": n, **self.graph.nodes[n]}
            for n in self.graph.nodes
            if self.graph.nodes[n].get("node_type") == node_type
        ]

    def get_stats(self) -> dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_types": list(set(d.get("node_type", "unknown") for _, d in self.graph.nodes(data=True))),
        }


def get_graph_store() -> GraphStore:
    """Singleton accessor for the global graph store."""
    global _graph_store
    if _graph_store is None:
        _graph_store = GraphStore()
    return _graph_store
```

### 1.4.5 `__init__.py` files for all packages

Create empty `__init__.py` in: `plantmind/ingestion/`, `plantmind/agents/`, `plantmind/api/`, `plantmind/tests/`

```python
# Each file just contains:
"""Module docstring."""
```

---

## 1.5 Create React Frontend via Vite

### Commands:
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind"
npx -y create-vite@latest web -- --template react
cd web
npm install
npm install axios react-router-dom lucide-react recharts
```

> **Note:** Run `npx create-vite@latest --help` first to confirm available options.

After Vite scaffolds the project, verify it boots:
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind\web"
npm run dev
```

Expected: Vite dev server running on `http://localhost:5173`

---

## 1.6 Create `.gitignore`

**File:** `plantmind/.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Environment
.env

# ChromaDB
data/chroma_db/

# Node
node_modules/
web/dist/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## 1.7 Verification Gate

Run these checks — **all must pass before proceeding to Step 2:**

### Check 1: Backend boots
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind"
pip install -r requirements.txt
python -m api.main
```
**Expected:** Server starts on `http://0.0.0.0:8000`. Visit `http://localhost:8000` and see:
```json
{"status": "ok", "service": "PlantMind API", "version": "1.0.0"}
```

### Check 2: Health endpoint
```bash
curl http://localhost:8000/health
```
**Expected:** JSON with `api: healthy`, `graph: healthy (0 nodes)`, `vector_db: healthy`

### Check 3: API docs load
Open `http://localhost:8000/docs` in browser — Swagger UI should show all stub endpoints.

### Check 4: Frontend boots
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind\web"
npm run dev
```
**Expected:** Vite dev server on `http://localhost:5173`, default Vite+React page renders.

### Check 5: Frontend can reach backend
In the browser console at `http://localhost:5173`, run:
```javascript
fetch('http://localhost:8000/').then(r => r.json()).then(console.log)
```
**Expected:** `{status: "ok", service: "PlantMind API", version: "1.0.0"}`

---

## Output of This Step

After completing Step 1, you should have:
- ✅ Complete monorepo directory structure
- ✅ FastAPI backend with health check + stub endpoints
- ✅ NetworkX graph store singleton
- ✅ React frontend via Vite (default template)
- ✅ All dependencies installed
- ✅ Backend ↔ Frontend CORS configured
- ✅ `.env.example` and `.gitignore` in place

**→ Proceed to [Step 2 — Sample Document Corpus](step2_sample_corpus.md)**
