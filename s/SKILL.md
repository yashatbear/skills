---
name: s
description: Simplify the last response. Re-explain the previous answer in plain, jargon-free language using context from the conversation and any investigation that was done. Use when asked to "simplify", "explain like I'm 5", "say that again simply", or "/s".
---

# S — Simplify Last Response

## When to Use

Run `/s` when the previous response was too technical, too long, or unclear and the user wants a plain-English version.

## How It Works

1. **Re-read your last response** — identify the core point(s) being communicated.
2. **Use conversation context** — pull in relevant background from the investigation, research, or code exploration that led to the response. The user shouldn't need to re-read everything above.
3. **Rewrite in simple terms:**
   - Lead with the bottom line ("Here's what this means:")
   - Replace jargon with everyday words. If a technical term is unavoidable, define it inline in parentheses.
   - Use short sentences. One idea per sentence.
   - Use analogies or concrete examples where they help.
   - Strip filler, caveats, and hedging. Be direct.
   - Keep structure flat — bullet points over nested lists, no headers unless the response covers multiple distinct topics.
4. **Stay faithful** — don't add new information or change the conclusion. Simplify, don't editorialize.

## Rules

- Never longer than the original response. Aim for 30-50% of the original length.
- If the original response was already simple, say so: "That was already pretty straightforward — nothing to simplify."
- Don't dumb down numbers, dates, or names. Keep specifics intact.
- If the user passes an argument (e.g., `/s the part about auth`), only simplify that section.
