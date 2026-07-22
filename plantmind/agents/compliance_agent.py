"""Compliance Agent — analyzes regulatory alignment and flags gaps."""

import json
import logging
import google.generativeai as genai
from api.config import GOOGLE_API_KEY
from graph.queries import find_compliance_gaps, get_equipment_history
from graph.graph_store import get_graph_store
from graph.schema import NodeType

logger = logging.getLogger(__name__)

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

COMPLIANCE_PROMPT_TEMPLATE = """You are an Industrial Safety Auditor and Compliance Specialist.

Analyze the regulatory compliance gaps found in Coastal Refinery Unit-3.

COMPLIANCE DATA & GRAPH DETAILS:
{context}

Your task:
1. Review the listed gaps between regulations (e.g., OISD-STD-154, Factory Act) and the active equipment/procedures.
2. Explain the safety and regulatory implications of each gap.
3. Suggest a corrective action plan to achieve full compliance.
4. Highlight critical violations that require immediate attention (e.g., slow isolation valves).

Format your response as a JSON object with this EXACT structure:
{{
  "summary": "Compliance overview of the facility",
  "total_gaps": 0,
  "violations": [
    {{
      "equipment_tag": "V-045",
      "regulation": "OISD-STD-154",
      "clause": "Clause 7.2.2",
      "description": "Describe the violation (e.g. valve response time 8s exceeds 5s max)",
      "implication": "Safety or legal risk of this violation",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "recommended_action": "How to resolve the compliance gap"
    }}
  ],
  "audit_score": 0.0-100.0
}}

Ensure the response contains ONLY valid JSON. Keep it audit-ready, professional, and directly tied to the context."""


class ComplianceAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def analyze(self) -> dict:
        """Run compliance gap analysis across the knowledge graph."""
        # 1. Fetch compliance gaps and related records from the graph
        gaps = find_compliance_gaps()
        graph = get_graph_store()
        
        # 2. Enrich the context by checking inspection reports for governed equipment
        context_parts = []
        context_parts.append(f"Direct gaps detected by graph relationships: {len(gaps)}")
        
        for i, gap in enumerate(gaps):
            equip_tag = gap["equipment"]["id"]
            reg_id = gap["regulation"]["id"]
            context_parts.append(
                f"\nGap {i+1}: Equipment '{equip_tag}' governed by '{reg_id}' has no linked safety/operating procedure."
            )
            
        context_parts.append("\nInspection & Audit Records:")
        inspections = graph.get_by_type(NodeType.DOCUMENT.value)
        for doc in inspections:
            if "inspection" in doc["id"].lower() or "audit" in doc["id"].lower() or "report" in doc["id"].lower():
                context_parts.append(f"- Document: {doc['name']}")
                context_parts.append(f"  Details: {doc.get('processing_notes', [])}")
                
        # Query details of V-045 which is critical
        v045_history = get_equipment_history("V-045")
        if v045_history.get("equipment"):
            context_parts.append("\nValve V-045 Detailed History:")
            for wo in v045_history["work_orders"]:
                context_parts.append(f"- WO: {wo['id']} Description: {wo.get('description')}")
            for doc in v045_history["documents"]:
                context_parts.append(f"- Document Mention: {doc['name']}")

        context = "\n".join(context_parts)
        
        # 3. Call Gemini
        try:
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not configured in .env")
                
            prompt = COMPLIANCE_PROMPT_TEMPLATE.format(context=context)
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Compliance Agent analysis failed: {e}")
            
            # Offline mock gap analysis response matching the V-045 fact
            return {
                "summary": "Coastal Refinery Unit-3 safety compliance review identifies two main gaps: slow response time on crude isolation valves and procedural gaps (Offline Mode).",
                "total_gaps": 2,
                "violations": [
                    {
                        "equipment_tag": "V-045",
                        "regulation": "OISD-STD-154",
                        "clause": "Clause 7.2.2",
                        "description": "V-045 emergency isolation valve response time of 8 seconds exceeds OISD standard limit of 5 seconds.",
                        "implication": "In case of emergency crude leakage or compressor trip, closing V-045 takes too long, exposing distillation columns to unisolated hydrocarbon feed lines.",
                        "severity": "CRITICAL",
                        "recommended_action": "Schedule immediate actuator repair, adjust pressure solenoid, and rebuild stem seal. Overhaul must be completed within 24 hours per Clause 7.2.3."
                    },
                    {
                        "equipment_tag": "P-104",
                        "regulation": "OISD-STD-154",
                        "clause": "Section 4.3",
                        "description": "Pump P-104 is missing a linked step-by-step Rotating Machinery Lockout/Tagout isolation procedure document.",
                        "implication": "Technicians performing coupling vibration checks may lack standardized energy isolation tags, causing compliance and physical safety risks.",
                        "severity": "HIGH",
                        "recommended_action": "Draft and link a specific Rotating Equipment Maintenance procedure complying with Section 4.3 Lockout protocols."
                    }
                ],
                "audit_score": 78.0
            }
        
        # Mock / fallback
        return {"status": "failed"}
