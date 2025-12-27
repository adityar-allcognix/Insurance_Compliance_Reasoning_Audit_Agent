import os
os.environ["OPENAI_API_KEY"] = "sk-dummy"

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db, policy_interpreter
from app.database import Base
from app.models import RuleCategory, RuleSeverity, RuleStatus
from app.schemas import StructuredRuleCreate

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase2.db"

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

def test_create_rule_with_ai_interpretation():
    mock_structured_rule = StructuredRuleCreate(
        rule_id="rule-001",
        version="1.0",
        applicability_conditions=["claim_amount > 5000"],
        obligations=["require_manager_approval"],
        exceptions=["emergency_claims"],
        severity=RuleSeverity.HIGH,
        raw_ai_output="Mocked AI Output"
    )
    
    with patch.object(policy_interpreter, 'interpret', return_value=mock_structured_rule):
        response = client.post(
            "/rules/",
            json={
                "rule_id": "rule-001",
                "category": "OPERATIONAL",
                "rule_text": "Claims over 5000 require manager approval except for emergencies.",
                "severity": "HIGH",
                "version": "1.0",
                "status": "ACTIVE"
            },
        )
        assert response.status_code == 201
        
        # Check if structured rule was created
        response_structured = client.get("/rules/rule-001/structured")
        assert response_structured.status_code == 200
        structured_data = response_structured.json()
        assert len(structured_data) == 1
        assert structured_data[0]["obligations"] == ["require_manager_approval"]

def test_create_rule_ai_failure_blocks_deployment():
    with patch.object(policy_interpreter, 'interpret', side_effect=Exception("AI Error")):
        response = client.post(
            "/rules/",
            json={
                "rule_id": "rule-error",
                "category": "OPERATIONAL",
                "rule_text": "This rule will fail interpretation.",
                "severity": "LOW",
                "version": "1.0",
                "status": "ACTIVE"
            },
        )
        assert response.status_code == 422
        assert "interpretation failed" in response.json()["detail"]
        
        # Verify rule was not saved (rolled back)
        response_check = client.get("/rules/rule-error")
        assert response_check.status_code == 404
