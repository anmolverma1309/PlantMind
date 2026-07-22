# Product Requirements Document (PRD)
## PlantMind — Unified Asset & Operations Brain

**Version:** 1.0
**Purpose:** Build specification for AI coding agent (Antigravity) to scaffold and implement the working prototype
**Target Deliverable:** Functional prototype + architecture diagram + GitHub repo + README

---

## 1. Product Summary

**What it is:** An AI platform that ingests heterogeneous industrial documents (P&IDs, maintenance records, safety procedures, inspection reports, regulatory filings) into one knowledge graph, and exposes that graph through specialist AI agents — a Q&A copilot, a maintenance/RCA agent, a compliance agent, and a lessons-learned agent — accessible via mobile-first chat UI and a desktop dashboard.

**Why it matters:** Plants lose ~35% of working hours to information fragmentation across 7–12 disconnected systems, driving 18–22% of unplanned downtime. PlantMind unifies these systems into one queryable, proactive layer.

**Prototype scope (hackathon-realistic):** We are NOT building all 5 pillars at full depth. We are building one working vertical slice — document ingestion → knowledge graph → RAG copilot — with the maintenance, compliance, and lessons-learned agents implemented as thinner functional demos on top of the same graph.

---

## 2. Goals & Non-Goals

**Goals for the prototype:**
- Ingest a small real/sample corpus (5–10 documents: mix of PDF procedures, a scanned inspection form, a CSV of work orders, a sample P&ID image)
- Extract entities and build an actual queryable knowledge graph
- Answer natural-language questions with citations and confidence scores
- Demonstrate at least one cross-document insight no single document could give alone (this is the "wow moment" for judges)
- Provide a usable mobile-responsive chat UI and a simple dashboard

**Non-goals (explicitly out of scope for prototype):**
- Production-grade security/auth
- Full regulatory ontology coverage (demo 2–3 OISD/PESO clauses, not the full corpus)
- Real-time IoT/sensor integration
- Enterprise-scale document volume (>1000 docs) — architecture should support it, prototype won't test it

---

## 3. Step-by-Step Build Plan (Sequential, for Agent Execution)

Each step below is a discrete unit of work. Complete and verify each step before moving to the next. Do not parallelize steps 1–4; they are dependencies.

### **Step 1 — Project Scaffolding & Environment Setup**
**Thinking model:** Before writing any feature code, establish a clean, runnable skeleton so every later step has somewhere to plug in.

- Initialize monorepo structure:
  ```
  /plantmind
    /ingestion       (document processing pipeline)
    /graph           (knowledge graph construction + queries)
    /agents          (RAG copilot, RCA, compliance, lessons-learned)
    /api             (backend orchestration, FastAPI)
    /web             (frontend — mobile-first chat + dashboard)
    /data/sample_docs (test corpus)
    /docs            (README, architecture diagram)
  ```
- Set up Python backend (FastAPI) and Node/React frontend
- Set up Neo4j (or NetworkX for a lighter prototype if Neo4j hosting is a blocker) instance
- Set up vector DB (Chroma or Qdrant — lightweight, local-friendly)
- Confirm: backend boots, frontend boots, DBs connect. **Do not proceed until this is verified.**

### **Step 2 — Sample Document Corpus**
**Thinking model:** The demo is only as convincing as the data. Curate before you build extraction logic, so extraction can be tested against real targets.

- Collect/create 5–10 representative documents:
  - 2–3 maintenance/work-order records (PDF or CSV)
  - 1–2 safety/operating procedures (PDF)
  - 1 scanned inspection form (image, to exercise OCR)
  - 1 simplified P&ID (image, to exercise CV/tag detection)
  - 1–2 regulatory reference excerpts (OISD/PESO/Factory Act sample clauses)
- Store in `/data/sample_docs`, organized by type
- Manually note 10–15 "ground truth" facts across these documents (equipment tags, dates, failure causes) — this becomes your evaluation benchmark later

### **Step 3 — Ingestion Pipeline**
**Thinking model:** Build ingestion as independent, swappable modules by document type, since PDFs, scans, and images each need different extraction logic — but all must converge on the same output schema.

- Text PDFs → text extraction (PyMuPDF/pdfplumber) → chunking
- Scanned documents → OCR (Tesseract or a cloud OCR API) → text
- P&ID/drawing image → CV pass for tag/symbol detection (can be simplified to OCR-on-image for prototype if full CV model is out of scope) → tag list
- CSV/structured records → direct parse into structured entities
- **NER pass** on all extracted text: identify equipment tags, dates, personnel, regulatory references, failure modes (use an LLM-based extraction prompt if a fine-tuned NER model isn't feasible in the timeframe)
- Output: a standardized JSON schema per document — `{doc_id, doc_type, entities[], relationships[], raw_text_chunks[], source_metadata}`
- **Verify:** run all sample docs through the pipeline, manually check extracted entities against your ground-truth list from Step 2

### **Step 4 — Knowledge Graph Construction**
**Thinking model:** The graph is the differentiator versus a plain RAG chatbot — it's what lets the system answer cross-document questions. Design the schema before writing ingestion-to-graph code.

- Define node types: `Equipment`, `Document`, `Procedure`, `Incident`, `Regulation`, `Person`, `WorkOrder`
- Define relationship types: `MENTIONED_IN`, `MAINTAINED_BY`, `GOVERNED_BY`, `CAUSED_BY`, `PART_OF`, `PERFORMED_BY`
- Write the entity/relationship loader that takes Step 3's JSON output and populates Neo4j (or NetworkX)
- Also embed text chunks into the vector DB, tagged with the same entity IDs — this is what enables hybrid retrieval (graph traversal + semantic search)
- **Verify:** manually query the graph (e.g., "show all incidents linked to Pump P-104") and confirm relationships are correctly linked

### **Step 5 — RAG Copilot Agent (Core Demo Feature)**
**Thinking model:** This is the highest-visibility deliverable — it's what judges will interact with directly. Build the retrieval logic to be hybrid (graph + vector) so answers can cite specific relationships, not just matching text.

- Query flow: user question → intent parse → (a) vector search for relevant chunks + (b) graph traversal for related entities → merge context → LLM generates answer with citations
- Response format: answer text + confidence score (based on retrieval score + graph linkage strength) + list of source documents with clickable references
- Build a basic chat API endpoint (`POST /query`)
- **Verify against ground-truth benchmark** from Step 2 — measure how many of your 10–15 known facts the copilot answers correctly with correct citations

### **Step 6 — Specialist Agents (Maintenance/RCA, Compliance, Lessons-Learned)**
**Thinking model:** These reuse the same graph and retrieval layer from Step 5 — don't rebuild retrieval logic per agent. Each agent is a specialized prompt + query pattern on top of shared infrastructure.

- **Maintenance/RCA agent:** given an equipment tag, traverse graph for linked work orders + incidents + procedures → LLM synthesizes likely root cause + recommendation
- **Compliance agent:** given a regulation node, traverse graph for linked procedures/equipment → LLM flags gaps where no linked compliant procedure exists
- **Lessons-learned agent:** scan incident nodes for repeated patterns (same equipment type + same failure mode across multiple incidents) → generate proactive alert text
- Each agent = one API endpoint + one specialized prompt template, orchestrated via LangGraph or simple function routing
- **Verify:** run each agent against your sample corpus and confirm at least one genuinely correct cross-document insight per agent — this is your demo's "wow moment," identify it now so the demo video can showcase it

### **Step 7 — Frontend: Mobile Chat + Dashboard**
**Thinking model:** Build mobile-first since that's the stated differentiator (field technicians, not just desk engineers). Dashboard is secondary — a thin layer over the same API.

- Chat interface: question input, streaming answer, citation links, confidence badge — responsive/mobile-first layout
- Dashboard: simple views for (a) compliance gap list, (b) recent lessons-learned alerts, (c) knowledge graph visual (even a simple force-directed graph view adds strong visual impact for judges)
- Connect frontend to backend API endpoints from Steps 5 & 6
- **Verify:** full end-to-end flow works — ask a question in UI, get cited answer; view a compliance gap; view an alert

### **Step 8 — Architecture Diagram & Documentation**
**Thinking model:** Do this after the system works, not before, so the diagram reflects what was actually built, not what was planned.

- Draw the 5-layer architecture diagram (Ingestion → Knowledge Graph → Agent Layer → Application Layer → Feedback Loop), matching what's actually implemented
- Write README: setup instructions, architecture overview, how to run locally, sample queries to try, known limitations
- Document the evaluation results against your ground-truth benchmark (entity extraction accuracy, query answer accuracy)

### **Step 9 — Demo Video & Final Packaging**
**Thinking model:** The demo video should follow the judging criteria order — problem, solution, live demo of the "wow moment," architecture, scalability — not just a feature walkthrough.

- Script: problem (15s) → solution overview (20s) → live demo: ask copilot a question, show RCA agent catching a cross-document insight, show compliance gap detection (90s) → architecture + scalability (30s) → close (5s)
- Keep to 3–4 minutes per submission requirements
- Package: GitHub repo (public, clean commit history, README at root), architecture diagram (PDF/PNG export), demo video, working prototype link/instructions

---

## 4. Success Metrics (Tie Back to Judging Criteria)

| Judging Criterion | How this PRD addresses it |
|---|---|
| Relevance to PS | Steps 3–6 directly implement all 5 PS pillars on one shared graph |
| Innovation & Creativity | Hybrid graph+vector retrieval; proactive lessons-learned agent (Step 6) |
| Technical Implementation | Real knowledge graph (not just vector search), verified against ground truth at each step |
| Business Viability | Compliance auto-evidence + RCA reduce measurable downtime/audit cost (Step 6, Step 9 framing) |
| Presentation & Clarity | Step 9 demo script structured around a clear "wow moment" |
| Impact & Scalability | Architecture (Step 1, Step 8) is modular/swappable per doc type — supports scale-up without redesign |

---

## 5. Risks & Fallbacks

- **CV/P&ID parsing too complex for timeframe** → fallback to OCR-only on drawing images, note as future work
- **Neo4j setup friction** → fallback to NetworkX in-memory graph for prototype, same schema, easy migration path
- **LLM extraction inaccuracy** → keep ground-truth benchmark small and manually verify; report honest accuracy % in README rather than overclaiming

---

## 6. Handoff Notes for Antigravity

Execute Steps 1–9 sequentially. After each step, run its stated verification before proceeding — do not chain unverified steps. Flag any step where a fallback (Section 5) had to be used, so it can be called out honestly in the README and demo narration.
