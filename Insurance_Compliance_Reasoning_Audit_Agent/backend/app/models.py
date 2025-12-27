import enum
from sqlalchemy import Column, String, DateTime, JSON, Enum, Text, Integer, event
from sqlalchemy.sql import func
from .database import Base


class WorkflowType(str, enum.Enum):
    CLAIM_PROCESSING = "CLAIM_PROCESSING"
    POLICY_ISSUANCE = "POLICY_ISSUANCE"
    DATA_ACCESS_REQUEST = "DATA_ACCESS_REQUEST"
    APPROVAL_ESCALATION = "APPROVAL_ESCALATION"

class RuleCategory(str, enum.Enum):
    PRIVACY = "PRIVACY"
    SECURITY = "SECURITY"
    OPERATIONAL = "OPERATIONAL"
    FINANCIAL = "FINANCIAL"

class RuleSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RuleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"

class DecisionOutcome(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, index=True, nullable=False)
    workflow_type = Column(Enum(WorkflowType), nullable=False)
    attributes = Column(JSON, nullable=False)
    actor_id = Column(String, nullable=False)
    source_system = Column(String, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, index=True, nullable=False)
    category = Column(Enum(RuleCategory), nullable=False)
    rule_text = Column(Text, nullable=False)
    severity = Column(Enum(RuleSeverity), nullable=False)
    version = Column(String, nullable=False)
    effective_from = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Enum(RuleStatus), default=RuleStatus.ACTIVE, nullable=False)

class StructuredRule(Base):
    __tablename__ = "structured_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    applicability_conditions = Column(JSON, nullable=False)
    obligations = Column(JSON, nullable=False)
    exceptions = Column(JSON, nullable=False)
    severity = Column(Enum(RuleSeverity), nullable=False)
    raw_ai_output = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ComplianceDecision(Base):
    __tablename__ = "compliance_decisions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, index=True, nullable=False)
    decision = Column(Enum(DecisionOutcome), nullable=False)
    violated_rules = Column(JSON, nullable=False) # List of rule_ids
    reasoning_trace = Column(JSON, nullable=False) # List of reasoning steps
    rule_versions = Column(JSON, nullable=False) # Map of rule_id to version
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(DateTime(timezone=True), server_default=func.now())


# Immutability Enforcement
def prevent_update(mapper, connection, target):
    raise Exception(f"Updates are not allowed on {target.__class__.__name__}")


def prevent_delete(mapper, connection, target):
    raise Exception(f"Deletions are not allowed on {target.__class__.__name__}")


# Register listeners for immutable models
for model in [WorkflowEvent, ComplianceDecision, StructuredRule]:
    event.listen(model, 'before_update', prevent_update)
    event.listen(model, 'before_delete', prevent_delete)
