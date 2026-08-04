# Delivery

Hins-flow owns the delivery sequence. This adapter implements one current slice;
it never starts a full verification pass, review, commit, merge, or downstream
stage on its own.

## Workspace

- Read-only work uses the current checkout.
- Quick low-risk edits may use a clean current checkout when unrelated changes
  can be preserved exactly.
- Standard, Large, and high-risk mutations use an isolated feature branch and
  worktree.
- Commit only a complete, verified slice. Use Simplified-Chinese commit prose
  and exclude unrelated files. Never rewrite history implicitly.

## Behavioral delivery

Use the test seam agreed during planning. Do not ask the user to confirm it
again unless new evidence invalidates it.

For each vertical slice:

1. write one behavior-level failing test;
2. run it and record `focused-red` as `expected-failure`;
3. add the smallest implementation;
4. run the same seam and record current `focused-green` evidence;
5. perform bounded cleanup without speculative abstraction.

Tests observe public behavior and survive internal refactors. Mock true external
boundaries; prefer local substitutes for owned persistence or services. Replace
obsolete shallow tests when a deeper interface becomes the real test surface;
do not layer redundant tests indefinitely.

## Merge conflicts

Resolve an in-progress merge or rebase hunk by hunk from each side's primary
intent. Preserve both intents where compatible. When incompatible, follow the
stated integration goal and record the trade-off. Verify the integrated snapshot
before continuing. Abort, discard, or history rewriting requires explicit user
direction.
