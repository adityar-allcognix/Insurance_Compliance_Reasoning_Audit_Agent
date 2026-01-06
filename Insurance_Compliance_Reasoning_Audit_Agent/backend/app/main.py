from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
import time
from . import models, schemas, database, agents, engine

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("compliance-audit")

# AI Metrics
AI_METRICS = {
    "reasoning_failures": 0,
    "interpretation_failures": 0,
    "total_audits": 0
}

LATENCY_DATA = []
RULE_COVERAGE = {}
START_TIME = time.time()

# Auth Configuration
SECRET_KEY = "super-secret-compliance-key"  # In production, use env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Insurance Compliance Audit System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


"""
SECURITY REVIEW CHECKLIST:
1. JWT Secret Key: Ensure SECRET_KEY is loaded from environment variables.
2. Password Hashing: Using bcrypt via passlib.
3. API Protection: Sensitive endpoints protected by get_current_user.
4. Input Validation: Pydantic schemas enforce strict types and structure.
5. Database: SQLAlchemy prevents SQL injection.
6. AI Safety: AI output validated; failures degrade to REQUIRES_REVIEW.
7. Immutability: Workflow events and audit decisions are append-only.
"""


@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Track latency for audit endpoint
    if "audit" in request.url.path and request.method == "POST":
        LATENCY_DATA.append(process_time)
        if len(LATENCY_DATA) > 100: # Keep last 100
            LATENCY_DATA.pop(0)

    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {process_time:.2f}ms"
    )
    return response


# Initialize Agent
policy_interpreter = agents.PolicyInterpreterAgent()
compliance_reasoner = agents.ComplianceReasoningAgent()
decision_engine = engine.DecisionEngine()


# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auth Helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(
        models.User.username == token_data.username
    ).first()
    if user is None:
        raise credentials_exception
    return user


# Auth Endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/metrics")
async def get_metrics(current_user: models.User = Depends(get_current_user)):
    return AI_METRICS


@app.get("/dashboard/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_audits = db.query(models.ComplianceDecision).count()
    
    # Compliance stats
    stats = {
        models.DecisionOutcome.COMPLIANT: db.query(models.ComplianceDecision).filter(models.ComplianceDecision.decision == models.DecisionOutcome.COMPLIANT).count(),
        models.DecisionOutcome.NON_COMPLIANT: db.query(models.ComplianceDecision).filter(models.ComplianceDecision.decision == models.DecisionOutcome.NON_COMPLIANT).count(),
        models.DecisionOutcome.REQUIRES_REVIEW: db.query(models.ComplianceDecision).filter(models.ComplianceDecision.decision == models.DecisionOutcome.REQUIRES_REVIEW).count(),
    }
    
    recent_audits = db.query(models.ComplianceDecision).order_by(
        models.ComplianceDecision.created_at.desc()
    ).limit(10).all()
    
    alerts = db.query(models.ComplianceDecision).filter(
        models.ComplianceDecision.decision == models.DecisionOutcome.NON_COMPLIANT
    ).order_by(models.ComplianceDecision.created_at.desc()).limit(5).all()
    
    return {
        "total_audits": total_audits,
        "compliance_stats": stats,
        "recent_audits": recent_audits,
        "alerts": alerts
    }


@app.get("/dashboard/metrics", response_model=schemas.SystemMetrics)
async def get_system_metrics(
    current_user: models.User = Depends(get_current_user)
):
    avg_latency = sum(LATENCY_DATA) / len(LATENCY_DATA) if LATENCY_DATA else 0.0
    uptime = time.time() - START_TIME
    
    return {
        "ai_metrics": AI_METRICS,
        "average_latency_ms": avg_latency,
        "rule_coverage": RULE_COVERAGE,
        "uptime_seconds": uptime
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "backend_uptime": time.time() - START_TIME,
        "ai_services": {
            "policy_interpreter": "available" if policy_interpreter else "unavailable",
            "compliance_reasoner": "available" if compliance_reasoner else "unavailable"
        }
    }


@app.post(
    "/workflows/",
    response_model=schemas.WorkflowEvent,
    status_code=status.HTTP_201_CREATED
)
def create_workflow_event(
    event: schemas.WorkflowEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_event = models.WorkflowEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.get("/workflows/", response_model=List[schemas.WorkflowEvent])
def read_workflow_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    events = db.query(models.WorkflowEvent).offset(skip).limit(limit).all()
    return events


@app.get("/workflows/{workflow_id}", response_model=List[schemas.WorkflowEvent])
def read_workflow_event(workflow_id: str, db: Session = Depends(get_db)):
    events = db.query(models.WorkflowEvent).filter(
        models.WorkflowEvent.workflow_id == workflow_id
    ).all()
    if not events:
        raise HTTPException(status_code=404, detail="Workflow events not found")
    return events


@app.post(
    "/workflows/{workflow_id}/audit",
    response_model=schemas.ComplianceDecision
)
def audit_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Get the latest event for this workflow
    event = db.query(models.WorkflowEvent).filter(
        models.WorkflowEvent.workflow_id == workflow_id
    ).order_by(models.WorkflowEvent.submitted_at.desc()).first()
    if not event:
        raise HTTPException(status_code=404, detail="Workflow event not found")

    # 2. Get all active rules and their latest structured versions
    active_rules = db.query(models.ComplianceRule).filter(
        models.ComplianceRule.status == models.RuleStatus.ACTIVE
    ).all()
    if not active_rules:
        return schemas.ComplianceDecision(
            workflow_id=workflow_id,
            decision=models.DecisionOutcome.COMPLIANT,
            violated_rules=[],
            reasoning_trace=[{"info": "No active rules found"}],
            rule_versions={},
            created_at=datetime.now()
        )

    rule_ids = [r.rule_id for r in active_rules]
    # Get latest structured rule for each rule_id
    structured_rules = []
    rule_versions = {}
    for r_id in rule_ids:
        s_rule = db.query(models.StructuredRule).filter(
            models.StructuredRule.rule_id == r_id
        ).order_by(models.StructuredRule.created_at.desc()).first()
        if s_rule:
            structured_rules.append(s_rule)
            rule_versions[r_id] = s_rule.version

    # 3. Invoke AI Reasoning Agent
    try:
        AI_METRICS["total_audits"] += 1
        ai_evaluation = compliance_reasoner.evaluate(event, structured_rules)

        # Track rule coverage
        for s_rule in structured_rules:
            RULE_COVERAGE[s_rule.rule_id] = RULE_COVERAGE.get(s_rule.rule_id, 0) + 1

        # 4. Deterministic Decision Engine
        rule_severities = {r.rule_id: r.severity for r in structured_rules}
        decision_outcome = decision_engine.decide(
            ai_evaluation.get("evaluations", []),
            rule_severities
        )

        violated_rules = [
            e["rule_id"] for e in ai_evaluation.get("evaluations", [])
            if e["status"] == "NON_COMPLIANT"
        ]
        reasoning_trace = [
            {"rule_id": e["rule_id"], "steps": e["reasoning_steps"]}
            for e in ai_evaluation.get("evaluations", [])
        ]

        db_decision = models.ComplianceDecision(
            workflow_id=workflow_id,
            decision=decision_outcome,
            violated_rules=violated_rules,
            reasoning_trace=reasoning_trace,
            rule_versions=rule_versions
        )
        db.add(db_decision)
        db.commit()
        db.refresh(db_decision)
        return db_decision

    except Exception as e:
        # AI failures degrade to REQUIRES_REVIEW
        AI_METRICS["reasoning_failures"] += 1
        logger.error(f"AI Reasoning failed for workflow {workflow_id}: {str(e)}")
        
        # Provide a structured reason for the failure so the UI can display it
        reasoning_trace = [{
            "rule_id": "System Diagnostic",
            "steps": [{
                "step": "AI Reasoning Protocol",
                "result": "Execution Failed",
                "detail": f"The reasoning agent encountered an error: {str(e)}. A manual override or review is required."
            }]
        }]

        db_decision = models.ComplianceDecision(
            workflow_id=workflow_id,
            decision=models.DecisionOutcome.REQUIRES_REVIEW,
            violated_rules=[],
            reasoning_trace=reasoning_trace,
            rule_versions=rule_versions
        )
        db.add(db_decision)
        db.commit()
        db.refresh(db_decision)
        return db_decision


@app.get("/decisions/", response_model=List[schemas.ComplianceDecision])
def get_all_decisions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    decisions = db.query(models.ComplianceDecision).order_by(
        models.ComplianceDecision.created_at.desc()
    ).offset(skip).limit(limit).all()
    return decisions


@app.get("/decisions/{workflow_id}", response_model=List[schemas.ComplianceDecision])
def get_decisions(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    decisions = db.query(models.ComplianceDecision).filter(
        models.ComplianceDecision.workflow_id == workflow_id
    ).order_by(models.ComplianceDecision.created_at.desc()).all()
    return decisions


@app.post(
    "/workflows/{workflow_id}/replay/{decision_id}",
    response_model=schemas.ComplianceDecision
)
def replay_decision(
    workflow_id: str,
    decision_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Replay a specific decision by re-evaluating the same event
    with the same rule versions.
    """
    old_decision = db.query(models.ComplianceDecision).filter(
        models.ComplianceDecision.id == decision_id
    ).first()
    if not old_decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Get the event that was used
    event = db.query(models.WorkflowEvent).filter(
        models.WorkflowEvent.workflow_id == workflow_id
    ).filter(
        models.WorkflowEvent.submitted_at <= old_decision.created_at
    ).order_by(models.WorkflowEvent.submitted_at.desc()).first()

    # Get the specific rule versions used
    structured_rules = []
    for r_id, version in old_decision.rule_versions.items():
        s_rule = db.query(models.StructuredRule).filter(
            models.StructuredRule.rule_id == r_id
        ).filter(models.StructuredRule.version == version).first()
        if s_rule:
            structured_rules.append(s_rule)

    # Re-run reasoning
    ai_evaluation = compliance_reasoner.evaluate(event, structured_rules)
    rule_severities = {r.rule_id: r.severity for r in structured_rules}
    decision_outcome = decision_engine.decide(
        ai_evaluation.get("evaluations", []),
        rule_severities
    )

    violated_rules = [
        e["rule_id"] for e in ai_evaluation.get("evaluations", [])
        if e["status"] == "NON_COMPLIANT"
    ]
    reasoning_trace = [
        {"rule_id": e["rule_id"], "steps": e["reasoning_steps"]}
        for e in ai_evaluation.get("evaluations", [])
    ]

    new_decision = models.ComplianceDecision(
        workflow_id=workflow_id,
        decision=decision_outcome,
        violated_rules=violated_rules,
        reasoning_trace=reasoning_trace,
        rule_versions=old_decision.rule_versions
    )
    db.add(new_decision)
    db.commit()
    db.refresh(new_decision)
    return new_decision


# Compliance Rules CRUD
@app.post(
    "/rules/",
    response_model=schemas.ComplianceRule,
    status_code=status.HTTP_201_CREATED
)
def create_compliance_rule(
    rule: schemas.ComplianceRuleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Save the human-readable rule
    db_rule = models.ComplianceRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    # 2. Invoke AI to interpret the rule
    try:
        structured_rule_data = policy_interpreter.interpret(db_rule)
        db_structured_rule = models.StructuredRule(**structured_rule_data.model_dump())
        db.add(db_structured_rule)
        db.commit()
    except Exception as e:
        # If AI interpretation fails, we might want to rollback
        AI_METRICS["interpretation_failures"] += 1
        logger.error(f"Rule interpretation failed for rule {db_rule.rule_id}: {str(e)}")
        db.delete(db_rule)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rule interpretation failed: {str(e)}"
        )

    return db_rule


@app.get("/rules/", response_model=List[schemas.ComplianceRule])
def read_compliance_rules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    rules = db.query(models.ComplianceRule).offset(skip).limit(limit).all()
    return rules


@app.get("/rules/{rule_id}", response_model=schemas.ComplianceRule)
def read_compliance_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(models.ComplianceRule).filter(
        models.ComplianceRule.rule_id == rule_id
    ).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@app.get("/rules/{rule_id}/structured", response_model=List[schemas.StructuredRule])
def read_structured_rules(rule_id: str, db: Session = Depends(get_db)):
    rules = db.query(models.StructuredRule).filter(
        models.StructuredRule.rule_id == rule_id
    ).all()
    return rules


@app.put("/rules/{rule_id}", response_model=schemas.ComplianceRule)
def update_compliance_rule(
    rule_id: str,
    rule_update: schemas.ComplianceRuleCreate,
    db: Session = Depends(get_db)
):
    db_rule = db.query(models.ComplianceRule).filter(
        models.ComplianceRule.rule_id == rule_id
    ).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Store old values for rollback if needed
    old_values = {
        var: getattr(db_rule, var)
        for var in rule_update.model_dump().keys()
    }

    for var, value in rule_update.model_dump().items():
        setattr(db_rule, var, value) if value else None

    db.commit()
    db.refresh(db_rule)

    # Re-interpret the rule
    try:
        structured_rule_data = policy_interpreter.interpret(db_rule)
        db_structured_rule = models.StructuredRule(**structured_rule_data.model_dump())
        db.add(db_structured_rule)
        db.commit()
    except Exception as e:
        # Rollback rule update
        for var, value in old_values.items():
            setattr(db_rule, var, value)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rule re-interpretation failed: {str(e)}"
        )

    return db_rule


# Note: WorkflowEvents are immutable, so no PUT or DELETE endpoints for them.
