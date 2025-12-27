import json
import concurrent.futures
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from . import schemas, models


class PolicyInterpreterAgent:
    def __init__(self, model_name: str = "gpt-4o", timeout: int = 60):
        self.llm = ChatOpenAI(model=model_name)
        self.timeout = timeout
        self.agent = Agent(
            role='Policy Interpreter',
            goal='Accurately translate human-readable insurance compliance '
                 'rules into structured machine-evaluable constraints.',
            backstory="""You are a senior compliance analyst with expertise in 
            insurance regulations. Your task is to take a rule text and break 
            it down into its logical components: applicability conditions, 
            obligations, and exceptions. You must be precise and 
            deterministic. Do not invent rules or modify the intent.""",
            allow_delegation=False,
            llm=self.llm,
            verbose=True
        )

    def interpret(
        self,
        rule: models.ComplianceRule
    ) -> schemas.StructuredRuleCreate:
        task = Task(
            description=f"""
            Interpret the following compliance rule:
            Rule ID: {rule.rule_id}
            Category: {rule.category}
            Severity: {rule.severity}
            Rule Text: {rule.rule_text}

            Extract:
            1. Applicability Conditions: Under what circumstances does this rule apply?
            2. Obligations: What MUST be done or NOT be done?
            3. Exceptions: Are there any cases where this rule does not apply?

            Output MUST be a valid JSON matching this structure:
            {{
                "rule_id": "{rule.rule_id}",
                "version": "{rule.version}",
                "applicability_conditions": ["condition1", "condition2"],
                "obligations": ["obligation1", "obligation2"],
                "exceptions": ["exception1", "exception2"],
                "severity": "{rule.severity}"
            }}
            """,
            expected_output="A structured JSON representation of the rule.",
            agent=self.agent
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential
        )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(crew.kickoff)
            try:
                result = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                raise Exception(f"Rule interpretation timed out after {self.timeout} seconds")

        # result.raw is the string output. We need to parse it.
        raw_output = result.raw
        json_str = raw_output
        if "```json" in raw_output:
            json_str = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            json_str = raw_output.split("```")[1].split("```")[0].strip()

        structured_data = json.loads(json_str)

        return schemas.StructuredRuleCreate(
            rule_id=structured_data["rule_id"],
            version=structured_data["version"],
            applicability_conditions=structured_data["applicability_conditions"],
            obligations=structured_data["obligations"],
            exceptions=structured_data["exceptions"],
            severity=models.RuleSeverity(structured_data["severity"]),
            raw_ai_output=raw_output
        )


class ComplianceReasoningAgent:
    def __init__(self, model_name: str = "gpt-4o", timeout: int = 90):
        self.llm = ChatOpenAI(model=model_name)
        self.timeout = timeout
        self.agent = Agent(
            role='Compliance Auditor',
            goal='Evaluate insurance workflows against structured compliance '
                 'rules and provide a detailed reasoning trace.',
            backstory="""You are an expert insurance auditor. Your job is to 
            analyze a workflow event and determine if it complies with a 
            specific set of structured rules. You must follow a strict 
            reasoning protocol:
            1. Applicability check: Does the rule apply to this event?
            2. Condition evaluation: Are the conditions met?
            3. Obligation validation: Are the obligations fulfilled?
            4. Exception handling: Do any exceptions apply?
            5. Violation detection: Is there a violation?

            You must provide a step-by-step reasoning trace for each rule.""",
            allow_delegation=False,
            llm=self.llm,
            verbose=True
        )

    def evaluate(
        self,
        event: models.WorkflowEvent,
        rules: list[models.StructuredRule]
    ) -> dict:
        rules_json = [
            {
                "rule_id": r.rule_id,
                "version": r.version,
                "applicability_conditions": r.applicability_conditions,
                "obligations": r.obligations,
                "exceptions": r.exceptions,
                "severity": r.severity
            } for r in rules
        ]

        task = Task(
            description=f"""
            Evaluate the following workflow event against the rules.

            Workflow Event:
            ID: {event.workflow_id}
            Type: {event.workflow_type}
            Actor: {event.actor_id}
            Attributes: {json.dumps(event.attributes)}

            Structured Rules:
            {json.dumps(rules_json)}

            For EACH rule, follow the reasoning protocol and determine if 
            it is COMPLIANT or NON_COMPLIANT.

            Output MUST be a valid JSON matching this structure:
            {{
                "workflow_id": "{event.workflow_id}",
                "evaluations": [
                    {{
                        "rule_id": "string",
                        "status": "COMPLIANT | NON_COMPLIANT",
                        "reasoning_steps": [
                            {{"step": "Applicability Check", "result": "...", "detail": "..."}},
                            {{"step": "Condition Evaluation", "result": "...", "detail": "..."}},
                            {{"step": "Obligation Validation", "result": "...", "detail": "..."}},
                            {{"step": "Exception Handling", "result": "...", "detail": "..."}},
                            {{"step": "Violation Detection", "result": "...", "detail": "..."}}
                        ]
                    }}
                ]
            }}
            """,
            expected_output="A detailed compliance evaluation JSON.",
            agent=self.agent
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential
        )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(crew.kickoff)
            try:
                result = future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                raise Exception(f"Compliance reasoning timed out after {self.timeout} seconds")

        raw_output = result.raw
        json_str = raw_output
        if "```json" in raw_output:
            json_str = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            json_str = raw_output.split("```")[1].split("```")[0].strip()
            
        return json.loads(json_str)
