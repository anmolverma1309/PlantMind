# PlantMind Demo Video Script

## Duration: 3-4 minutes

---

## Scene 1: Problem Statement (0:00 – 0:30)

**[Screen: Industrial plant footage / document chaos montage]**

**Narration:**
> "Industrial plants generate thousands of documents every year — work orders, incident reports, safety procedures, regulatory compliance records, and engineering diagrams. Today, when a technician needs to troubleshoot a pump failure at 2 AM, they're searching through filing cabinets, not querying an intelligent brain."

> "PlantMind changes that."

---

## Scene 2: Architecture Overview (0:30 – 1:00)

**[Screen: Show the Mermaid architecture diagram from README]**

**Narration:**
> "PlantMind ingests scattered documents through a multi-format pipeline — CSVs, PDFs, OCR scans, P&ID diagrams — and builds a unified Knowledge Graph connecting equipment, maintenance history, incidents, and regulations."

> "On top of this graph, we deploy four specialized Gemini-powered AI agents."

**[Show: Agent icons — RAG Copilot, RCA Agent, Compliance Auditor, Lessons-Learned]**

---

## Scene 3: Live Demo — RAG Copilot (1:00 – 1:45)

**[Screen: Open browser at localhost:5173 → Chat tab]**

### Demo Question 1:
> "What caused the C-302 compressor seal failure?"

**[Show: Copilot responds with detailed answer, citations from incident_report_C302.txt and work_orders.csv, confidence score, and safety flags]**

### Demo Question 2:
> "Which equipment shares misalignment as a root cause?"

**[Show: Cross-document insight highlighting both P-104 and C-302]**

**Narration:**
> "The RAG Copilot combines vector similarity search with knowledge graph traversal for hybrid retrieval — giving richer, more accurate answers than traditional RAG alone."

---

## Scene 4: Live Demo — RCA Dashboard (1:45 – 2:15)

**[Screen: Switch to Dashboard tab → Select C-302]**

**[Show: Failure modes detected (Seal Failure), root cause conclusion (misalignment 0.15mm), recommendations with HIGH priority actions]**

**Narration:**
> "The RCA Agent analyzes equipment work order history and incident data to automatically identify recurring failure patterns and generate corrective action plans."

---

## Scene 5: Live Demo — Compliance Audit (2:15 – 2:45)

**[Screen: Switch to Compliance tab]**

**[Show: Audit score (78%), CRITICAL violation for V-045 valve response time (8s vs 5s OISD limit)]**

**Narration:**
> "The Compliance Agent cross-references equipment data against regulatory standards like OISD-154 and the Factory Act, flagging critical gaps before auditors do."

---

## Scene 6: Live Demo — Knowledge Graph (2:45 – 3:10)

**[Screen: Switch to Graph tab]**

**[Show: Node directory with Equipment, Document, Regulation, WorkOrder types. Edge relationships showing GOVERNED_BY, HAS_WORK_ORDER, REFERENCES connections]**

**Narration:**
> "Everything is connected through a queryable knowledge graph — equipment links to work orders, which link to incidents, which link to regulations. No more siloed information."

---

## Scene 7: Closing & Gemini API Usage (3:10 – 3:30)

**[Screen: Split — architecture diagram + API key configuration]**

**Narration:**
> "PlantMind uses the Google Gemini API across every layer:"
> - "Gemini 2.0 Flash for all agent generation"  
> - "Embedding-001 for semantic vector search"
> - "Structured JSON output for reliable parsing"
> - "NER extraction for entity recognition"

> "All with graceful offline fallbacks for demo reliability."

**[Show: PlantMind logo + tagline]**

> "PlantMind — Making industrial knowledge accessible, actionable, and intelligent."

---

## Demo Checklist

Before recording, ensure:

1. [ ] `GOOGLE_API_KEY` is set in `.env`
2. [ ] Run `python -m scripts.build_graph` (builds knowledge graph)
3. [ ] Backend running: `python -m api.main` (port 8000)
4. [ ] Frontend running: `cd web && npm run dev` (port 5173)
5. [ ] Test all 5 tabs: Chat, Dashboard, Compliance, Lessons, Graph
6. [ ] Test at least 2 chat questions
7. [ ] Verify RCA works for both P-104 and C-302
