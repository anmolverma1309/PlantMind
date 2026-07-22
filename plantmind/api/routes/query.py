"""Query endpoint — RAG copilot chat interface."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    entity_hints: Optional[list[str]] = None


class Citation(BaseModel):
    doc_title: str
    relevant_text: str = ""
    relevance: str = ""


class QueryResponse(BaseModel):
    answer: str
    confidence: str
    confidence_score: float
    citations: list[dict]
    graph_entities: list[dict]
    cross_document_insights: list[str]
    safety_flags: list[str]
    follow_up_suggestions: list[str]
    session_id: str
    retrieval_stats: dict


@router.post("/query", response_model=QueryResponse)
async def query_copilot(request: QueryRequest):
    """
    Send a natural language question to the PlantMind RAG Copilot.
    
    The copilot performs hybrid retrieval (graph + vector search)
    and generates an answer with citations and confidence scores.
    """
    from agents.rag_copilot import get_copilot
    
    try:
        copilot = get_copilot()
        result = await copilot.query(
            question=request.question,
            session_id=request.session_id,
            entity_hints=request.entity_hints,
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/health")
async def query_health():
    """Check if the query system is ready."""
    from agents.rag_copilot import get_copilot
    
    try:
        copilot = get_copilot()
        chunk_count = copilot.retriever.vector_store.count()
        graph_stats = copilot.retriever.graph.get_stats()
        
        return {
            "status": "ready",
            "vector_store_chunks": chunk_count,
            "graph_nodes": graph_stats["total_nodes"],
            "graph_edges": graph_stats["total_edges"],
        }
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}
