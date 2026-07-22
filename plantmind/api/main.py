"""FastAPI application entry point."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import CORS_ORIGINS, API_HOST, API_PORT, DATA_DIR
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


@app.on_event("startup")
async def load_knowledge_graph():
    """Load the persisted knowledge graph on startup."""
    from graph.graph_store import get_graph_store
    
    logger = logging.getLogger("plantmind.startup")
    graph_path = DATA_DIR / "knowledge_graph.json"
    
    if graph_path.exists():
        try:
            graph = get_graph_store()
            graph.load_from_json(str(graph_path))
            stats = graph.get_stats()
            logger.info(f"Knowledge graph loaded: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        except Exception as e:
            logger.error(f"Failed to load knowledge graph: {e}")
    else:
        logger.warning("No persisted knowledge graph found — run `python -m scripts.build_graph` first")


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "PlantMind API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint that verifies all subsystems."""
    from graph.graph_store import get_graph_store
    from graph.vector_store import get_local_vector_store
    
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
        vector_store = get_local_vector_store()
        checks["vector_db"] = f"healthy ({vector_store.count()} chunks)"
    except Exception as e:
        checks["vector_db"] = f"error: {str(e)}"
    
    overall = "healthy" if all("healthy" in str(v) for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=API_HOST, port=int(API_PORT), reload=True)
