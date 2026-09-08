---
status: "{proposed | accepted | rejected | deprecated | superseded by ADR-NNNN}"
date: "{YYYY-MM-DD the decision was made}"
decision-makers: "{who made the call}"
---

# NNNN. {Short title, naming both the problem and the chosen solution}

## Context and Problem Statement

{Two or three sentences on the situation that forces a choice. Name the
concrete architectural elements involved — files, configs, components — so the
scope of the decision is unambiguous. Phrasing it as a question helps.}

## Decision Drivers

- {A quality, constraint or force that pushes on the choice}
- {Another}

## Considered Options

- {Option 1}
- {Option 2}
- {Option 3}

## Decision Outcome

Chosen option: "{Option N}", because {the justification — which driver it
satisfies that the others do not}.

### Consequences

- Good, because {what improves}
- Bad, because {what this costs — an ADR with no Bad entries is not finished}
- Neutral, because {a trade-off that is neither, or a decision deliberately deferred}

### Confirmation

{How compliance is verified: a CI job, a test file, a config invariant, a
manual check. If nothing enforces this decision, say so plainly.}

## Pros and Cons of the Options

### {Option 1}

- Good, because {argument}
- Neutral, because {argument}
- Bad, because {argument}

### {Option 2}

- Good, because {argument}
- Bad, because {argument}

## More Information

{Supporting links: docs, the blog post or commit where the decision played out,
related ADRs. Note here when the decision should be revisited.}
