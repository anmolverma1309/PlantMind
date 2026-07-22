"""Specialist agent endpoints (RCA, Compliance, Lessons-Learned)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from agents.rca_agent import RCAAgent
from agents.compliance_agent import ComplianceAgent
from agents.lessons_learned_agent import LessonsLearnedAgent

router = APIRouter()


class RCARequest(BaseModel):
    equipment_tag: str


class RCABasicResponse(BaseModel):
    equipment_tag: str
    findings_summary: str
    recurring_failure_modes: List[Dict[str, Any]]
    root_cause_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    safety_risk_score: float


class ComplianceResponse(BaseModel):
    summary: str
    total_gaps: int
    violations: List[Dict[str, Any]]
    audit_score: float


class LessonsResponse(BaseModel):
    alerts_count: int
    lessons: List[Dict[str, Any]]


@router.post("/agents/rca", response_model=RCABasicResponse)
async def run_rca_agent(request: RCARequest):
    """Run root cause analysis for a specific equipment tag."""
    agent = RCAAgent()
    result = await agent.analyze(request.equipment_tag)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/agents/compliance", response_model=ComplianceResponse)
async def run_compliance_agent():
    """Run compliance gap audit across all assets and regulations."""
    agent = ComplianceAgent()
    result = await agent.analyze()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/agents/lessons", response_model=LessonsResponse)
async def run_lessons_agent():
    """Scan the asset history to extract lessons learned and proactive alerts."""
    agent = LessonsLearnedAgent()
    result = await agent.analyze()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
