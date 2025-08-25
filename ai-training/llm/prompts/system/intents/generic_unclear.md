# Generic Unclear Intent

Handle unclear requests that don't fit specific patterns but need clarification.

## Trigger Conditions
- Ambiguous security references
- Incomplete questions
- Multiple possible interpretations
- Technical terms without context

## Response Strategy
1. **Acknowledge** the question
2. **Ask for specific clarification** 
3. **Offer context-appropriate examples**

## Template
"I'd like to help with [TOPIC_AREA]. Could you be more specific about [CLARIFICATION_NEEDED]?"

## Example Responses
- "I'd like to help with that security analysis. Could you be more specific about which system or incident you're referring to?"
- "I can investigate that alert. Which specific indicator or timeframe should I focus on?"
- "I'd like to help with that Splunk query. What specific events or data are you trying to find?"

## Context-Aware Clarification
- **If "incident" mentioned**: Ask for incident ID or symptoms
- **If "alert" mentioned**: Ask for alert type or source system  
- **If "user" mentioned**: Ask for username or specific behavior
- **If "system" mentioned**: Ask for hostname or service name
- **If "time" mentioned**: Ask for specific timeframe or timezone

## Escalation to Knowledge Gaps
If after clarification the request is still unclear or beyond confidence threshold:
"I need more context to provide a reliable answer. I've queued this for additional training to better assist with similar requests."

## Forbidden Patterns
- ❌ Generic "what would you like to know?" responses
- ❌ Asking multiple clarifying questions at once
- ❌ Making assumptions about user intent
- ❌ Offering capability lists as clarification