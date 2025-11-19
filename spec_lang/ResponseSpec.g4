grammar ResponseSpec;

// Lexer Rules
RULE: 'rule';
TRIGGER: 'trigger'; 
CHECK: 'check';
ORCHESTRATE: 'orchestrate';  
END: 'end';
AT: '@';
HASH: '#';
NOT: '!';
AND: '&&';
OR: '||';
LPAREN: '(';
RPAREN: ')';

// Whitespace and comments
WS: [ \t\r\n]+ -> skip;
LINE_COMMENT: '//' ~[\r\n]* -> skip;
BLOCK_COMMENT: '/*' .*? '*/' -> skip;

// Identifiers and literals
IDENTIFIER: [a-zA-Z_][a-zA-Z0-9_]*;
STRING: '"' ( '\\' . | ~[\\"\r\n] )* '"';

// Parser Rules
program: rule* EOF;

rule: ruleClause
      triggerClause 
      checkClause
      orchestrateClause
      END;

ruleClause: RULE AT IDENTIFIER;

triggerClause: TRIGGER toolTrigger;

toolTrigger: STRING  // e.g., "delete_file"
           | IDENTIFIER;  // e.g., delete_file

checkClause: CHECK incidentCondition;

incidentCondition: STRING  // Natural language condition
                 | logicalExpression;

logicalExpression: STRING (AND STRING)+
                 | STRING (OR STRING)+
                 | NOT STRING
                 | LPAREN logicalExpression RPAREN;

orchestrateClause: ORCHESTRATE remediationAction;

remediationAction: STRING  // Natural language remediation instruction
                 | multiStepRemediation;

multiStepRemediation: STRING (STRING)+;  // Multiple steps separated by newlines
