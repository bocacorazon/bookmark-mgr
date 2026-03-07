---
description: Perform a code review of changes on the current branch against the base branch, focused on Go best practices and spec compliance.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Instructions

Review the changes on this branch against `develop` (or the base branch specified in user input).

Mode policy:
- Default mode is **REVIEW_ONLY**.
- In REVIEW_ONLY, you MUST NOT modify files, apply patches, run write operations, or otherwise change the workspace.
- If asked to fix issues during review, do not fix them inline. Instead, produce findings plus an **AUTOFIX_HANDOFF** section describing exact fix steps.
- Only perform fixes in a separate explicit fix phase/agent invocation.

Focus on:
1. Does the implementation match the spec? (Check for a `spec.md` in the relevant spec directory.)
2. Are there bugs, logic errors, or security issues?
3. Do interface implementations satisfy their contracts?
4. Are error handling patterns consistent — using `fmt.Errorf` with `%w` for wrapping, returning sentinel errors where appropriate, and avoiding swallowed errors?
5. Is the TDD discipline maintained — do tests exist for all new functionality?
6. Are goroutine patterns correct — no goroutine leaks, proper use of `context.Context` for cancellation, channels closed by senders?
7. Is resource cleanup handled — `defer` for Close/Unlock, no deferred calls in loops?
8. Are there any data races — shared state protected by mutexes or channels, no unguarded map access from multiple goroutines?

Do NOT comment on:
- Code style or formatting (enforced by `gofmt`/`goimports`)
- Naming conventions (enforced by `golangci-lint`)
- Import ordering

For each finding, classify as:
- **CRITICAL**: Must fix before merge — bugs, security vulnerabilities, spec violations, broken contracts, data races, goroutine leaks
- **IMPORTANT**: Should fix — logic issues, missing edge cases, incomplete error handling, missing context propagation
- **MINOR**: Nice to have — better abstractions, documentation improvements

Only set `HUMAN_DECISION_REQUIRED: yes` when there are multiple valid fix approaches and a human must choose among alternatives. If there is a clear technical fix, set it to `no` and provide the fix directly.

Determinism rules:
- Always emit the required output format exactly.
- Never infer “no issues” from attempted edits.
- If output is malformed or incomplete, treat it as a failed review and report at least one CRITICAL finding explaining the format failure.

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

Optional handoff section when user requests fixing during review:
```
## AUTOFIX_HANDOFF
- <ordered actionable fix step 1>
- <ordered actionable fix step 2>
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
