# Plan Skill

## Purpose

This skill is activated when the `/oc plan` command is detected.

## RULES -- ABSOLUTE CONSTRAINTS

1. You MUST NOT create any branch.
2. You MUST NOT create any commit.
3. You MUST NOT create any Pull Request.
4. You MUST NOT modify any file in the repository.
5. Your ONLY action is to post a single comment on the current issue.

## Procedure

1. Read the issue title and body.
2. Read all existing comments on the issue, especially the functional requirement analysis.
3. Examine the codebase to understand affected areas.
4. Compose a detailed technical implementation plan with file-level breakdown.
5. Post it as a comment on the issue using `gh issue comment`.

## Output Format

Your comment MUST follow this structure:

```
## Technical Implementation Plan

### Overview
[Brief summary of the implementation approach]

### Files to Modify
- `path/to/file1`: [What changes are needed]
- `path/to/file2`: [What changes are needed]
- ...

### Implementation Steps
1. [Step 1 description]
2. [Step 2 description]
...

### Dependencies
[Any prerequisites or dependencies]

### Risk Assessment
[Potential risks and mitigation strategies]
```

## Verification

Before finishing, confirm:
- Did I create any branch? If yes, ABORT -- you violated the rules.
- Did I create any PR? If yes, ABORT -- you violated the rules.
- Did I post exactly one comment? If no, something went wrong.
