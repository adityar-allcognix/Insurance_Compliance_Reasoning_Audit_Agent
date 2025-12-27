import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.database import Base
from app.models import WorkflowType, RuleCategory, RuleSeverity, RuleStatus

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

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

def test_create_workflow_event():
    response = client.post(
        "/workflows/",
        json={
            "workflow_id": "wf-123",
            "workflow_type": "CLAIM_PROCESSING",
            "attributes": {"claim_amount": 1000, "policy_id": "pol-456"},
            "actor_id": "user-789",
            "source_system": "claims-portal"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["workflow_id"] == "wf-123"
    assert "id" in data
    assert "submitted_at" in data

def test_workflow_event_immutability():
    # Create an event
    client.post(
        "/workflows/",
        json={
            "workflow_id": "wf-123",
            "workflow_type": "CLAIM_PROCESSING",
            "attributes": {"claim_amount": 1000},
            "actor_id": "user-789",
            "source_system": "claims-portal"
        },
    )
    
    # Try to update (should fail as no endpoint exists)
    response = client.put("/workflows/wf-123", json={"attributes": {"claim_amount": 2000}})
    assert response.status_code == 405 # Method Not Allowed

    # Try to delete (should fail as no endpoint exists)
    response = client.delete("/workflows/wf-123")
    assert response.status_code == 405 # Method Not Allowed

def test_create_compliance_rule():
    response = client.post(
        "/rules/",
        json={
            "rule_id": "rule-001",
            "category": "PRIVACY",
            "rule_text": "All PII must be encrypted.",
            "severity": "HIGH",
            "version": "1.0",
            "status": "ACTIVE"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rule_id"] == "rule-001"
    assert data["category"] == "PRIVACY"

def test_update_compliance_rule():
    # Create a rule
    client.post(
        "/rules/",
        json={
            "rule_id": "rule-001",
            "category": "PRIVACY",
            "rule_text": "All PII must be encrypted.",
            "severity": "HIGH",
            "version": "1.0",
            "status": "ACTIVE"
        },
    )
    
    # Update the rule
    response = client.put(
        "/rules/rule-001",
        json={
            "rule_id": "rule-001",
            "category": "PRIVACY",
            "rule_text": "All PII must be encrypted and masked.",
            "severity": "HIGH",
            "version": "1.1",
            "status": "ACTIVE"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1"
    assert "masked" in data["rule_text"]
