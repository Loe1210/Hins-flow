---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline 鈥?challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill 鈥?that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

Most repos have a single context:

```
/
鈹溾攢鈹€ CONTEXT.md
鈹溾攢鈹€ docs/
鈹?  鈹斺攢鈹€ adr/
鈹?      鈹溾攢鈹€ 0001-event-sourced-orders.md
鈹?      鈹斺攢鈹€ 0002-postgres-for-write-model.md
鈹斺攢鈹€ src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
鈹溾攢鈹€ CONTEXT-MAP.md
鈹溾攢鈹€ docs/
鈹?  鈹斺攢鈹€ adr/                          鈫?system-wide decisions
鈹溾攢鈹€ src/
鈹?  鈹溾攢鈹€ ordering/
鈹?  鈹?  鈹溾攢鈹€ CONTEXT.md
鈹?  鈹?  鈹斺攢鈹€ docs/adr/                 鈫?context-specific decisions
鈹?  鈹斺攢鈹€ billing/
鈹?      鈹溾攢鈹€ CONTEXT.md
鈹?      鈹斺攢鈹€ docs/adr/
```

Create files lazily 鈥?only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y 鈥?which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' 鈥?do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible 鈥?which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up 鈥?capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** 鈥?the cost of changing your mind later is meaningful
2. **Surprising without context** 鈥?a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** 鈥?there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
