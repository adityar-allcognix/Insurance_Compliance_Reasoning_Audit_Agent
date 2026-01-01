import os
import sys
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import models, database, schemas

def seed_workflows():
    db = database.SessionLocal()
    try:
        # Clear existing workflows to avoid duplicates if needed, 
        # but here we just add new ones.
        
        workflows = [
            {
                "workflow_id": "WF-001",
                "workflow_type": models.WorkflowType.CLAIM_PROCESSING,
                "actor_id": "agent_smith",
                "source_system": "claims_portal_v2",
                "attributes": {
                    "claim_id": "CLM-101",
                    "submission_date": (datetime.now() - timedelta(days=2)).isoformat(),
                    "acknowledgment_sent": True,
                    "acknowledgment_date": (datetime.now() - timedelta(days=1)).isoformat(),
                    "description": "Standard auto glass claim."
                }
            },
            {
                "workflow_id": "WF-002",
                "workflow_type": models.WorkflowType.CLAIM_PROCESSING,
                "actor_id": "agent_jones",
                "source_system": "claims_portal_v2",
                "attributes": {
                    "claim_id": "CLM-102",
                    "submission_date": (datetime.now() - timedelta(days=20)).isoformat(),
                    "acknowledgment_sent": False,
                    "description": "Delayed property damage claim."
                }
            },
            {
                "workflow_id": "WF-003",
                "workflow_type": models.WorkflowType.DATA_ACCESS_REQUEST,
                "actor_id": "remote_user_01",
                "source_system": "vpn_gateway",
                "attributes": {
                    "access_type": "external",
                    "network_segment": "internal_prod",
                    "mfa_used": True,
                    "mfa_method": "TOTP",
                    "ip_address": "192.168.1.50"
                }
            },
            {
                "workflow_id": "WF-004",
                "workflow_type": models.WorkflowType.DATA_ACCESS_REQUEST,
                "actor_id": "remote_user_02",
                "source_system": "vpn_gateway",
                "attributes": {
                    "access_type": "external",
                    "network_segment": "internal_prod",
                    "mfa_used": False,
                    "ip_address": "203.0.113.5"
                }
            },
            {
                "workflow_id": "WF-005",
                "workflow_type": models.WorkflowType.POLICY_ISSUANCE,
                "actor_id": "underwriter_01",
                "source_system": "policy_admin_system",
                "attributes": {
                    "customer_id": "CUST-5001",
                    "is_new_customer": True,
                    "privacy_notice_provided": True,
                    "notice_delivery_method": "email",
                    "policy_type": "LIFE"
                }
            },
            {
                "workflow_id": "WF-006",
                "workflow_type": models.WorkflowType.POLICY_ISSUANCE,
                "actor_id": "underwriter_02",
                "source_system": "policy_admin_system",
                "attributes": {
                    "customer_id": "CUST-5002",
                    "is_new_customer": True,
                    "privacy_notice_provided": False,
                    "policy_type": "HEALTH"
                }
            },
            {
                "workflow_id": "WF-007",
                "workflow_type": models.WorkflowType.DATA_ACCESS_REQUEST,
                "actor_id": "nurse_joy",
                "source_system": "ehr_system",
                "attributes": {
                    "data_type": "PHI",
                    "purpose": "treatment",
                    "fields_accessed": ["patient_name", "current_medications"],
                    "limit_to_minimum_necessary": True
                }
            },
            {
                "workflow_id": "WF-008",
                "workflow_type": models.WorkflowType.DATA_ACCESS_REQUEST,
                "actor_id": "billing_clerk_01",
                "source_system": "ehr_system",
                "attributes": {
                    "data_type": "PHI",
                    "purpose": "billing_query",
                    "fields_accessed": ["full_medical_history", "genetic_data", "psych_notes"],
                    "limit_to_minimum_necessary": False
                }
            },
            {
                "workflow_id": "WF-009",
                "workflow_type": models.WorkflowType.APPROVAL_ESCALATION,
                "actor_id": "ciso_admin",
                "source_system": "siem_alert",
                "attributes": {
                    "event_type": "Cybersecurity Event",
                    "determination_time": (datetime.now() - timedelta(hours=24)).isoformat(),
                    "notification_sent_to_superintendent": True,
                    "notification_time": (datetime.now() - timedelta(hours=2)).isoformat()
                }
            },
            {
                "workflow_id": "WF-010",
                "workflow_type": models.WorkflowType.APPROVAL_ESCALATION,
                "actor_id": "it_staff_01",
                "source_system": "siem_alert",
                "attributes": {
                    "event_type": "Cybersecurity Event",
                    "determination_time": (datetime.now() - timedelta(hours=100)).isoformat(),
                    "notification_sent_to_superintendent": True,
                    "notification_time": (datetime.now() - timedelta(hours=1)).isoformat()
                }
            }
        ]

        for wf_data in workflows:
            # Check if exists
            existing = db.query(models.WorkflowEvent).filter(
                models.WorkflowEvent.workflow_id == wf_data["workflow_id"]
            ).first()
            if not existing:
                db_wf = models.WorkflowEvent(**wf_data)
                db.add(db_wf)
                print(f"Created workflow: {wf_data['workflow_id']}")
            else:
                print(f"Workflow {wf_data['workflow_id']} already exists, skipping.")
        
        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding workflows: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_workflows()
