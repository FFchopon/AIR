"""
Interpreter for ResponseSpec rules.
Handles incident detection using LLM-based natural language evaluation.
"""

import json
import os
import time
from typing import Dict, Any, Optional, Tuple
from rule import Rule
from state import IncidentState


def _env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


DEBUG_LLM_API = _env_flag("RESPONSESPEC_DEBUG_LLM", default=False)


def set_llm_api_debug(enabled: bool = True) -> None:
    global DEBUG_LLM_API
    DEBUG_LLM_API = enabled


class IncidentDetector:
    """
    Detects incidents by evaluating natural language conditions using an LLM.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize the incident detector.
        
        Args:
            llm_client: Optional LLM client for detection. If None, uses OpenAI by default.
        """
        self.llm_client = llm_client
    
    def detect_incident(
        self,
        triggered_rules: list[Rule],
        recent_history: list[Dict[str, Any]],
        environment_state: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect if any incident occurred based on triggered rules.
        
        Args:
            triggered_rules: List of rules to check
            recent_history: Recent tool call history (last 5 calls)
            environment_state: Optional description of current environment state
            
        Returns:
            Tuple of (incident_detected, incident_details)
            incident_details contains: rule_id, description, severity
        """
        if not triggered_rules:
            return False, None
        
        # Construct detection prompt
        rules_json = [
            {
                "id": rule.id,
                "condition": rule.incident_condition,
                "remediation": rule.remediation_action
            }
            for rule in triggered_rules
        ]
        
        detection_prompt = self._build_detection_prompt(
            rules_json, 
            recent_history, 
            environment_state
        )
        
        # Call LLM for detection
        result = self._call_llm_for_detection(detection_prompt, stage="postcheck")
        
        if result.get("incident_detected", False):
            return True, {
                "rule_id": result.get("triggered_rule_id"),
                "description": result.get("description"),
                "severity": result.get("severity", "medium")
            }
        
        return False, None
    
    def _build_detection_prompt(
        self,
        rules: list[Dict],
        history: list[Dict],
        env_state: Optional[str]
    ) -> str:
        """Build the detection prompt for the LLM"""
        
        env_section = f"\nEnvironment State:\n{env_state}\n" if env_state else ""
        
        return f"""You are a security incident detection system. Your task is to analyze recent actions and determine if any security incidents have occurred.

SECURITY RULES TO CHECK:
{json.dumps(rules, indent=2)}

RECENT ACTION HISTORY:
{json.dumps(history, indent=2)}
{env_section}

TASK:
Carefully analyze the action history against each security rule's condition.
Determine if any incident has occurred based on the recent actions.

RESPONSE FORMAT (JSON):
{{
    "incident_detected": true or false,
    "triggered_rule_id": "rule ID if incident detected, otherwise null",
    "description": "detailed description of what happened and why it's an incident",
    "severity": "low, medium, high, or critical",
    "confidence": "low, medium, or high"
}}

Be precise and only flag actual incidents that match the rule conditions.
"""
    
    def _call_llm_for_detection(self, prompt: str, stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Call LLM to perform incident detection using OpenAI API.
        
        Uses structured output (JSON mode) for reliable parsing.
        """
        start_ts = time.time()
        model = "gpt-5.6-luna"
        stage_value = stage or "detector"
        try:
            if self.llm_client:
                # Use provided LLM client
                client = self.llm_client
            else:
                # Use default OpenAI client (requires OPENAI_API_KEY env var)
                from openai import OpenAI
                client = OpenAI()

            if DEBUG_LLM_API:
                prompt_chars = len(prompt) if isinstance(prompt, str) else 0
                print(
                    f"[LLM API START] kind=detector stage={stage_value} model={model} prompt_chars={prompt_chars}"
                )
            
            # Call OpenAI with JSON mode for structured output
            request_kwargs = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a security incident detection system. Analyze actions against security rules and respond in JSON format.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "response_format": {"type": "json_object"},
            }

            # Some models (e.g., gpt-5-mini) only support the default temperature.
            if not str(model).startswith("gpt-5"):
                request_kwargs["temperature"] = 0

            response = client.chat.completions.create(**request_kwargs)
            
            result = json.loads(response.choices[0].message.content)

            if DEBUG_LLM_API:
                duration_ms = int((time.time() - start_ts) * 1000)
                print(
                    f"[LLM API END] kind=detector stage={stage_value} model={model} duration_ms={duration_ms}"
                )
            
            # Validate required fields
            if "incident_detected" not in result:
                result["incident_detected"] = False
            if "triggered_rule_id" not in result:
                result["triggered_rule_id"] = None
            if "description" not in result:
                result["description"] = ""
            if "severity" not in result:
                result["severity"] = "medium"
            
            return result
            
        except Exception as e:
            if DEBUG_LLM_API:
                duration_ms = int((time.time() - start_ts) * 1000)
                print(
                    f"[LLM API END] kind=detector stage={stage_value} model={model} duration_ms={duration_ms} status=error"
                )
            print(f"[IncidentDetector] Error calling LLM: {e}")
            # Return safe default on error
            return {
                "incident_detected": False,
                "triggered_rule_id": None,
                "description": f"Error during detection: {str(e)}",
                "severity": "low",
                "confidence": "low"
            }


class RuleInterpreter:
    """
    Interprets and executes ResponseSpec rules.
    Coordinates incident detection and remediation orchestration.
    """
    
    def __init__(self, rules: list[Rule], llm_client: Optional[Any] = None):
        """
        Initialize the rule interpreter.
        
        Args:
            rules: List of ResponseSpec rules
            llm_client: Optional LLM client for detection
        """
        self.rules = rules
        self.detector = IncidentDetector(llm_client)
    
    def process_tool_call(
        self,
        state: IncidentState,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a tool call and check for incidents.
        
        Args:
            state: Current incident state
            tool_name: Name of the tool that was called
            tool_args: Arguments passed to the tool
            tool_result: Result returned by the tool
            
        Returns:
            Incident details if detected, None otherwise
        """
        # Record the tool call
        state.add_tool_call(tool_name, tool_args, tool_result)
        
        # Get triggered rules
        triggered_rules = state.get_triggered_rules_for_tool(tool_name)
        state.triggered_rules_current_turn = triggered_rules
        
        if not triggered_rules:
            return None
        
        # Detect incidents
        incident_detected, incident_details = self.detector.detect_incident(
            triggered_rules,
            state.get_recent_history(5)
        )
        
        if incident_detected:
            # Find the triggered rule to get remediation action
            rule = next(
                (r for r in triggered_rules if r.id == incident_details["rule_id"]),
                None
            )
            
            if rule:
                state.set_incident(
                    rule_id=rule.id,
                    description=incident_details["description"],
                    remediation=rule.remediation_action,
                    severity=incident_details["severity"]
                )
                return incident_details
        
        return None
    
    def get_remediation_instruction(self, state: IncidentState) -> Optional[str]:
        """
        Get the remediation instruction for the current incident.
        
        Args:
            state: Current incident state
            
        Returns:
            Remediation instruction or None
        """
        if not state.incident_detected:
            return None
        
        return state.remediation_action
