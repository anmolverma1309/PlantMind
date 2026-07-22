# Step 5 — RAG Copilot Agent (Core Demo Feature)

## Objective
Build the hybrid retrieval-augmented generation copilot that combines graph traversal + vector semantic search to answer natural language questions with citations and confidence scores. This is the **highest-visibility deliverable** — judges will interact with it directly.

---

## 5.1 Hybrid Retriever

**File:** `plantmind/agents/retriever.py`

```python
"""
Hybrid retriever — combines graph traversal + vector semantic search.

This is the core retrieval engine shared by all agents. It provides
richer context than pure vector search by also pulling graph-connected
entities and their relationships.
"""

import logging
from typing import Optional
import chromadb
from graph.graph_store import get_graph_store
from graph.schema import NodeType
from api.config import CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Retrieval engine that combines:
    1. Vector semantic search (ChromaDB) for relevant text chunks
    2. Graph traversal (NetworkX) for related entities and context
    
    The merged context is richer than either source alone.
    """

    def __init__(self):
        self.graph = get_graph_store()
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
            self._collection = client.get_collection("plantmind_chunks")
        return self._collection

    def retrieve(
        self,
        query: str,
        n_vector_results: int = 5,
        graph_depth: int = 2,
        entity_hints: list[str] = None,
    ) -> dict:
        """
        Hybrid retrieval: vector search + graph traversal.
        
        Args:
            query: Natural language question
            n_vector_results: Number of vector search results
            graph_depth: BFS depth for graph traversal
            entity_hints: Optional list of entity names/tags detected in the query
        
        Returns:
            {
                "vector_results": [...],      # Semantically similar text chunks
                "graph_context": {...},        # Graph traversal results
                "merged_context": str,         # Combined context string for LLM
                "source_documents": [...],     # Unique source documents
                "confidence_signals": {...},   # Retrieval quality indicators
            }
        """
        # 1. Vector semantic search
        vector_results = self._vector_search(query, n_vector_results)
        
        # 2. Extract entity mentions from query (simple approach)
        if entity_hints is None:
            entity_hints = self._extract_entity_hints(query)
        
        # 3. Graph traversal for each mentioned entity
        graph_context = self._graph_search(entity_hints, graph_depth)
        
        # 4. Merge contexts
        merged_context = self._merge_contexts(vector_results, graph_context)
        
        # 5. Collect source documents
        source_docs = self._collect_sources(vector_results, graph_context)
        
        # 6. Calculate confidence signals
        confidence = self._calculate_confidence(vector_results, graph_context)
        
        return {
            "vector_results": vector_results,
            "graph_context": graph_context,
            "merged_context": merged_context,
            "source_documents": source_docs,
            "confidence_signals": confidence,
        }

    def _vector_search(self, query: str, n_results: int) -> list[dict]:
        """Search ChromaDB for semantically similar text chunks."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            chunks = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    chunks.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0,
                        "id": results["ids"][0][i] if results["ids"] else "",
                    })
            
            return chunks
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _extract_entity_hints(self, query: str) -> list[str]:
        """
        Extract potential entity references from the query text.
        Uses simple pattern matching — the LLM-based intent parser 
        in the copilot provides more sophisticated extraction.
        """
        import re
        
        hints = []
        
        # Look for equipment tag patterns (P-104, HX-201, V-045, C-302, etc.)
        tag_matches = re.findall(r'\b([A-Z]{1,3}-\d{2,4}[A-Z]?)\b', query)
        hints.extend(tag_matches)
        
        # Look for work order patterns (WO-2024-001)
        wo_matches = re.findall(r'\b(WO-\d{4}-\d{3})\b', query)
        hints.extend(wo_matches)
        
        # Look for incident patterns (INC-2024-003)
        inc_matches = re.findall(r'\b(INC-\d{4}-\d{3})\b', query)
        hints.extend(inc_matches)
        
        # Look for regulation patterns (OISD-STD-154)
        reg_matches = re.findall(r'\b(OISD-STD-\d+)\b', query, re.IGNORECASE)
        hints.extend(reg_matches)
        
        # Look for SOP patterns (SOP-SAFE-007)
        sop_matches = re.findall(r'\b(SOP-[A-Z]+-\d+)\b', query, re.IGNORECASE)
        hints.extend(sop_matches)
        
        # Also try to find known node names in the graph
        for word in query.split():
            node = self.graph.find_node(word.strip('?,.:'))
            if node:
                hints.append(node["id"])
        
        return list(set(hints))

    def _graph_search(self, entity_hints: list[str], depth: int) -> dict:
        """Traverse the graph from each hinted entity to build relational context."""
        all_nodes = []
        all_edges = []
        entity_details = []
        
        for hint in entity_hints:
            node = self.graph.find_node(hint)
            if node:
                entity_details.append(node)
                
                # BFS traversal
                subgraph = self.graph.traverse(node["id"], max_depth=depth)
                all_nodes.extend(subgraph["nodes"])
                all_edges.extend(subgraph["edges"])
        
        # Deduplicate nodes
        seen_ids = set()
        unique_nodes = []
        for n in all_nodes:
            if n["id"] not in seen_ids:
                unique_nodes.append(n)
                seen_ids.add(n["id"])
        
        return {
            "matched_entities": entity_details,
            "nodes": unique_nodes,
            "edges": all_edges,
            "entity_count": len(unique_nodes),
            "relationship_count": len(all_edges),
        }

    def _merge_contexts(self, vector_results: list[dict], graph_context: dict) -> str:
        """
        Merge vector search results and graph context into a single 
        context string for the LLM.
        """
        sections = []
        
        # Graph context section
        if graph_context["matched_entities"]:
            sections.append("=== KNOWLEDGE GRAPH CONTEXT ===")
            
            for entity in graph_context["matched_entities"]:
                sections.append(f"\n--- Entity: {entity.get('name', entity['id'])} ({entity.get('node_type', 'Unknown')}) ---")
                
                # Add entity properties
                props = {k: v for k, v in entity.items() if k not in ('id', 'name', 'node_type', 'source_docs')}
                if props:
                    sections.append(f"Properties: {props}")
            
            # Add relationships
            if graph_context["edges"]:
                sections.append("\n--- Relationships ---")
                for edge in graph_context["edges"][:20]:  # Limit to avoid context overflow
                    sections.append(f"  {edge['source']} --[{edge['rel_type']}]--> {edge['target']}")
            
            # Add connected nodes with details
            sections.append("\n--- Connected Entities ---")
            for node in graph_context["nodes"][:15]:
                node_type = node.get("node_type", "Unknown")
                name = node.get("name", node["id"])
                props_str = ""
                relevant_props = {k: v for k, v in node.items() 
                                 if k not in ('id', 'name', 'node_type', 'source_docs', 'direction', 'rel_type')}
                if relevant_props:
                    props_str = f" | {relevant_props}"
                sections.append(f"  [{node_type}] {name}{props_str}")
        
        # Vector search results section
        if vector_results:
            sections.append("\n=== DOCUMENT TEXT MATCHES ===")
            for i, result in enumerate(vector_results):
                doc_info = result["metadata"].get("filename", "unknown")
                sections.append(f"\n--- Match {i+1} (from: {doc_info}) ---")
                sections.append(result["text"])
        
        return "\n".join(sections)

    def _collect_sources(self, vector_results: list[dict], graph_context: dict) -> list[dict]:
        """Collect unique source document references."""
        sources = {}
        
        # From vector results
        for result in vector_results:
            filename = result["metadata"].get("filename", "unknown")
            if filename not in sources:
                sources[filename] = {
                    "filename": filename,
                    "doc_type": result["metadata"].get("doc_type", "unknown"),
                    "relevance_score": 1.0 - result.get("distance", 0),
                    "match_type": "semantic",
                }
        
        # From graph context
        for node in graph_context.get("nodes", []):
            if node.get("node_type") == "Document":
                filename = node.get("name", "unknown")
                if filename not in sources:
                    sources[filename] = {
                        "filename": filename,
                        "doc_type": node.get("doc_type", "unknown"),
                        "relevance_score": 0.8,
                        "match_type": "graph",
                    }
        
        return list(sources.values())

    def _calculate_confidence(self, vector_results: list[dict], graph_context: dict) -> dict:
        """
        Calculate confidence signals for the retrieval quality.
        Higher confidence = more relevant context found.
        """
        signals = {
            "vector_match_count": len(vector_results),
            "graph_entity_count": len(graph_context.get("matched_entities", [])),
            "graph_relationship_count": len(graph_context.get("edges", [])),
            "has_graph_context": len(graph_context.get("matched_entities", [])) > 0,
            "has_vector_context": len(vector_results) > 0,
        }
        
        # Calculate overall confidence score (0-1)
        score = 0.0
        
        if vector_results:
            # Best vector match distance (lower = better match)
            best_distance = min(r.get("distance", 1.0) for r in vector_results)
            vector_score = max(0, 1.0 - best_distance)
            score += vector_score * 0.5
        
        if graph_context.get("matched_entities"):
            graph_score = min(1.0, len(graph_context["matched_entities"]) * 0.3 + 
                            len(graph_context.get("edges", [])) * 0.05)
            score += graph_score * 0.5
        
        signals["overall_confidence"] = round(min(1.0, score), 3)
        
        return signals
```

---

## 5.2 RAG Copilot Agent

**File:** `plantmind/agents/rag_copilot.py`

```python
"""
RAG Copilot — the main Q&A agent for PlantMind.

Combines hybrid retrieval (graph + vector) with LLM generation
to answer natural language questions about industrial assets,
with citations and confidence scores.
"""

import json
import logging
import uuid
from typing import Optional
import google.generativeai as genai
from api.config import GOOGLE_API_KEY
from agents.retriever import HybridRetriever

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

COPILOT_SYSTEM_PROMPT = """You are PlantMind Copilot, an AI assistant for industrial plant operations at Coastal Refinery Unit-3.

You have access to a knowledge graph containing information about equipment, maintenance records, safety procedures, inspection reports, work orders, incidents, and regulatory requirements.

Your role:
1. Answer questions accurately based ONLY on the provided context
2. Cite specific source documents for every claim
3. Highlight cross-document insights when applicable
4. Flag safety-critical information prominently
5. If information is insufficient, say so clearly — never fabricate facts

Response format:
- Give a clear, direct answer first
- Follow with supporting evidence and citations
- Note confidence level (High/Medium/Low)
- If you identify a safety concern or compliance gap, flag it with ⚠️
- For cross-document insights, explicitly note which documents contribute to the insight"""

COPILOT_QUERY_PROMPT = """Based on the following context from the PlantMind knowledge graph and document database, answer the user's question.

{context}

USER QUESTION: {question}

Instructions:
1. Answer based ONLY on the context above — do not use external knowledge
2. Cite specific documents by filename in [brackets]
3. If the context contains information from multiple documents that together provide a richer answer, highlight this as a "Cross-Document Insight"
4. Rate your confidence as:
   - HIGH: Direct answer found in context with clear evidence
   - MEDIUM: Answer inferred from partial context
   - LOW: Limited relevant context found
5. If you identify any safety concerns, compliance gaps, or repeated failure patterns, flag them with ⚠️

Provide your response as JSON with this structure:
{{
    "answer": "Your detailed answer here",
    "confidence": "HIGH|MEDIUM|LOW",
    "confidence_score": 0.0-1.0,
    "citations": [
        {{
            "doc_title": "filename",
            "relevant_text": "brief quote from the document",
            "relevance": "why this document is relevant"
        }}
    ],
    "cross_document_insights": [
        "Any insights that combine information from multiple documents"
    ],
    "safety_flags": [
        "Any safety concerns or compliance gaps identified"
    ],
    "follow_up_suggestions": [
        "Suggested follow-up questions the user might want to ask"
    ]
}}"""


class RAGCopilot:
    """
    The main Q&A agent that combines hybrid retrieval with LLM generation.
    """

    def __init__(self):
        self.retriever = HybridRetriever()
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=COPILOT_SYSTEM_PROMPT,
        )
        self.sessions: dict[str, list] = {}  # session_id -> conversation history

    async def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        entity_hints: Optional[list[str]] = None,
    ) -> dict:
        """
        Process a user question through the full RAG pipeline.
        
        Pipeline:
        1. Parse intent and extract entity hints
        2. Hybrid retrieval (vector + graph)
        3. Build context from retrieved information
        4. Generate answer with Gemini
        5. Parse and validate response
        
        Args:
            question: Natural language question
            session_id: Optional session ID for conversation continuity
            entity_hints: Optional pre-extracted entity references
        
        Returns:
            Structured response with answer, citations, confidence
        """
        if not session_id:
            session_id = str(uuid.uuid4())[:8]
        
        logger.info(f"[{session_id}] Query: {question}")
        
        # Step 1: Hybrid retrieval
        retrieval = self.retriever.retrieve(
            query=question,
            n_vector_results=5,
            graph_depth=2,
            entity_hints=entity_hints,
        )
        
        logger.info(
            f"[{session_id}] Retrieved: "
            f"{len(retrieval['vector_results'])} vector matches, "
            f"{retrieval['graph_context']['entity_count']} graph entities"
        )
        
        # Step 2: Build prompt with context
        prompt = COPILOT_QUERY_PROMPT.format(
            context=retrieval["merged_context"],
            question=question,
        )
        
        # Step 3: Generate answer with Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=2000,
                ),
            )
            
            result = json.loads(response.text)
            
        except json.JSONDecodeError:
            # If JSON parsing fails, wrap the raw text
            result = {
                "answer": response.text if response else "Failed to generate answer",
                "confidence": "LOW",
                "confidence_score": 0.3,
                "citations": [],
                "cross_document_insights": [],
                "safety_flags": [],
                "follow_up_suggestions": [],
            }
        except Exception as e:
            logger.error(f"[{session_id}] LLM generation failed: {e}")
            result = {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "confidence": "LOW",
                "confidence_score": 0.0,
                "citations": [],
                "cross_document_insights": [],
                "safety_flags": [],
                "follow_up_suggestions": [],
            }
        
        # Step 4: Enrich with retrieval metadata
        result["session_id"] = session_id
        result["retrieval_stats"] = {
            "vector_matches": len(retrieval["vector_results"]),
            "graph_entities": retrieval["graph_context"]["entity_count"],
            "graph_relationships": retrieval["graph_context"]["relationship_count"],
            "source_documents": retrieval["source_documents"],
        }
        result["graph_entities"] = [
            {
                "id": e["id"],
                "name": e.get("name", e["id"]),
                "type": e.get("node_type", "Unknown"),
            }
            for e in retrieval["graph_context"].get("matched_entities", [])
        ]
        
        # Merge confidence from retrieval signals
        retrieval_confidence = retrieval["confidence_signals"]["overall_confidence"]
        llm_confidence = result.get("confidence_score", 0.5)
        result["confidence_score"] = round((retrieval_confidence + llm_confidence) / 2, 3)
        
        # Store in session history
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({
            "question": question,
            "answer": result["answer"],
            "confidence": result["confidence_score"],
        })
        
        return result


# Singleton instance
_copilot: Optional[RAGCopilot] = None


def get_copilot() -> RAGCopilot:
    global _copilot
    if _copilot is None:
        _copilot = RAGCopilot()
    return _copilot
```

---

## 5.3 Update Query API Endpoint

Replace the stub in `plantmind/api/routes/query.py`:

```python
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
        chunk_count = copilot.retriever.collection.count()
        graph_stats = copilot.retriever.graph.get_stats()
        
        return {
            "status": "ready",
            "vector_store_chunks": chunk_count,
            "graph_nodes": graph_stats["total_nodes"],
            "graph_edges": graph_stats["total_edges"],
        }
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}
```

---

## 5.4 Startup: Auto-Load Graph on Server Boot

Update `plantmind/api/main.py` to load the persisted graph on startup:

Add this after the app is created:

```python
@app.on_event("startup")
async def load_knowledge_graph():
    """Load the persisted knowledge graph and verify vector store on startup."""
    import logging
    from pathlib import Path
    from graph.graph_store import get_graph_store
    from api.config import DATA_DIR
    
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
```

---

## 5.5 Verification Gate

**All checks must pass before proceeding to Step 6:**

### Check 1: Build graph first (if not already done)
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind"
python -m scripts.build_graph
```

### Check 2: Start the API server
```bash
python -m api.main
```
**Expected:** Graph loads on startup, server is ready.

### Check 3: Query health check
```bash
curl http://localhost:8000/api/v1/query/health
```
**Expected:** `{"status": "ready", "vector_store_chunks": 10+, "graph_nodes": 20+, ...}`

### Check 4: Test ground truth questions

Run each of these queries and verify the copilot answers correctly:

```bash
# GT-01: Single document query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many work orders have been raised for Pump P-104?"}'
# Expected: Answer mentions 3 work orders (WO-2024-001, WO-2024-004, WO-2024-008)

# GT-02: Cross-document query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the root cause of recurring vibration in Pump P-104?"}'
# Expected: Coupling misalignment, bearing wear, thermal expansion

# GT-05: Cross-document compliance (THE WOW MOMENT)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Does Valve V-045 comply with OISD-STD-154 requirements?"}'
# Expected: No — 8 sec response time vs 5 sec max requirement, with ⚠️ flag

# GT-11: Cross-document insight
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Are there any common failure patterns across different equipment?"}'
# Expected: Misalignment is a recurring root cause in both P-104 and C-302
```

### Check 5: Benchmark evaluation script

```bash
python -c "
import json
import asyncio
from agents.rag_copilot import get_copilot

async def benchmark():
    copilot = get_copilot()
    gt = json.load(open('data/ground_truth.json'))
    
    correct = 0
    total = len(gt['facts'])
    
    for fact in gt['facts'][:5]:  # Test first 5 for speed
        result = await copilot.query(fact['question'])
        confidence = result.get('confidence_score', 0)
        has_citations = len(result.get('citations', [])) > 0
        
        print(f'{fact[\"id\"]}: confidence={confidence:.2f}, citations={has_citations}')
        print(f'  Q: {fact[\"question\"]}')
        print(f'  A: {result[\"answer\"][:150]}...')
        print()
        
        if confidence > 0.3 and has_citations:
            correct += 1
    
    print(f'Score: {correct}/{total} passed confidence + citation check')

asyncio.run(benchmark())
"
```

---

## Output of This Step

After completing Step 5, you should have:
- ✅ HybridRetriever combining graph traversal + vector search
- ✅ RAG Copilot with Gemini-powered answer generation
- ✅ Structured responses with citations, confidence scores, and safety flags
- ✅ Cross-document insight detection
- ✅ `/api/v1/query` endpoint fully functional
- ✅ Auto-loading of persisted graph on server startup
- ✅ At least 3/5 ground truth questions answered correctly with citations

**→ Proceed to [Step 6 — Specialist Agents](step6_specialist_agents.md)**
