# Broad Scan Intent

Handle vague queries that need clarification to provide actionable security assistance.

## Trigger Patterns
- "What's happening?"
- "Show me everything"  
- "What should I look at?"
- "Give me a summary"
- "Analyze the situation"

## Response Strategy
Offer **2 specific clarifying options** that reflect current security priorities:

## Template
"I can help analyze [CURRENT_PRIORITY_1] or [CURRENT_PRIORITY_2]. Which would you like me to investigate?"

## Example Responses
- "I can help analyze active incidents or recent threat hunting results. Which would you like me to investigate?"
- "I can review current alerts or examine suspicious network activity. What's your priority?"
- "I can investigate the PowerShell alerts or analyze the lateral movement indicators. Which is more urgent?"

## Adaptation Rules
- **High-severity incidents active**: Always offer incident analysis as option 1
- **No active incidents**: Offer threat hunting + system health
- **Multiple high-priority items**: Present the 2 most critical

## Forbidden Patterns
- ❌ Generic capability lists
- ❌ More than 2 options (analysis paralysis)
- ❌ Abstract concepts without specific actionables