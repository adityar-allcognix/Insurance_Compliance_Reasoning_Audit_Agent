import os
os.environ["OPENAI_API_KEY"] = "sk-dummy"

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db, compliance_reasoner, policy_interpreter
from app.database import Base
from app.models import RuleCategory, RuleSeverity, RuleStatus, DecisionOutcome, WorkflowType
from app.schemas import StructuredRuleCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase3.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_audit_workflow_compliant():
    # 1. Create a rule
    mock_structured_rule = StructuredRuleCreate(
        rule_id="rule-001",
        version="1.0",
        applicability_conditions=["claim_amount > 5000"],
        obligations=["require_manager_approval"],
        exceptions=[],
        severity=RuleSeverity.HIGH,
        raw_ai_output="Mocked AI Output"
    )
    
    with patch.object(policy_interpreter, 'interpret', return_value=mock_structured_rule):
        client.post("/rules/", json={
            "rule_id": "rule-001",
            "category": "OPERATIONAL",
            "rule_text": "Claims over 5000 require manager approval.",
            "severity": "HIGH",
            "version": "1.0",
            "status": "ACTIVE"
        })

    # 2. Create a workflow event (compliant because amount < 5000)
    client.post("/workflows/", json={
        "workflow_id": "wf-compliant",
        "workflow_type": "CLAIM_PROCESSING",
        "attributes": {"claim_amount": 1000},
        "actor_id": "user-1",
        "source_system": "portal"
    })

    # 3. Mock AI Reasoning
    mock_ai_eval = {
        "workflow_id": "wf-compliant",
        "evaluations": [
            {
                "rule_id": "rule-001",
                "status": "COMPLIANT",
                "reasoning_steps": [{"step": "Applicability Check", "result": "NOT_APPLICABLE", "detail": "Amount 1000 <= 5000"}]
            }
        ]
    }

    with patch.object(compliance_reasoner, 'evaluate', return_value=mock_ai_eval):
        response = client.post("/workflows/wf-compliant/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "COMPLIANT"
        assert len(data["violated_rules"]) == 0

def test_audit_workflow_non_compliant():
    # 1. Create a rule
    mock_structured_rule = StructuredRuleCreate(
        rule_id="rule-001",
        version="1.0",
        applicability_conditions=["claim_amount > 5000"],
        obligations=["require_manager_approval"],
        exceptions=[],
        severity=RuleSeverity.HIGH,
        raw_ai_output="Mocked AI Output"
    )
    
    with patch.object(policy_interpreter, 'interpret', return_value=mock_structured_rule):
        client.post("/rules/", json={
            "rule_id": "rule-001",
            "category": "OPERATIONAL",
            "rule_text": "Claims over 5000 require manager approval.",
            "severity": "HIGH",
            "version": "1.0",
            "status": "ACTIVE"
        })

    # 2. Create a workflow event (non-compliant because amount > 5000 and no approval)
    client.post("/workflows/", json={
        "workflow_id": "wf-non-compliant",
        "workflow_type": "CLAIM_PROCESSING",
        "attributes": {"claim_amount": 6000},
        "actor_id": "user-1",
        "source_system": "portal"
    })

    # 3. Mock AI Reasoning
    mock_ai_eval = {
        "workflow_id": "wf-non-compliant",
        "evaluations": [
            {
                "rule_id": "rule-001",
                "status": "NON_COMPLIANT",
                "reasoning_steps": [{"step": "Violation Detection", "result": "VIOLATION", "detail": "No manager approval found for 6000"}]
            }
        ]
    }

    with patch.object(compliance_reasoner, 'evaluate', return_value=mock_ai_eval):
        response = client.post("/workflows/wf-non-compliant/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "NON_COMPLIANT"
        assert "rule-001" in data["violated_rules"]

def test_audit_ai_failure_degrades_to_review():
    # Create event
    client.post("/workflows/", json={
        "workflow_id": "wf-fail",
        "workflow_type": "CLAIM_PROCESSING",
        "attributes": {"claim_amount": 1000},
        "actor_id": "user-1",
        "source_system": "portal"
    })
    
    # Create rule
    mock_structured_rule = StructuredRuleCreate(
        rule_id="rule-001",
        version="1.0",
        applicability_conditions=[],
        obligations=[],
        exceptions=[],
        severity=RuleSeverity.LOW,
        raw_ai_output="Mocked AI Output"
    )
    with patch.object(policy_interpreter, 'interpret', return_value=mock_structured_rule):
        client.post("/rules/", json={
            "rule_id": "rule-001",
            "category": "OPERATIONAL",
            "rule_text": "Some rule",
            "severity": "LOW",
            "version": "1.0",
            "status": "ACTIVE"
        })

    with patch.object(compliance_reasoner, 'evaluate', side_effect=Exception("AI Error")):
        response = client.post("/workflows/wf-fail/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "REQUIRES_REVIEW"
