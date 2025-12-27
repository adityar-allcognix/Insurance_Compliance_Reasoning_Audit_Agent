# AI-Assisted Insurance Compliance & Audit System

This system provides an automated, AI-driven platform for monitoring insurance workflows against regulatory compliance rules. It features structured reasoning, deterministic decision-making, and immutable audit trails.

## Core Features
- **AI Rule Interpretation**: Automatically converts human-readable policies into machine-evaluable constraints.
- **Multi-Step Reasoning**: AI agents evaluate workflows using a strict protocol (Applicability, Conditions, Obligations, Exceptions).
- **Deterministic Decision Engine**: Aggregates AI findings into final compliance outcomes based on rule severity.
- **Immutable Audit Trail**: All workflow events and compliance decisions are append-only at the database level.
- **Audit Replay**: Re-evaluate past events using the exact rule versions active at the time of the original audit.

## Rule Authoring Methodology
Rules are authored in natural language by compliance officers. The system follows a versioned lifecycle:
1. **Drafting**: Human-readable text is submitted via the API/UI.
2. **Interpretation**: The `PolicyInterpreterAgent` (LLM-based) breaks the rule into structured components.
3. **Validation**: The structured rule is stored with a version number and linked to the original text.
4. **Activation**: Only `ACTIVE` rules are used in audits.

## Workflow Provenance
Every audit decision is linked to:
- A specific **Workflow Event** (immutable).
- A set of **Structured Rules** with specific versions.
- A **Reasoning Trace** providing step-by-step justification for the decision.
- The **Actor** and **Source System** that triggered the event.

## Getting Started (Docker)
To run the entire stack using Docker:
```bash
docker-compose up --build
```
The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

## Development Setup
### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. `export OPENAI_API_KEY=your_key`
4. `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Testing
Run the hardening and logic tests:
```bash
cd backend
pytest tests/test_hardening.py
```
Run the end-to-end verification:
```bash
cd backend
python3 test_e2e.py
```
