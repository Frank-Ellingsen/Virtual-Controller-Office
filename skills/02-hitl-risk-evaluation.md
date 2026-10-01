# SKILL: HITL Risk Evaluation & Policy Gate

## Trigger / When to Use
Use when evaluating task risk before executing tool calls or promoting analysis to final reporting.

## Instructions
1. **Assess Impact Level**:
   - **LOW**: Read-only queries, local data summary, public market benchmark research. -> Autonomous Execution.
   - **MEDIUM**: Transforming local DuckDB schema, generating draft dashboards. -> Bounded Autonomy with Notification.
   - **HIGH**: Actionable strategy prescriptions, financial budget reallocations, external communication, database schema changes. -> Mandatory Human Approval Gate.
2. **Format HITL Card**: Present decision summary, confidence score, trade-offs, and alternative options clearly on the Virtual Web UI.

## Constraints
- Mandatory human approval for all HIGH-risk actions.
- Include clear 'Approve', 'Edit', and 'Reject' actions on the web interface.