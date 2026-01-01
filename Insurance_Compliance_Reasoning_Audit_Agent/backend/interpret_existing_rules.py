import sys
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ComplianceRule, StructuredRule
from app.agents import PolicyInterpreterAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interpret-rules")

def interpret_rules():
    db = SessionLocal()
    interpreter = PolicyInterpreterAgent()
    try:
        rules = db.query(ComplianceRule).all()
        for rule in rules:
            # Check if already structured
            existing = db.query(StructuredRule).filter(StructuredRule.rule_id == rule.rule_id).first()
            if existing:
                logger.info(f"Rule {rule.rule_id} already has structured data, skipping.")
                continue
            
            logger.info(f"Interpreting rule: {rule.rule_id}")
            try:
                structured_data = interpreter.interpret(rule)
                db_structured_rule = StructuredRule(**structured_data.model_dump())
                db.add(db_structured_rule)
                db.commit()
                logger.info(f"Successfully structured rule: {rule.rule_id}")
            except Exception as e:
                logger.error(f"Failed to interpret rule {rule.rule_id}: {e}")
                db.rollback()
        
        print("Interpretation completed.")
    finally:
        db.close()

if __name__ == "__main__":
    interpret_rules()
