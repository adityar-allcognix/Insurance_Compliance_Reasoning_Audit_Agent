import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.engine import DecisionEngine
from app.models import DecisionOutcome, RuleSeverity, WorkflowEvent, WorkflowType, ComplianceDecision

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_hardening.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_decision_engine_compliant():
    evals = [
        {"rule_id": "R1", "status": "COMPLIANT"},
        {"rule_id": "R2", "status": "COMPLIANT"}
    ]
    severities = {"R1": RuleSeverity.LOW, "R2": RuleSeverity.HIGH}
    decision = DecisionEngine.decide(evals, severities)
    assert decision == DecisionOutcome.COMPLIANT

def test_decision_engine_non_compliant_high():
    evals = [
        {"rule_id": "R1", "status": "NON_COMPLIANT"},
        {"rule_id": "R2", "status": "COMPLIANT"}
    ]
    severities = {"R1": RuleSeverity.HIGH, "R2": RuleSeverity.LOW}
    decision = DecisionEngine.decide(evals, severities)
    assert decision == DecisionOutcome.NON_COMPLIANT

def test_decision_engine_empty():
    decision = DecisionEngine.decide([], {})
    assert decision == DecisionOutcome.COMPLIANT

def test_immutability_workflow_event(db_session):
    from app.models import WorkflowEvent, WorkflowType
    event = WorkflowEvent(
        workflow_id="IMMUTABLE-1",
        workflow_type=WorkflowType.CLAIM_PROCESSING,
        attributes={},
        actor_id="test",
        source_system="test"
    )
    db_session.add(event)
    db_session.commit()
    
    event.actor_id = "changed"
    with pytest.raises(Exception) as excinfo:
        db_session.commit()
    assert "Updates are not allowed on WorkflowEvent" in str(excinfo.value)
    db_session.rollback()

def test_immutability_decision(db_session):
    from app.models import ComplianceDecision, DecisionOutcome
    decision = ComplianceDecision(
        workflow_id="IMMUTABLE-2",
        decision=DecisionOutcome.COMPLIANT,
        violated_rules=[],
        reasoning_trace=[],
        rule_versions={}
    )
    db_session.add(decision)
    db_session.commit()
    
    with pytest.raises(Exception) as excinfo:
        db_session.delete(decision)
        db_session.commit()
    assert "Deletions are not allowed on ComplianceDecision" in str(excinfo.value)
    db_session.rollback()
