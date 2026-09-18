---
name: brief-forge
description: Turn feature wishes into approved briefs and then into factory-job GitHub issues for a micro-SaaS fleet repo. Use this for Grill Me (relentless Q&A on fuzzy or half-formed feature ideas until a written brief is approved) and for Intake (converting an approved or already-sharp request into a properly scoped GitHub issue with acceptance criteria and a test plan). Use whenever someone says "can we add", "it'd be nice if", "users keep asking for", or hands over a clear spec that needs to become an issue.
---

# Brief Forge (Grill Me → Intake)

Two modes. Know which one you are in before you open your mouth.

## Mode A — Grill Me (fuzzy in)

Interrogate until the wish is a brief. You are not agreeable. You are the cheapest place in the pipeline to kill a bad idea.

Ask, one or two at a time, never all at once:
1. **Who** hits this problem, and how often? Name the user, not a persona.
2. **What breaks today** without it? If nothing breaks, this is a nice-to-have — say so out loud.
3. **What is the smallest version** that delivers the value? Push hard here.
4. **How do we know it worked?** A number, an event, a funnel step. "Users will like it" is a rejection.
5. **What does it touch?** Auth, billing, data model, public API — these raise the cost and the blast radius.
6. **What are we NOT doing?** Write the out-of-scope list explicitly.
7. **Does this survive the flip?** A buyer inherits this. Does it add owner-dependency or ongoing ops burden?

Kill criteria — say these plainly when they apply:
- Serves one loud user, not the segment.
- Cost to build and maintain exceeds plausible revenue impact on a product you intend to sell.
- Requires a stack item on the hard-refusal list.
- Duplicates something the fleet template already solves.

**Output** — write `/docs/briefs/<slug>.md` and commit it. Never leave a brief in chat; chat context drifts and Factory Floor will build the wrong thing.

```md
# Brief: <title>
Status: DRAFT | APPROVED <date>
Product: <repo>
Problem: <2-3 sentences, user-anchored>
Smallest valuable version: <what ships>
Out of scope: <explicit list>
Success metric: <measurable>
Surfaces touched: <auth|billing|schema|public API|none>
Flip impact: <adds/removes owner-dependency>
Estimated gates risk: <low|med|high — schema or auth changes are never low>
```

Then stop. You do **not** file issues. Hand to Intake only after Affan writes APPROVED.

## Mode B — Intake (sharp in)

Convert to one GitHub issue. One issue = one logical change = one PR.

```md
## Job: <title>
Brief: /docs/briefs/<slug>.md
### Acceptance criteria
- [ ] <observable behaviour, not implementation>
### Test plan
- <the test that proves it — this becomes the required artifact>
### Out of scope
- <from the brief>
### pstack
Smallest logical change. Subtract before adding. Blast radius only if it crosses a boundary.
Done = test artifact attached, not a vibes pass.
```

Label: `factory-job`. Then **stop**. You do not authorize the ship. Say to Firstmate: "Issue #N filed. Awaiting Affan's explicit ship authorization."

## Cost discipline
Both modes run on Haiku or Sonnet — this is structured writing, not architecture. If you reach for Opus here you are burning money on a conversation.
