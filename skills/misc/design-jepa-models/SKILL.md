---
name: design-jepa-models
description: Design, review, prototype, and evaluate JEPA models, joint-embedding predictive architectures, V-JEPA/I-JEPA-style representation learners, action-conditioned world models, and JEPA-inspired models for time series or trading research. Use when the user asks for JEPA architecture design, masking/target choices, collapse prevention, latent probes, toy JEPA experiments, market-data JEPA research, world-model planning, or critique of a JEPA paper/model/implementation.
---

# Design JEPA Models

Use this skill to turn a vague JEPA idea into a research-grade design spec: data, context, target, representation, masking, architecture, collapse prevention, probes, validation, and failure modes.

## Workflow

1. **Classify the request branch.**
   - New model design or architecture review: read `references/core-jepa-design.md`.
   - World-model, planning, objectives, actions, or LeCun lecture framing: read `references/world-model-lessons.md`.
   - Trading, finance, probes, labels, baselines, leakage, or backtesting: read `references/evaluation-and-trading.md`.
   - CPU toy experiment, tutorial implementation, or micro prototype: read `references/toy-experiments.md`.
   - Source-grounded explanation, paper comparison, or paper deep dive: read `references/source-map.md` and `references/paper-deep-dives.md`, then the relevant paper file.
   - Recap of the learned JEPA concepts: read `references/course-recap.md`.
   - LeCun world-model lecture/slides framing: read `references/lecun-lecture-digest.md`.

2. **Write the JEPA spec before proposing code.**
   Include these fields, marking unknowns explicitly:
   - Data domain and observation unit.
   - Context available at decision/inference time.
   - Target hidden during pretraining.
   - Latent abstraction the model should preserve.
   - Nuisance detail the representation may discard.
   - Masking strategy and shortcut risks.
   - Context encoder, target encoder, predictor, and target-update rule.
   - Loss, collapse-prevention mechanism, and collapse diagnostics.
   - Probe labels, fair baselines, split protocol, and success criterion.

3. **Hold the representation line.**
   Treat JEPA as representation learning unless the user explicitly moves to decision-making. A good JEPA result means the latent carries useful out-of-sample structure; it does not imply a tradable strategy, robot policy, or safe planner.

4. **Use small heads as the first evaluation.**
   For a frozen encoder, prefer simple probes over full fine-tuning. For market data, start with future volatility/liquidity/imbalance buckets before noisy direction or PnL labels.

5. **Finish with an audit.**
   Before finalizing any design, report:
   - What could collapse.
   - What could leak future information.
   - What baseline must be beaten.
   - What positive result would and would not prove.
   - Which primary source most directly supports the design choice.

## Output Shape

For design tasks, produce a compact spec with:

```text
Objective:
Data:
Context:
Target:
Mask:
Architecture:
Target update:
Loss:
Collapse checks:
Probe labels:
Baselines:
Validation split:
Success means:
Does not prove:
Next experiment:
```

For review tasks, lead with findings ordered by risk:

```text
Critical issues:
Major issues:
Missing controls:
Good design choices:
Minimal next fixes:
```

## Guardrails

- Prefer representation-space prediction over raw reconstruction for high-dimensional, continuous, noisy data.
- Prefer mechanically defined labels and frozen probes before strategy or policy claims.
- Treat finance/trading designs as research methodology, not financial advice.
- Ground non-obvious claims in the source map or the user's local artifacts when available.
