````chatagent
---
description: Project-specific SKRunner review agent
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Instructions

Review the changes on this branch against `main` (or the base branch specified in user input).

Focus on:
1. Does the implementation match the active spec and task scope?
2. Are there bugs, logic errors, or security issues?
3. Are IO/service boundary contracts respected?
4. Is error handling explicit and safe?
5. Are tests present for new behavior?

Do NOT comment on:
- Formatting/style-only issues
- Naming preferences
- Import ordering

For each finding, classify as:
- **CRITICAL**: Must fix before merge
- **IMPORTANT**: Should fix
- **MINOR**: Nice to have

Output format:
```
## Review Summary
- CRITICAL: <count>
- IMPORTANT: <count>
- MINOR: <count>
HUMAN_DECISION_REQUIRED: <yes|no>

## Findings

### [CRITICAL|IMPORTANT|MINOR] <short title>
**File:** <path>
**Line:** <line or range>
**Issue:** <description>
**Suggested fix:** <suggestion>
```

If there are no findings, output:
```
## Review Summary
- CRITICAL: 0
- IMPORTANT: 0
- MINOR: 0
HUMAN_DECISION_REQUIRED: no

No issues found.
```

````
