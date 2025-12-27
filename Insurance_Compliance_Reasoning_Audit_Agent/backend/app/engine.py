from typing import List, Dict, Any
from .models import DecisionOutcome, RuleSeverity

class DecisionEngine:
    @staticmethod
    def decide(ai_evaluations: List[Dict[str, Any]], rule_severities: Dict[str, RuleSeverity]) -> DecisionOutcome:
        """
        Deterministically decide the compliance outcome based on AI evaluations and rule severities.
        """
        if not ai_evaluations:
            return DecisionOutcome.COMPLIANT

        violated_rules = []
        for evaluation in ai_evaluations:
            if evaluation.get("status") == "NON_COMPLIANT":
                violated_rules.append(evaluation.get("rule_id"))

        if not violated_rules:
            return DecisionOutcome.COMPLIANT

        # If there are violations, check severities
        # For now, any violation leads to NON_COMPLIANT
        # But we could add logic like: if only LOW violations, maybe REQUIRES_REVIEW
        
        has_high_violation = any(rule_severities.get(rid) == RuleSeverity.HIGH for rid in violated_rules)
        
        if has_high_violation:
            return DecisionOutcome.NON_COMPLIANT
        
        # Default to NON_COMPLIANT for any violation
        return DecisionOutcome.NON_COMPLIANT

    @staticmethod
    def resolve_conflicts(evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Placeholder for conflict resolution logic if multiple agents were used.
        """
        return evaluations
