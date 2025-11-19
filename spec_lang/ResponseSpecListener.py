# Generated from D:/10.4/AgentSpec-master/ResponseSpec/spec_lang/ResponseSpec.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ResponseSpecParser import ResponseSpecParser
else:
    from ResponseSpecParser import ResponseSpecParser

# This class defines a complete listener for a parse tree produced by ResponseSpecParser.
class ResponseSpecListener(ParseTreeListener):

    # Enter a parse tree produced by ResponseSpecParser#program.
    def enterProgram(self, ctx:ResponseSpecParser.ProgramContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#program.
    def exitProgram(self, ctx:ResponseSpecParser.ProgramContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#rule.
    def enterRule(self, ctx:ResponseSpecParser.RuleContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#rule.
    def exitRule(self, ctx:ResponseSpecParser.RuleContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#ruleClause.
    def enterRuleClause(self, ctx:ResponseSpecParser.RuleClauseContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#ruleClause.
    def exitRuleClause(self, ctx:ResponseSpecParser.RuleClauseContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#triggerClause.
    def enterTriggerClause(self, ctx:ResponseSpecParser.TriggerClauseContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#triggerClause.
    def exitTriggerClause(self, ctx:ResponseSpecParser.TriggerClauseContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#toolTrigger.
    def enterToolTrigger(self, ctx:ResponseSpecParser.ToolTriggerContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#toolTrigger.
    def exitToolTrigger(self, ctx:ResponseSpecParser.ToolTriggerContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#checkClause.
    def enterCheckClause(self, ctx:ResponseSpecParser.CheckClauseContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#checkClause.
    def exitCheckClause(self, ctx:ResponseSpecParser.CheckClauseContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#incidentCondition.
    def enterIncidentCondition(self, ctx:ResponseSpecParser.IncidentConditionContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#incidentCondition.
    def exitIncidentCondition(self, ctx:ResponseSpecParser.IncidentConditionContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#logicalExpression.
    def enterLogicalExpression(self, ctx:ResponseSpecParser.LogicalExpressionContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#logicalExpression.
    def exitLogicalExpression(self, ctx:ResponseSpecParser.LogicalExpressionContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#orchestrateClause.
    def enterOrchestrateClause(self, ctx:ResponseSpecParser.OrchestrateClauseContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#orchestrateClause.
    def exitOrchestrateClause(self, ctx:ResponseSpecParser.OrchestrateClauseContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#remediationAction.
    def enterRemediationAction(self, ctx:ResponseSpecParser.RemediationActionContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#remediationAction.
    def exitRemediationAction(self, ctx:ResponseSpecParser.RemediationActionContext):
        pass


    # Enter a parse tree produced by ResponseSpecParser#multiStepRemediation.
    def enterMultiStepRemediation(self, ctx:ResponseSpecParser.MultiStepRemediationContext):
        pass

    # Exit a parse tree produced by ResponseSpecParser#multiStepRemediation.
    def exitMultiStepRemediation(self, ctx:ResponseSpecParser.MultiStepRemediationContext):
        pass



del ResponseSpecParser