---
name: agent-debate
description: Run a structured two-agent design dialogue (initiator + challenger) for complex architectural decisions where multiple plausible models exist and trade-offs are non-obvious. Produces three artifacts — ADR, human-readable architecture overview, component-level implementation plan. Use when a single agent's first opinion is unlikely to seriously consider the alternatives, and the human can provide constraints + final judgment but doesn't want to enumerate the design space themselves. Typical run: 10-20 rounds, several human interjections.
---

# Agent debate

A structured async dialogue between two agents for co-designing complex
architectural or strategic decisions. The dialogue is dialectic by design:
one agent proposes, the other challenges, both refine, and the human
intervenes at specific moments to provide constraints, correct
assumptions, and approve.

This document is the **playbook**. Both agents must read it before round 1.
It is intentionally agent-agnostic — Claude, Codex, or any sufficiently
capable agent can play either role, as long as both follow these rules.

## Distributing the playbook to both agents

Different agents discover instructions differently:

- **Claude Code** auto-loads this file from `~/.claude/skills/agent-debate/SKILL.md`.
- **Codex / other agents** typically don't see Claude Code's user-level
  skills. They need the playbook in a path they read.

**At debate kickoff**, copy this file into the project so both agents see
the same rules:

```bash
mkdir -p debate
cp ~/.claude/skills/agent-debate/SKILL.md debate/PLAYBOOK.md
```

(Or symlink it; or hand-paste into the project's docs folder. The
canonical source stays in `~/.claude/skills/agent-debate/SKILL.md`; the
debate folder gets a copy that travels with the project.)

**The opening bead/round 1 task must reference the playbook explicitly**,
e.g., "Both agents: read `debate/PLAYBOOK.md` before responding. It
defines round structure, markers, anti-patterns, and the final
deliverable shape." This way the receiving agent always has the playbook
in scope, regardless of what skill-loading mechanism it uses.

If the human invokes the format via a Claude Code skill on one side and a
direct prompt on the other, the playbook copy in the debate folder is
what synchronizes the two.

## When to use this playbook

Use when:

- the decision space is large (multiple plausible models, architectures,
  or strategies, no obviously-right answer);
- the decision will be costly to revisit later;
- a single agent's first opinion is unlikely to consider the alternatives
  seriously;
- the human can provide constraints, domain facts, and final judgment but
  doesn't want to enumerate the design space themselves;
- there is enough scope for 10-20 rounds of refinement.

Don't use when:

- the decision is mostly known and just needs to be written down;
- time pressure prevents iteration;
- the question is purely about implementation detail with no open
  architectural choice;
- one expert agent's opinion is genuinely sufficient.

## Setup

### Two agent roles

**Initiator** (round 1, alternating thereafter): writes the opening
proposal. States the problem, proposes a model, **explicitly enumerates
2-3 alternative shapes**, recommends one with reasons, lists open
questions for the challenger.

**Challenger** (round 2, alternating thereafter): reviews critically.
Marks each thesis AGREE / CHALLENGE / REFINE. Adds new theses where the
initiator's frame missed something. Actively looks for alternatives the
initiator did not enumerate.

Both agents alternate as initiator/challenger across rounds. Convergence
happens when both agents agree on a numbered set of items.

### Human's role

The human is NOT the design authority — they are the constraint provider
and final arbiter. Their actual contributions:

1. **Frame the problem** at the start.
2. **Provide context** the agents can't observe (codebase state, team
   capacity, prior decisions, organizational realities).
3. **Push back when convergence feels fast** — "are you sure? did you
   consider X?".
4. **Surface buried assumptions** when reading the consensus and noticing
   an unstated premise.
5. **Correct domain facts** — agents will guess wrong about your
   environment.
6. **Add use cases** the agents don't know about.
7. **Approve the final plan** only when it's been challenged enough.

The human's most useful instruction, repeated as needed: *"Only approve
when you're sure the chosen idea is valid, sane, and consistent."*

### Transport

The format works with any combination of file storage + task tracker.
Concrete recommendation:

- **Markdown files** in a `debate/` (or `debate2/`, `debate3/`) folder are
  the canonical record. Filename: `roundN_<author>_<short-topic>.md`.
- **Beads tasks** (or any equivalent task tracker both agents can read
  and write — Linear, GitHub Issues, Jira, etc.) carry the same content
  as the file body, used as the agent-to-agent handoff signal.
- **One epic per debate topic**, with rounds as children.
- Closing a round task = handoff to the other agent. The handoff reason
  summarizes what the next agent must address.
- If the task tracker auto-closes the epic when a child closes, re-open
  it explicitly each time.
- The playbook itself (`debate/PLAYBOOK.md`) lives alongside the rounds
  so both agents can reference it.

The minimum requirement: each agent's round must be persisted somewhere
the other agent can read, with an unambiguous "your turn" signal between
rounds. If your tooling doesn't have a task tracker, plain markdown
files plus a "next-up" pointer in a `debate/STATE.md` file works.

## Round conventions

### Markers
Each thesis or item gets one of:
- **AGREE** — accept as stated
- **CHALLENGE** — disagree, with reasons and counter-proposal
- **REFINE** — agree direction, propose adjustment

### Numbered theses
- Initiator's opening: `T1, T2, ...`
- Challenger's new theses (introduced later): `C-T11, C-T12, ...`
- Sub-debate within a sub-topic: prefix the topic letter, e.g., `O-T1`
  for the Output sub-debate, `Q-T1` for the Query sub-debate

### Round close
Every round ends with **OPEN FOR NEXT ROUND** — a numbered list of items
the next agent must address. This prevents debate drift and makes the
handoff explicit. Without it, the next agent guesses and frequently
misses items.

## Round types

### Round 1 — Opening

Initiator: state the problem. Propose a model. **Enumerate at least 2
alternative shapes that aren't the recommended one, with reasons for
rejecting them.** Recommend a model. List open questions.

Critically: enumerate alternatives EXPLICITLY in the opening, not after
the human pushes back. Anchoring on the first reasonable model and never
seriously considering alternatives is the most common failure mode of
this format.

### Round 2 — First challenge

Challenger: AGREE / CHALLENGE / REFINE per thesis. Add new theses where
the initiator's frame is incomplete. **Actively look for alternatives
the initiator did not enumerate** — propose them, even briefly, so they
are on the record as considered.

### Rounds 3 to N/2 — Refinement

Both agents converge on details: scope of components, sequence of
interactions, deliverables per phase, edge cases. Each round still uses
markers; convergence is measured by how many items move from
CHALLENGE/REFINE to AGREE.

### One step-back round (somewhere around round N/2)

At least once per debate, ideally before "the final plan" is in sight,
one agent **must** explicitly ask: "Did we anchor on the first reasonable
model? Are there alternative shapes we never enumerated? Are there
components we silently assumed someone else owns?"

Step-back rounds catch anchoring failures that refinement rounds cannot.
The human can also force a step-back round by saying "step back and
challenge" or equivalent.

A good step-back round:
- enumerates alternatives that were never seriously considered (e.g.,
  build vs wrap, our model vs a standard format, our team owns vs
  delegate to platform team);
- self-criticizes positions the agent took in earlier rounds;
- challenges the human's framing where applicable;
- lists external decisions that need named owners (gates).

### Convergence rounds (N-2, N-1)

Both agents agree on the consensus, with explicit **gates** for items
requiring human or external decisions. A gate has:
- a name
- a precise question
- a named owner (human or external)
- what it blocks if unanswered

Anything that can't be agent-decided becomes a gate, never a "we'll
figure it out later" item.

### Final plan round (round N)

One agent writes the three deliverables. The other agent reviews against
an audit checklist (see below). Human approves.

## Anti-patterns to actively avoid

1. **Anchoring on the first model.** Initiator proposes Shape A, every
   subsequent round refines A. Counter: round 1 must enumerate alternatives;
   step-back round must happen at least once.

2. **Agreement-by-exhaustion.** Agents tire of debating and agree to
   converge without resolving real disagreements. Counter: human pushes
   back when convergence feels fast or when alternatives weren't seriously
   considered.

3. **Buried open questions.** "We'll figure that out later" — but later
   never comes. Counter: every open item becomes either (a) in scope
   for the current round, or (b) a numbered gate with named owner.

4. **Silent defaults.** Agent picks a default without flagging it as a
   choice. Counter: every default with a non-obvious choice is called
   out as a decision in the ADR.

5. **Imitation rounds.** A round that just rephrases the previous round
   with no new information. Counter: if an agent has nothing new to add,
   close the debate or escalate to human.

6. **Premature plan.** Writing implementation detail before the model is
   solid. Counter: clear separation between model rounds (1 to N/2) and
   plan rounds (N/2 to N).

7. **Quietly imposing scope.** Agent describes a feature as in-scope when
   it's actually a major undertaking. Counter: plan must distinguish
   `build` / `wrap` / `configure` / `defer` per component.

8. **Restartable debates.** Final plan doesn't document rejected
   alternatives, so a future reader reopens the debate. Counter: ADR
   must have an "Alternatives considered and rejected" section with
   reasons.

## When to ask the human / when to loop autonomously

### Always interrupt the loop and ask the human

- **Product decisions**: timeline, priorities, what to ship in which
  quarter, what use cases are real.
- **Org boundaries**: which team owns what, named platform owners for
  components agents propose to wrap.
- **Domain facts agents can't observe**: proportion of X in production,
  what the user actually wants, technology in active use.
- **Buried assumptions newly visible**: e.g., "are these stored in our
  system or theirs?", "is the dataset semantically owned by us or by
  the source?".
- **Scope changes**: new use case appears mid-debate.
- **Decision gates that affect implementation**: storage substrate,
  build vs wrap, identity propagation choices.
- **Final plan approval**.
- **Cross-agent agreement that turns out to be on a wrong premise**.

### Sometimes ask the human

- **Tie-breaking** when agents disagree after 2-3 rounds with no
  convergence.
- When one agent challenges a foundational assumption the human
  originally provided (the human's earlier instruction may need
  updating in light of new information).
- When the agents are converging suspiciously fast.
- When a step-back round surfaces something material.
- When a separate question to the human (asked outside the debate)
  yields an answer that may change the agents' reasoning — agents
  should be told and asked to evaluate alignment.

### Never ask the human

- Architectural choices within the agreed scope.
- Refining each other's positions.
- Internal model decisions that don't affect product.

### Loop autonomously

- Initiator writes opening → automatically hand to challenger.
- Challenger writes response → automatically hand back to initiator.
- Both agree on a round close → next round begins.
- Refinement rounds where both have things to address.
- Scenario-coverage rounds (S1, S2, ...).
- Failure-mode enumeration.

### Pause naturally for human review

- After opening (let human verify the framing).
- Before any step-back round (let human decide if it's needed).
- Before final plan authoring (let human gate-keep the model).
- After final plan, before approval.

## What the agents must DO

### Self-criticism, rolled forward
When you change your position across rounds, say so explicitly. Carry
self-criticism forward into the final ADR's "Alternatives considered"
section. Don't hide that round 2 had position X and round 6 walked it
back — that history is part of the audit trail.

### Audit checklist before the final plan
The agent who hands off authorship of the final plan owes the receiving
agent a comprehensive checklist of items pinned across all rounds.
Without it, items get silently dropped because the writing agent has
narrower context than the reviewing agent. Format: numbered list, each
item references the round it came from.

### Three-artifact final output

The final deliverable is three documents:

1. **ADR** — decisions, alternatives considered (with rejection
   reasons), consequences. Audience: future engineers asking "why did
   we choose X?".
2. **Architecture overview** — human-readable target architecture.
   Audience: product/leadership readers, accessible to non-engineers.
   Use plain language, problem-statement-before-solution, per-stakeholder
   benefits, concrete examples, scenario-based "How the architecture is
   used".
3. **Component-level implementation plan** — components, sequencing,
   gates, scenarios, failure modes. Audience: the team executing.

The split is deliberate. One document trying to serve all three
audiences serves none of them.

### Use the human's diagrams or documents when provided

If the human provides a diagram or document partway through the debate,
add an explicit reconciliation section to the final plan that maps the
human's entities to the agents' model. Note where they conflate concepts
the agents kept separate, and where the agents' framing should adopt
their wording.

## Final deliverable structures

### ADR template

```
# ADR-NNN: <title>

Date / Status / Decision owners / Related artifacts

## Context
Why this decision is needed, what problem it solves.

## Decision
The chosen approach, in one paragraph + numbered details.

## Additional decisions
Sub-decisions made along with the main one.

## Alternatives considered
Each alternative with: description, decision (selected/rejected/deferred),
reason. Cover everything seriously enumerated across the debate, not just
what survived to the end.

## Consequences
Positive and negative. Be honest about costs.

## Implementation notes
Incremental delivery slices.

## Open points
Items still gated on external validation, with named owners.
```

### Architecture overview template

Aim for non-engineering readability. Suggested structure:

- Plain-language opening (the main idea in one diagram-free paragraph).
- Problem statement before the solution.
- Design principles, named.
- Core concepts, each named with one-paragraph definition.
- Logical architecture (text-based or actual diagram).
- Main services and responsibilities.
- "How the architecture is used" — scenario-based explanation per main
  use case.
- Schema model / data shape if relevant.
- Policy, identity, audit.
- Storage / external substrate strategy.
- Evolution path (incremental slices).
- "What this architecture gives us" — per-stakeholder benefits.
- Summary.

The "What this gives us" per-stakeholder section is what makes this
document accessible to product/leadership. Don't skip it.

### Implementation plan structure

Sections:

1. **Layer/component model** with named layers.
2. **Lifetime / state model** where relevant.
3. **C3 component diagram** (mermaid or equivalent) plus tables.
   Each component: delivery mode (`build` / `wrap` / `configure` /
   `defer`), named owner, responsibility, main consumers. Cells
   marked `TODO: confirm with <owner>` are acceptable for the first
   draft; named owners must be filled before commitment.
4. **Sequenced delivery slices** (not just a flat list of tasks).
   Each slice should have a visible product outcome.
5. **Required capabilities per slice**.
6. **Storage / external substrate strategy**.
7. **Addressing / API surface**.
8. **External gates** — decisions blocking implementation, named owners,
   what they block if unanswered.
9. **Alternatives considered and rejected** — reproduce the ADR section
   so the plan is self-contained.
10. **Scenario checklist** — happy paths, edge cases, failure paths.
11. **Failure modes inline** with mitigations (not in an appendix).
12. **Inherited consensus** from prior debates / decisions.
13. **Team split** — who owns what.
14. **Reconciliation** with any human-provided diagrams or documents.
15. **Explicit non-goals** — what we are NOT doing in this scope.
16. **Open product questions** — things requiring human/business
    decisions, with options enumerated.

## Naming conventions

Files:
- `roundN_<author>_<short-topic>.md`
- Final deliverables: `target_architecture.md`, `adr_NNN_<topic>.md`,
  `component_diagram_and_plan.md`
- Side artifacts (optional, useful during debate): `consensus.md`,
  `risky_assumptions.md`

Beads / task tracker:
- Epic: descriptive title for the debate topic
- Tasks: `<author> round N: <one-line summary>`
- Labels: `agent-debate`, `architecture` (or relevant domain), `<author>`,
  `round-N`

## How a debate ends

A debate is complete when:

1. Both agents AGREE on the model and scope (consensus is a numbered list,
   not a vibe).
2. The three artifacts are written.
3. External gates are documented with named owners.
4. The human has reviewed the three artifacts and approved (possibly
   with revision remarks).

If a debate stalls (one agent keeps challenging without converging, or
the human keeps pushing back without resolution), it usually means a
foundational constraint is missing. Pause the debate, ask the human for
the missing constraint, then resume.

## Estimated effort

A debate typically takes 10-20 rounds spread over 4-8 hours of human
attention (the agents do the bulk of writing; the human's contribution
is targeted intervention at the right moments). Final artifacts are
roughly 30-50 pages combined.

If a debate is heading toward 30+ rounds, it likely needs to be split:
either the topic is too broad (split into sub-topics, each its own
debate), or there is a missing constraint causing churn (escalate to
human).

## Tips from real runs

- **First framing usually undersells the design space.** The human's
  early clarification ("the focus is X and Y") often reframes the debate
  before round 2. Treat the human's first follow-up after the opening as
  load-bearing.
- **A diagram from the human at any point is a gift.** Reconcile it
  explicitly — entities they conflate often surface decisions agents
  silently made.
- **Mid-debate use-case additions are common.** Don't treat them as
  scope creep; treat them as additional constraints the model must
  accommodate (or explicitly defer).
- **The human will sometimes correct domain facts.** Agents will guess
  wrong about technology in active use, proportion of legacy artifacts,
  team capacity. Concrete corrections from the human override agent
  defaults.
- **The phrase "should X be coupled?" usually surfaces a buried
  decision.** Treat it as a request to make an implicit choice explicit,
  not as a request to change the architecture.
- **When the human asks one agent the same question they asked the
  other**, the goal is to verify alignment without anchoring. The agent
  receiving the question should answer fresh, then check alignment.
- **The audit checklist before final plan is non-negotiable.** Without
  it, items pinned across 10+ rounds get silently dropped because the
  plan-writing agent has narrower working context than the reviewing
  agent.
