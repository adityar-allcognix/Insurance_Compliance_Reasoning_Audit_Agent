import os
os.environ["OPENAI_API_KEY"] = "sk-dummy"

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db, compliance_reasoner, policy_interpreter
from app.database import Base
from app.models import RuleCategory, RuleSeverity, RuleStatus, DecisionOutcome
from app.schemas import StructuredRuleCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase4.db"

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

def test_decision_engine_logic():
    from app.engine import DecisionEngine
    from app.models import RuleSeverity, DecisionOutcome
    
    # Test compliant
    evals = [{"rule_id": "r1", "status": "COMPLIANT"}]
    sevs = {"r1": RuleSeverity.HIGH}
    assert DecisionEngine.decide(evals, sevs) == DecisionOutcome.COMPLIANT
    
    # Test non-compliant
    evals = [{"rule_id": "r1", "status": "NON_COMPLIANT"}]
    sevs = {"r1": RuleSeverity.HIGH}
    assert DecisionEngine.decide(evals, sevs) == DecisionOutcome.NON_COMPLIANT

def test_replay_capability():
    # 1. Setup rule and event
    mock_structured_rule = StructuredRuleCreate(
        rule_id="rule-001",
        version="1.0",
        applicability_conditions=[],
        obligations=[],
        exceptions=[],
        severity=RuleSeverity.HIGH,
        raw_ai_output="Mocked AI Output"
    )
    with patch.object(policy_interpreter, 'interpret', return_value=mock_structured_rule):
        client.post("/rules/", json={
            "rule_id": "rule-001",
            "category": "OPERATIONAL",
            "rule_text": "Rule 1",
            "severity": "HIGH",
            "version": "1.0",
            "status": "ACTIVE"
        })

    client.post("/workflows/", json={
        "workflow_id": "wf-replay",
        "workflow_type": "CLAIM_PROCESSING",
        "attributes": {},
        "actor_id": "user-1",
        "source_system": "portal"
    })

    # 2. First audit
    mock_ai_eval = {
        "workflow_id": "wf-replay",
        "evaluations": [{"rule_id": "rule-001", "status": "COMPLIANT", "reasoning_steps": []}]
    }
    with patch.object(compliance_reasoner, 'evaluate', return_value=mock_ai_eval):
        response = client.post("/workflows/wf-replay/audit")
        decision_id = response.json()["id"]

    # 3. Replay
    with patch.object(compliance_reasoner, 'evaluate', return_value=mock_ai_eval):
        response_replay = client.post(f"/workflows/wf-replay/replay/{decision_id}")
        assert response_replay.status_code == 200
        assert response_replay.json()["decision"] == "COMPLIANT"
        assert response_replay.json()["rule_versions"] == {"rule-001": "1.0"}
