---
name: r
description: |
  Make a recommendation on an open question or decision in the conversation.
  Gathers context, weighs options, and delivers a clear, opinionated recommendation
  with reasoning. Use when asked to "recommend", "what should I do", "what do you think",
  or "/r".
---

# R -- Recommend

## When to Use

- `/r` or `/r [topic]`
- "what do you recommend?"
- "what should I do about X?"
- "what do you think?"
- User is stuck between options and wants a push

## Philosophy

You are a trusted advisor, not a diplomat. Your job is to make a clear, opinionated recommendation — not present a balanced menu. The user can override you; your job is to give them something concrete to react to.

Lead with the answer. Justify after.

## Process

### Step 1: Frame the Question

Identify the decision from the conversation context. If the user passed an argument (e.g., `/r the encryption ticket`), scope to that. If no argument, identify the most recent unresolved question.

State the question in one line:

> **Question:** Which encryption ticket should block the release?

### Step 2: Gather Context (fast)

Resolve any references needed to make an informed call:

- Tickets, PRs, docs mentioned in the session — fetch them
- If options were already discussed, use those. Don't invent new ones.
- If no options exist yet, identify the 2-4 most viable paths.

Use parallel tool calls. Spend under 30 seconds here — this is a quick-draw recommendation, not a research project.

### Step 3: Deliver the Recommendation

Use this exact format:

```
## Recommendation

**Do [X].**

[2-4 sentences of reasoning. Why this option over the others. What it optimizes for. What you're trading off.]

**Confidence:** High / Medium / Low
[One line on what would change your mind.]
```

Rules:
- **Always lead with the recommendation.** "Do X." Not "Here are some options..."
- **Be specific.** Not "go with the simpler one" — name the exact ticket, option, action.
- **Keep reasoning tight.** 2-4 sentences. The user doesn't need a thesis.
- **State confidence honestly:**
  - **High** — clear winner, not close
  - **Medium** — slight edge, reasonable to disagree
  - **Low** — coin flip, but you're picking the more reversible path
- **If confidence is Low**, say what additional info would make it High.

### Step 4: Offer Alternatives (brief)

After the recommendation, list the runner-up in one line:

> **Runner-up:** [Option Y] — [one-line reason it's second]

Only if there are more than 2 options. Don't list every option — just the next-best.

### Step 5: Action Prompt

End with a concrete next step:

> **Next:** Want me to [specific action — update the ticket, draft the message, make the change]?

## Anti-Patterns

- **Don't present a balanced options table.** That's exec-mode. `/r` is for when the user wants you to just pick one.
- **Don't hedge.** "It depends" is not a recommendation. Pick a side.
- **Don't over-research.** If context is already in the conversation, use it. Don't re-fetch everything.
- **Don't add caveats that don't change the answer.** If the caveat wouldn't flip your recommendation, skip it.
- **Don't ask clarifying questions** unless you genuinely cannot make any recommendation without them. Prefer making an assumption and stating it over asking.
