# Step 9 — Demo Video & Final Packaging

## Objective
Finalize submission packaging for the hackathon judges. Write a script for a 3-minute demo video showing the "wow moments" of the system, create the final deployment check list, and organize the repository structure.

---

## 9.1 Hackathon Demo Video Script (3 Minutes)

**File:** `plantmind/docs/demo_video_script.md`

```markdown
# PlantMind Hackathon Demo Script (Target duration: 3:00)

## [0:00 - 0:30] Slide/Intro: The Problem
- **Visual:** Pitch slide detailing "fragmentation penalty" (technicians waste 35% of their shift looking for information across 7-12 disconnected databases).
- **Narration:** "Meet Coastal Refinery Unit-3. A minor leak or pump vibration requires a technician to check CSV work orders, read operating procedures, scan P&IDs, and cross-reference OISD safety standard documents. That information fragmentation drives 20% of unplanned downtime. We built PlantMind to solve this."

## [0:30 - 1:15] Demo 1: The Unified Knowledge Graph & RAG Copilot
- **Visual:** Screen capture of the **RAG Copilot View** in a browser, typing a question: *"Does emergency valve V-045 comply with safety regulations?"*
- **Narration:** "Instead of manually fetching docs, we query the PlantMind RAG Copilot. In seconds, it traverses our NetworkX knowledge graph and queries our vector store."
- **Visual:** Focus on the generated response. Show the citations panel highlighting `inspection_V045_scan.png` and `OISD_STD_154_excerpt.pdf`. Show the warning symbol: *⚠️ Violation: Actuator response time of 8 seconds exceeds 5 seconds limit.*
- **Narration:** "Look at this citation. It read an OCR-scanned inspection report listing an 8-second response time and mapped it against Clause 7.2.2 of the OISD safety PDF which mandates a 5-second maximum shutdown speed. That's a cross-document compliance gap flagged instantly."

## [1:15 - 2:00] Demo 2: Specialist Agents (RCA & Alerts)
- **Visual:** Click on the **Dashboard** navigation tab. Select **Compressor C-302** inside the control buttons.
- **Narration:** "Next, our Reliability RCA agent. When we click Compressor C-302, it traverses the graph for linked work orders and incidents. It identifies a recurring seal failure. It points out that while the seal was replaced twice, the root misalignment of 0.15mm was never corrected, raising the safety risk score to 8.2 out of 10."
- **Visual:** Click on the **Lessons Learned** tab. Show the proactive alert card: *"Alignment Checks for High-Temp Seals (Affected: C-302, P-104)."*
- **Narration:** "Finally, our Lessons Learned agent detects a common failure signature: both Pump P-104 and Compressor C-302 suffered misalignment-induced failures. Rather than treating these as isolated events, PlantMind prompts the engineering team with a preventative check-list before the next turnaround."

## [2:00 - 2:45] Technical Architecture & Ingestion Pipeline
- **Visual:** Show the 5-Layer architecture diagram from `README.md`. Show the ingestion scripts running in the terminal.
- **Narration:** "Under the hood, PlantMind uses PyMuPDF for PDFs, Tesseract for scanned OCRs, regex tag-catchers for P&ID drawings, and a Gemini NER enrichment pass. The data converges on ChromaDB for semantic chunks and a custom NetworkX graph database. This local, zero-infra setup can easily migrate to Neo4j for enterprise volume."

## [2:45 - 3:00] Conclusion & Outro
- **Visual:** Show the mobile responsive layout view, scrolling through the chat log on a simulated mobile phone.
- **Narration:** "PlantMind gives field technicians mobile access to the collective brain of the refinery, transforming downtime into uptime. Thank you."
```

---

## 9.2 Final Submission Check List

Before committing and uploading:

- [ ] `.env.example` has placeholder values (no active secret keys committed!)
- [ ] Requirements.txt contains correct versions, matching backend imports.
- [ ] Run `python -m scripts.build_graph` to verify graph data is populated inside `data/knowledge_graph.json` and vector collection works.
- [ ] Run `npm run build` on the frontend.
- [ ] Clean up any temp or test scratch logs.
- [ ] Commit all changes to the repository with clean, descriptive commit messages.

---

## Output of This Step

After completing Step 9, you should have:
- ✅ **Demo script** formatted for 3 minutes, highlighting core features (RAG Copilot, RCA dashboard, Lessons learned).
- ✅ Clean, formatted submission package guidelines ready for execution.

**→ Your PlantMind implementation steps are complete! You are ready to execute.**
