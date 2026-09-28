# Agent inspection record — no human source-read escalation

CODE-READ-ID: AGENT-READ-002
Observed failure: unusable impact verdicts followed by ordinary persisted decisions.
Why evidence was insufficient: traces proved None helper results and small-impact flags, but did not
by themselves establish whether small was an explicit fallback or another conversion.
Source inspected: inherited/llm_utils.py impact response parsing (535–556), inherited/notice_validator.py
termination handling (205–239) and impact fallback (273–307). No inherited edits.
What was learned: missing verdict returns None; validator's else branch treats None as small (+0.10)
without distinguishing it in the validity flag. Missing prior termination continues scoring.
Missing harness/evidence capability: coarse MODEL_FAILURE label conflated cause; gate ERROR obscured
independent observations; application flags did not identify a defaulted impact assessment.
Harness improvement made: versioned request/parser/application audit, independent observable checks,
coverage/outcome separation, retained SAFETY-001 failure-handling evidence.
Could the same code read be avoided next time? The retained audit explains this branch; ideally a
future implementation explicitly reports parser status and fallback disposition in its output contract.

This was an AI agent's limited source inspection, not a reported human code read or broad review.
