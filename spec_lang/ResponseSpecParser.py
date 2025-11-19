# Generated from D:/10.4/AgentSpec-master/ResponseSpec/spec_lang/ResponseSpec.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,17,88,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,1,0,5,0,24,8,0,10,0,12,0,27,
        9,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,2,1,2,1,2,1,3,1,3,1,3,
        1,4,1,4,1,5,1,5,1,5,1,6,1,6,3,6,51,8,6,1,7,1,7,1,7,4,7,56,8,7,11,
        7,12,7,57,1,7,1,7,1,7,4,7,63,8,7,11,7,12,7,64,1,7,1,7,1,7,1,7,1,
        7,1,7,3,7,73,8,7,1,8,1,8,1,8,1,9,1,9,3,9,80,8,9,1,10,1,10,4,10,84,
        8,10,11,10,12,10,85,1,10,0,0,11,0,2,4,6,8,10,12,14,16,18,20,0,1,
        1,0,16,17,85,0,25,1,0,0,0,2,30,1,0,0,0,4,36,1,0,0,0,6,40,1,0,0,0,
        8,43,1,0,0,0,10,45,1,0,0,0,12,50,1,0,0,0,14,72,1,0,0,0,16,74,1,0,
        0,0,18,79,1,0,0,0,20,81,1,0,0,0,22,24,3,2,1,0,23,22,1,0,0,0,24,27,
        1,0,0,0,25,23,1,0,0,0,25,26,1,0,0,0,26,28,1,0,0,0,27,25,1,0,0,0,
        28,29,5,0,0,1,29,1,1,0,0,0,30,31,3,4,2,0,31,32,3,6,3,0,32,33,3,10,
        5,0,33,34,3,16,8,0,34,35,5,5,0,0,35,3,1,0,0,0,36,37,5,1,0,0,37,38,
        5,6,0,0,38,39,5,16,0,0,39,5,1,0,0,0,40,41,5,2,0,0,41,42,3,8,4,0,
        42,7,1,0,0,0,43,44,7,0,0,0,44,9,1,0,0,0,45,46,5,3,0,0,46,47,3,12,
        6,0,47,11,1,0,0,0,48,51,5,17,0,0,49,51,3,14,7,0,50,48,1,0,0,0,50,
        49,1,0,0,0,51,13,1,0,0,0,52,55,5,17,0,0,53,54,5,9,0,0,54,56,5,17,
        0,0,55,53,1,0,0,0,56,57,1,0,0,0,57,55,1,0,0,0,57,58,1,0,0,0,58,73,
        1,0,0,0,59,62,5,17,0,0,60,61,5,10,0,0,61,63,5,17,0,0,62,60,1,0,0,
        0,63,64,1,0,0,0,64,62,1,0,0,0,64,65,1,0,0,0,65,73,1,0,0,0,66,67,
        5,8,0,0,67,73,5,17,0,0,68,69,5,11,0,0,69,70,3,14,7,0,70,71,5,12,
        0,0,71,73,1,0,0,0,72,52,1,0,0,0,72,59,1,0,0,0,72,66,1,0,0,0,72,68,
        1,0,0,0,73,15,1,0,0,0,74,75,5,4,0,0,75,76,3,18,9,0,76,17,1,0,0,0,
        77,80,5,17,0,0,78,80,3,20,10,0,79,77,1,0,0,0,79,78,1,0,0,0,80,19,
        1,0,0,0,81,83,5,17,0,0,82,84,5,17,0,0,83,82,1,0,0,0,84,85,1,0,0,
        0,85,83,1,0,0,0,85,86,1,0,0,0,86,21,1,0,0,0,7,25,50,57,64,72,79,
        85
    ]

class ResponseSpecParser ( Parser ):

    grammarFileName = "ResponseSpec.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'rule'", "'trigger'", "'check'", "'orchestrate'", 
                     "'end'", "'@'", "'#'", "'!'", "'&&'", "'||'", "'('", 
                     "')'" ]

    symbolicNames = [ "<INVALID>", "RULE", "TRIGGER", "CHECK", "ORCHESTRATE", 
                      "END", "AT", "HASH", "NOT", "AND", "OR", "LPAREN", 
                      "RPAREN", "WS", "LINE_COMMENT", "BLOCK_COMMENT", "IDENTIFIER", 
                      "STRING" ]

    RULE_program = 0
    RULE_rule = 1
    RULE_ruleClause = 2
    RULE_triggerClause = 3
    RULE_toolTrigger = 4
    RULE_checkClause = 5
    RULE_incidentCondition = 6
    RULE_logicalExpression = 7
    RULE_orchestrateClause = 8
    RULE_remediationAction = 9
    RULE_multiStepRemediation = 10

    ruleNames =  [ "program", "rule", "ruleClause", "triggerClause", "toolTrigger", 
                   "checkClause", "incidentCondition", "logicalExpression", 
                   "orchestrateClause", "remediationAction", "multiStepRemediation" ]

    EOF = Token.EOF
    RULE=1
    TRIGGER=2
    CHECK=3
    ORCHESTRATE=4
    END=5
    AT=6
    HASH=7
    NOT=8
    AND=9
    OR=10
    LPAREN=11
    RPAREN=12
    WS=13
    LINE_COMMENT=14
    BLOCK_COMMENT=15
    IDENTIFIER=16
    STRING=17

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProgramContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(ResponseSpecParser.EOF, 0)

        def rule_(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ResponseSpecParser.RuleContext)
            else:
                return self.getTypedRuleContext(ResponseSpecParser.RuleContext,i)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_program

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProgram" ):
                listener.enterProgram(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProgram" ):
                listener.exitProgram(self)




    def program(self):

        localctx = ResponseSpecParser.ProgramContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_program)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 25
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==1:
                self.state = 22
                self.rule_()
                self.state = 27
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 28
            self.match(ResponseSpecParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RuleContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ruleClause(self):
            return self.getTypedRuleContext(ResponseSpecParser.RuleClauseContext,0)


        def triggerClause(self):
            return self.getTypedRuleContext(ResponseSpecParser.TriggerClauseContext,0)


        def checkClause(self):
            return self.getTypedRuleContext(ResponseSpecParser.CheckClauseContext,0)


        def orchestrateClause(self):
            return self.getTypedRuleContext(ResponseSpecParser.OrchestrateClauseContext,0)


        def END(self):
            return self.getToken(ResponseSpecParser.END, 0)

        def getRuleIndex(self):
            return ResponseSpecParser.RULE_rule

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRule" ):
                listener.enterRule(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRule" ):
                listener.exitRule(self)




    def rule_(self):

        localctx = ResponseSpecParser.RuleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_rule)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.ruleClause()
            self.state = 31
            self.triggerClause()
            self.state = 32
            self.checkClause()
            self.state = 33
            self.orchestrateClause()
            self.state = 34
            self.match(ResponseSpecParser.END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RuleClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def RULE(self):
            return self.getToken(ResponseSpecParser.RULE, 0)

        def AT(self):
            return self.getToken(ResponseSpecParser.AT, 0)

        def IDENTIFIER(self):
            return self.getToken(ResponseSpecParser.IDENTIFIER, 0)

        def getRuleIndex(self):
            return ResponseSpecParser.RULE_ruleClause

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRuleClause" ):
                listener.enterRuleClause(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRuleClause" ):
                listener.exitRuleClause(self)




    def ruleClause(self):

        localctx = ResponseSpecParser.RuleClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_ruleClause)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 36
            self.match(ResponseSpecParser.RULE)
            self.state = 37
            self.match(ResponseSpecParser.AT)
            self.state = 38
            self.match(ResponseSpecParser.IDENTIFIER)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TriggerClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def TRIGGER(self):
            return self.getToken(ResponseSpecParser.TRIGGER, 0)

        def toolTrigger(self):
            return self.getTypedRuleContext(ResponseSpecParser.ToolTriggerContext,0)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_triggerClause

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTriggerClause" ):
                listener.enterTriggerClause(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTriggerClause" ):
                listener.exitTriggerClause(self)




    def triggerClause(self):

        localctx = ResponseSpecParser.TriggerClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_triggerClause)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 40
            self.match(ResponseSpecParser.TRIGGER)
            self.state = 41
            self.toolTrigger()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ToolTriggerContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(ResponseSpecParser.STRING, 0)

        def IDENTIFIER(self):
            return self.getToken(ResponseSpecParser.IDENTIFIER, 0)

        def getRuleIndex(self):
            return ResponseSpecParser.RULE_toolTrigger

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterToolTrigger" ):
                listener.enterToolTrigger(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitToolTrigger" ):
                listener.exitToolTrigger(self)




    def toolTrigger(self):

        localctx = ResponseSpecParser.ToolTriggerContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_toolTrigger)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            _la = self._input.LA(1)
            if not(_la==16 or _la==17):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CheckClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CHECK(self):
            return self.getToken(ResponseSpecParser.CHECK, 0)

        def incidentCondition(self):
            return self.getTypedRuleContext(ResponseSpecParser.IncidentConditionContext,0)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_checkClause

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCheckClause" ):
                listener.enterCheckClause(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCheckClause" ):
                listener.exitCheckClause(self)




    def checkClause(self):

        localctx = ResponseSpecParser.CheckClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_checkClause)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 45
            self.match(ResponseSpecParser.CHECK)
            self.state = 46
            self.incidentCondition()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IncidentConditionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(ResponseSpecParser.STRING, 0)

        def logicalExpression(self):
            return self.getTypedRuleContext(ResponseSpecParser.LogicalExpressionContext,0)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_incidentCondition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIncidentCondition" ):
                listener.enterIncidentCondition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIncidentCondition" ):
                listener.exitIncidentCondition(self)




    def incidentCondition(self):

        localctx = ResponseSpecParser.IncidentConditionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_incidentCondition)
        try:
            self.state = 50
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 48
                self.match(ResponseSpecParser.STRING)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 49
                self.logicalExpression()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LogicalExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self, i:int=None):
            if i is None:
                return self.getTokens(ResponseSpecParser.STRING)
            else:
                return self.getToken(ResponseSpecParser.STRING, i)

        def AND(self, i:int=None):
            if i is None:
                return self.getTokens(ResponseSpecParser.AND)
            else:
                return self.getToken(ResponseSpecParser.AND, i)

        def OR(self, i:int=None):
            if i is None:
                return self.getTokens(ResponseSpecParser.OR)
            else:
                return self.getToken(ResponseSpecParser.OR, i)

        def NOT(self):
            return self.getToken(ResponseSpecParser.NOT, 0)

        def LPAREN(self):
            return self.getToken(ResponseSpecParser.LPAREN, 0)

        def logicalExpression(self):
            return self.getTypedRuleContext(ResponseSpecParser.LogicalExpressionContext,0)


        def RPAREN(self):
            return self.getToken(ResponseSpecParser.RPAREN, 0)

        def getRuleIndex(self):
            return ResponseSpecParser.RULE_logicalExpression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLogicalExpression" ):
                listener.enterLogicalExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLogicalExpression" ):
                listener.exitLogicalExpression(self)




    def logicalExpression(self):

        localctx = ResponseSpecParser.LogicalExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_logicalExpression)
        self._la = 0 # Token type
        try:
            self.state = 72
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,4,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 52
                self.match(ResponseSpecParser.STRING)
                self.state = 55 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 53
                    self.match(ResponseSpecParser.AND)
                    self.state = 54
                    self.match(ResponseSpecParser.STRING)
                    self.state = 57 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==9):
                        break

                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 59
                self.match(ResponseSpecParser.STRING)
                self.state = 62 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 60
                    self.match(ResponseSpecParser.OR)
                    self.state = 61
                    self.match(ResponseSpecParser.STRING)
                    self.state = 64 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==10):
                        break

                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 66
                self.match(ResponseSpecParser.NOT)
                self.state = 67
                self.match(ResponseSpecParser.STRING)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 68
                self.match(ResponseSpecParser.LPAREN)
                self.state = 69
                self.logicalExpression()
                self.state = 70
                self.match(ResponseSpecParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OrchestrateClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ORCHESTRATE(self):
            return self.getToken(ResponseSpecParser.ORCHESTRATE, 0)

        def remediationAction(self):
            return self.getTypedRuleContext(ResponseSpecParser.RemediationActionContext,0)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_orchestrateClause

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOrchestrateClause" ):
                listener.enterOrchestrateClause(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOrchestrateClause" ):
                listener.exitOrchestrateClause(self)




    def orchestrateClause(self):

        localctx = ResponseSpecParser.OrchestrateClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_orchestrateClause)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            self.match(ResponseSpecParser.ORCHESTRATE)
            self.state = 75
            self.remediationAction()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RemediationActionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(ResponseSpecParser.STRING, 0)

        def multiStepRemediation(self):
            return self.getTypedRuleContext(ResponseSpecParser.MultiStepRemediationContext,0)


        def getRuleIndex(self):
            return ResponseSpecParser.RULE_remediationAction

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRemediationAction" ):
                listener.enterRemediationAction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRemediationAction" ):
                listener.exitRemediationAction(self)




    def remediationAction(self):

        localctx = ResponseSpecParser.RemediationActionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_remediationAction)
        try:
            self.state = 79
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,5,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 77
                self.match(ResponseSpecParser.STRING)
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 78
                self.multiStepRemediation()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MultiStepRemediationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self, i:int=None):
            if i is None:
                return self.getTokens(ResponseSpecParser.STRING)
            else:
                return self.getToken(ResponseSpecParser.STRING, i)

        def getRuleIndex(self):
            return ResponseSpecParser.RULE_multiStepRemediation

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMultiStepRemediation" ):
                listener.enterMultiStepRemediation(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMultiStepRemediation" ):
                listener.exitMultiStepRemediation(self)




    def multiStepRemediation(self):

        localctx = ResponseSpecParser.MultiStepRemediationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_multiStepRemediation)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 81
            self.match(ResponseSpecParser.STRING)
            self.state = 83 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 82
                self.match(ResponseSpecParser.STRING)
                self.state = 85 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==17):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





