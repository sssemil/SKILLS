---
name: codex-coop
description: Co-operative workflow with OpenAI Codex CLI for plan review and pre-commit code review. Use this skill whenever Claude is about to present a plan to the user, propose an implementation approach, or commit code changes. Also triggers when the user mentions "codex", "co-op", "second opinion", "review with codex", or asks Claude to validate plans or changes before proceeding. This skill should fire before ANY plan is shown to the user and before ANY git commit — even if the user doesn't explicitly ask for Codex review.
---

# Co-op with Codex

This skill defines a two-agent workflow where Claude collaborates with OpenAI Codex CLI to get a second opinion before presenting plans or committing code. The goal is to catch blind spots, validate approaches, and improve output quality by routing work through an independent reviewer before the human ever sees it.

## Prerequisites

- `codex` CLI must be installed and available on PATH
- A working OpenAI API key configured for Codex

Verify availability before first use:

```bash
which codex && codex --version
```

If `codex` is not found, inform the user and skip the review steps (proceed normally without Codex review).

---

## Workflow 1: Plan Review

**When:** You have drafted a plan, implementation approach, architecture decision, or multi-step strategy — and are about to present it to the user for review.

**Before showing the plan to the user**, submit it to Codex for independent review:

```bash
codex exec """
review my plan and suggest improvements, flag risks, or confirm it looks good:

<INSERT FULL PLAN HERE>
"""
```

### How to handle the response

1. **Read Codex's feedback carefully.** Look for:
   - Missed edge cases or failure modes
   - Better ordering of steps
   - Unnecessary complexity that can be removed
   - Missing dependencies or prerequisites
   - Alternative approaches worth considering

2. **Integrate valid suggestions** into your plan before presenting it to the user. You do not need to accept everything — use your judgment. Discard feedback that is incorrect, irrelevant, or lower quality than your original approach.

3. **Present the improved plan to the user.** Briefly note that you consulted Codex and incorporated feedback where relevant, so the user has full transparency into the process.

---

## Workflow 2: Pre-Commit Code Review

**When:** You have made code changes and are about to commit them (or present final changes to the user).

**Before committing**, ask Codex to review the uncommitted diff:

```bash
codex exec """
review the uncommitted changes in this repository. Flag bugs, style issues, missing error handling, or anything that looks off. If everything looks good, confirm.

$(git diff)
$(git diff --cached)
"""
```

### How to handle the response

1. **Review Codex's suggestions** against the actual changes.

2. **Apply fixes** for any legitimate issues found (bugs, missing error handling, typos, logic errors).

3. **Ignore suggestions** that are stylistic preferences without substance, incorrect, or would introduce regressions.

4. **Then proceed** with the commit or present the finalized changes to the user.

---

## General Rules

- **Always run Workflow 1 before presenting a plan.** Do not skip this step, even for small plans — a quick "looks good" confirmation from Codex is still valuable.
- **Always run Workflow 2 before committing.** This is your last line of defense before code goes in.
- **Be transparent.** When presenting to the user, mention that Codex reviewed the work. If Codex caught something meaningful, briefly note what changed.
- **Handle failures gracefully.** If the `codex` command fails, times out, or is unavailable, proceed without it — do not block the user's workflow. Mention that Codex review was skipped and why.
- **Don't loop endlessly.** One round of Codex review per plan or commit is sufficient. Do not re-submit to Codex after incorporating feedback unless the plan changed substantially.
