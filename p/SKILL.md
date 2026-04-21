---
name: p
description: |
  Proceed with the recommended action from the previous response. Use when the
  user says "/p", "proceed", "go ahead", or "do it" after you've offered a
  recommendation or proposed next step.
---

# P — Proceed

## When to Use

- `/p` or `/p [optional note]`
- User wants you to execute the action you just recommended, without restating it

## Process

1. **Identify the pending action.** Look at your last response. It should end with a concrete proposal — a recommendation from `/r`, a "Next:" prompt, a drafted message awaiting send, a plan awaiting execution, etc. That is the action to proceed with.

2. **If the action is ambiguous**, pick the most recent explicit "Next:" / "Want me to..." / "Shall I..." offer. If there are multiple, ask which one — briefly. Don't re-litigate the decision.

3. **If the user passed a note** (`/p but use draft instead`), apply it as a modifier to the action, not a new request.

4. **Execute.** Just do it. Don't re-explain what you're about to do in more than one short sentence. Don't re-derive the recommendation. The user already agreed.

5. **Report the result** tersely: what changed, what's next (if anything). Same terseness rules as any end-of-turn summary.

## Anti-Patterns

- **Don't re-summarize the plan** before executing. The user said proceed — proceed.
- **Don't ask for confirmation again** on the same action. `/p` is the confirmation.
- **Don't expand scope.** Execute exactly what you proposed, not an improved version. Scope is bounded by your **immediately preceding question**, not by a multi-step pattern from earlier in the session. If your last question offered one step ("add to revs doc?"), `/p` authorizes that one step — not the propose→apply→cleanup routine you happened to follow on an earlier round. When in doubt, do the smaller thing and let the user say `/p` again.
- **Don't skip risky-action confirmation** that the base system requires (destructive ops, sending messages to third parties, etc.). `/p` authorizes the specific action you proposed, not a broader class.
- **If nothing was proposed**, say so in one line and ask what to proceed with. Don't invent an action.
