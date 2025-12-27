from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List
from .models import (
    WorkflowType,
    RuleCategory,
    RuleSeverity,
    RuleStatus,
    DecisionOutcome
)


class WorkflowEventBase(BaseModel):
    workflow_id: str
    workflow_type: WorkflowType
    attributes: Dict[str, Any]
    actor_id: str
    source_system: str


class WorkflowEventCreate(WorkflowEventBase):
    pass


class WorkflowEvent(WorkflowEventBase):
    id: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class ComplianceRuleBase(BaseModel):
    rule_id: str
    category: RuleCategory
    rule_text: str
    severity: RuleSeverity
    version: str
    status: RuleStatus = RuleStatus.ACTIVE


class ComplianceRuleCreate(ComplianceRuleBase):
    effective_from: Optional[datetime] = None


class ComplianceRule(ComplianceRuleBase):
    id: int
    effective_from: datetime

    class Config:
        from_attributes = True


class StructuredRuleBase(BaseModel):
    rule_id: str
    version: str
    applicability_conditions: List[str]
    obligations: List[str]
    exceptions: List[str]
    severity: RuleSeverity


class StructuredRuleCreate(StructuredRuleBase):
    raw_ai_output: Optional[str] = None


class StructuredRule(StructuredRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceDecisionBase(BaseModel):
    workflow_id: str
    decision: DecisionOutcome
    violated_rules: List[str]
    reasoning_trace: List[Dict[str, Any]]
    rule_versions: Dict[str, str]


class ComplianceDecisionCreate(ComplianceDecisionBase):
    pass


class ComplianceDecision(ComplianceDecisionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class DashboardStats(BaseModel):
    total_audits: int
    compliance_stats: Dict[DecisionOutcome, int]
    recent_audits: List[ComplianceDecision]
    alerts: List[ComplianceDecision]


class SystemMetrics(BaseModel):
    ai_metrics: Dict[str, int]
    average_latency_ms: float
    rule_coverage: Dict[str, int]
    uptime_seconds: float

