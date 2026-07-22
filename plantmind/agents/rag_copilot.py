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
if GOOGLE_API_KEY:
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
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured in .env")
                
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=2000,
                ),
            )
            
            result = json.loads(response.text)
            
        except Exception as e:
            logger.error(f"[{session_id}] LLM generation failed: {e}")
            # Mock / fallback answer if Gemini key is missing or failed during testing
            result = {
                "answer": f"I am running in offline verification mode because GOOGLE_API_KEY is not set or failed. Context details: {retrieval['graph_context']['entity_count']} entities and {len(retrieval['vector_results'])} document matches were successfully retrieved.",
                "confidence": "LOW",
                "confidence_score": 0.5,
                "citations": [
                    {
                        "doc_title": r["metadata"].get("filename", "unknown"),
                        "relevant_text": r["text"][:100],
                        "relevance": "Retrieved through local vector semantic similarity"
                    }
                    for r in retrieval["vector_results"][:2]
                ],
                "cross_document_insights": ["Offline retrieval fallback loaded successfully."],
                "safety_flags": [],
                "follow_up_suggestions": ["Please configure GOOGLE_API_KEY in .env to enable generative AI responses."],
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
