import sys
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import ComplianceRule, RuleCategory, RuleSeverity, RuleStatus

def seed_rules():
    db = SessionLocal()
    try:
        rules = [
            ComplianceRule(
                rule_id="NYDFS-500.12",
                category=RuleCategory.SECURITY,
                rule_text="Multi-Factor Authentication must be implemented for any individual accessing the Covered Entity's internal networks from an external network.",
                severity=RuleSeverity.HIGH,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="NYDFS-500.17",
                category=RuleCategory.OPERATIONAL,
                rule_text="Each Covered Entity shall notify the Superintendent as promptly as possible but in no event later than 72 hours from a determination that a Cybersecurity Event has occurred.",
                severity=RuleSeverity.HIGH,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="HIPAA-164.502(b)",
                category=RuleCategory.PRIVACY,
                rule_text="When using or disclosing protected health information or when requesting protected health information from another covered entity, a covered entity must make reasonable efforts to limit protected health information to the minimum necessary to accomplish the intended purpose.",
                severity=RuleSeverity.MEDIUM,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="GLBA-313.4",
                category=RuleCategory.PRIVACY,
                rule_text="A financial institution must provide a clear and conspicuous notice that accurately reflects its privacy policies and practices to individuals who become the institution's customers.",
                severity=RuleSeverity.MEDIUM,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="NAIC-Claims-Ack",
                category=RuleCategory.OPERATIONAL,
                rule_text="Insurers must acknowledge receipt of a claim within 15 working days of receiving the claim notification.",
                severity=RuleSeverity.MEDIUM,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="NYDFS-500.11",
                category=RuleCategory.SECURITY,
                rule_text="Covered Entities must implement written policies and procedures designed to ensure the security of Information Systems and Nonpublic Information that are accessible to, or held by, Third Party Service Providers.",
                severity=RuleSeverity.HIGH,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="HIPAA-164.308(a)(1)",
                category=RuleCategory.SECURITY,
                rule_text="Conduct an accurate and thorough assessment of the potential risks and vulnerabilities to the confidentiality, integrity, and availability of electronic protected health information held by the covered entity.",
                severity=RuleSeverity.HIGH,
                version="1.0",
                status=RuleStatus.ACTIVE
            ),
            ComplianceRule(
                rule_id="GLBA-Safeguards",
                category=RuleCategory.SECURITY,
                rule_text="Develop, implement, and maintain a comprehensive information security program that contains administrative, technical, and physical safeguards appropriate to the entity's size and complexity.",
                severity=RuleSeverity.HIGH,
                version="1.0",
                status=RuleStatus.ACTIVE
            )
        ]

        for rule in rules:
            # Check if rule already exists
            existing = db.query(ComplianceRule).filter(ComplianceRule.rule_id == rule.rule_id).first()
            if not existing:
                db.add(rule)
                print(f"Adding rule: {rule.rule_id}")
            else:
                print(f"Rule {rule.rule_id} already exists, skipping.")
        
        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding rules: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_rules()
