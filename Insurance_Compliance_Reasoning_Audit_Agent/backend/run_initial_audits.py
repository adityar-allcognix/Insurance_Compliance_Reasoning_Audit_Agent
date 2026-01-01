import os
import sys
import requests
import json

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import models, database

def run_audits():
    db = database.SessionLocal()
    try:
        # Get all workflows
        workflows = db.query(models.WorkflowEvent).all()
        print(f"Found {len(workflows)} workflows to audit.")

        # We need a token to call the audit endpoint if we use requests, 
        # or we can call the logic directly.
        # Calling the logic directly is easier for a script.
        
        from app.main import audit_workflow
        from unittest.mock import MagicMock

        # Mock current_user
        mock_user = MagicMock()
        
        for wf in workflows:
            print(f"Auditing workflow: {wf.workflow_id}...")
            try:
                # Call the audit function directly
                # Note: audit_workflow is a FastAPI endpoint, so we pass dependencies
                decision = audit_workflow(
                    workflow_id=wf.workflow_id,
                    db=db,
                    current_user=mock_user
                )
                print(f"Result for {wf.workflow_id}: {decision.decision}")
            except Exception as e:
                print(f"Error auditing {wf.workflow_id}: {e}")

        print("All audits completed.")
    finally:
        db.close()

if __name__ == "__main__":
    run_audits()
