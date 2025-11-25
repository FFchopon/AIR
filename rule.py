"""
Rule definition and parsing for ResponseSpec DSL.
Handles incident response rules with natural language conditions.
"""

from antlr4 import *
from pydantic import BaseModel 
from typing import Optional, List
from spec_lang.ResponseSpecListener import ResponseSpecListener 
from spec_lang.ResponseSpecLexer import ResponseSpecLexer
from spec_lang.ResponseSpecParser import ResponseSpecParser


class RuleParser(ResponseSpecListener): 
    """ANTLR listener for parsing ResponseSpec rules"""
    
    def __init__(self):
        self.rule_id: str = ""
        # Primary trigger tool (for backward compatibility)
        self.trigger_tool: str = ""
        # Support multiple trigger tools per rule (any of them can trigger)
        self.trigger_tools: List[str] = []
        self.incident_condition: str = ""
        self.remediation_action: str = ""
    
    def enterRuleClause(self, ctx: ResponseSpecParser.RuleClauseContext):
        """Extract rule ID"""
        self.rule_id = ctx.IDENTIFIER().getText()
    
    def enterToolTrigger(self, ctx: ResponseSpecParser.ToolTriggerContext):
        """Extract trigger tool name"""
        if ctx.STRING():
            # Remove quotes: "delete_file" -> delete_file
            name = ctx.STRING().getText()[1:-1]
        elif ctx.IDENTIFIER():
            # Use identifier directly: delete_file -> delete_file
            name = ctx.IDENTIFIER().getText()
        else:
            return

        # Record primary trigger_tool for backward compatibility
        if not self.trigger_tool:
            self.trigger_tool = name
        # And always append into the list of trigger_tools
        self.trigger_tools.append(name)
    
    def enterIncidentCondition(self, ctx: ResponseSpecParser.IncidentConditionContext):
        """Extract incident condition (natural language)"""
        if ctx.STRING():
            # Remove quotes
            self.incident_condition = ctx.STRING().getText()[1:-1]
        else:
            # Handle logical expressions if needed
            self.incident_condition = ctx.getText()
    
    def enterRemediationAction(self, ctx: ResponseSpecParser.RemediationActionContext):
        """Extract remediation action (natural language)"""
        if ctx.STRING():
            # Single step remediation
            self.remediation_action = ctx.STRING().getText()[1:-1]
        elif ctx.multiStepRemediation():
            # Multi-step remediation
            steps = [s.getText()[1:-1] for s in ctx.multiStepRemediation().STRING()]
            self.remediation_action = " THEN ".join(steps)


class Rule(BaseModel):
    """
    Represents a security incident response rule.
    
    Attributes:
        id: Unique identifier for the rule
        trigger_tool: Name of the primary tool that triggers this rule
        trigger_tools: Optional list of tools, any of which can trigger the rule
        incident_condition: Natural language description of the incident
        remediation_action: Natural language instruction for remediation
        raw: Original rule text
        is_learned: Whether this is a learned rule (from eradication)
        confidence: Confidence score for learned rules (0.0-1.0)
        learned_from: ID of the incident this rule was learned from
        examples: Example operations that this rule should block
    """
    id: str
    trigger_tool: str
    trigger_tools: List[str] = []
    incident_condition: str
    remediation_action: str
    raw: str
    is_learned: bool = False
    confidence: float = 1.0
    learned_from: str = ""
    examples: List[str] = []
    
    def triggered_by_tool(self, tool_name: str) -> bool:
        """Check if this rule is triggered by the given tool"""
        # If a multi-tool list is present, prefer it
        if self.trigger_tools:
            return tool_name in self.trigger_tools or "any" in self.trigger_tools
        # Fallback to single trigger_tool for backward compatibility
        return self.trigger_tool == tool_name or self.trigger_tool == "any"
    
    @staticmethod
    def from_text(rule_str: str) -> 'Rule':
        """
        Parse a rule from DSL text.
        
        Args:
            rule_str: Rule definition in ResponseSpec DSL format
            
        Returns:
            Parsed Rule object
            
        Raises:
            ValueError: If the rule syntax is invalid
        """
        input_stream = InputStream(rule_str)
        lexer = ResponseSpecLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = ResponseSpecParser(token_stream)
        
        # Add error handling
        parser.removeErrorListeners()
        from antlr4.error.ErrorListener import ErrorListener
        
        class CustomErrorListener(ErrorListener):
            def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
                raise ValueError(f"Syntax error at line {line}:{column} - {msg}")
        
        parser.addErrorListener(CustomErrorListener())
        
        # Parse the rule
        tree = parser.program()
        walker = ParseTreeWalker()
        rule_parser = RuleParser()
        walker.walk(rule_parser, tree)
        
        # Normalize trigger tools
        tools = rule_parser.trigger_tools
        # Ensure trigger_tool is always populated for backward compatibility
        primary_tool = rule_parser.trigger_tool or (tools[0] if tools else "")

        return Rule(
            raw=rule_str,
            id=rule_parser.rule_id,
            trigger_tool=primary_tool,
            trigger_tools=tools,
            incident_condition=rule_parser.incident_condition,
            remediation_action=rule_parser.remediation_action
        )
    
    @staticmethod
    def from_file(file_path: str) -> List['Rule']:
        """
        Parse multiple rules from a file.
        
        Args:
            file_path: Path to file containing rule definitions
            
        Returns:
            List of parsed Rule objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by 'rule @' to get individual rules
        import re
        rule_texts = re.split(r'(?=rule\s+@)', content)
        rule_texts = [r.strip() for r in rule_texts if r.strip()]
        
        return [Rule.from_text(text) for text in rule_texts]


# Example usage and testing
if __name__ == "__main__":
    example_rule = """
rule @prevent_system_file_copy
trigger 
    "copy_file"
check
    "copied files from /etc to any user-accessible directory." 
orchestrate
    "Delete any copied sensitive files from user directories."
end
"""
    
    try:
        rule = Rule.from_text(example_rule)
        print(f"Rule ID: {rule.id}")
        print(f"Trigger Tool: {rule.trigger_tool}")
        print(f"Incident Condition: {rule.incident_condition}")
        print(f"Remediation Action: {rule.remediation_action}")
    except Exception as e:
        print(f"Error parsing rule: {e}")
