# World-Model Lessons

Use this reference when a JEPA design touches LeCun's world-model agenda, objective-driven agents, planning, action-conditioning, or high-dimensional continuous noisy data.

## Core Claim

The LeCun lecture and slides argue that real-world intelligence needs learned world models over high-dimensional, continuous, noisy observations. Language-like token prediction is not enough for physical, sensory, scientific, engineering, or finance-like systems.

Course translation:
- JEPA is a way to learn abstract state representations.
- A world model predicts future or counterfactual state representations.
- Planning searches over actions to optimize objectives and guardrails.

## What World Models Should Be

A world model should be an action-conditioned predictor in abstract representation space.

```text
observation -> abstract state representation
action/intervention -> world model
predicted outcome -> outcome representation
objective/guardrails -> search over actions
```

It should not be treated as:
- A full raw simulator.
- A video generator.
- A digital twin that reproduces every detail.
- A black-box trading rule.

## Why Representation Space Matters

Raw prediction is underdetermined. In video, many futures are plausible; exact pixels include unknowable detail. In markets, exact future ticks include microstructure noise, hidden liquidity, exogenous events, and participant behavior the model cannot observe.

Therefore:
- Predict useful latent structure.
- Let representations discard unpredictable nuisance detail.
- Evaluate whether the retained structure supports downstream objectives.

## Objective-Driven Architecture

LeCun's framing separates:
- Perception: encode observations into state representations.
- World model: predict outcomes of actions/interventions.
- Objective: score task completion.
- Guardrail objective: score safety/constraint satisfaction.
- Planner: search/optimize actions.

For JEPA model design:
- Keep representation learning separate from decision policy at first.
- Add small heads for objectives or constraints only after representation quality is established.
- Use planning/model-predictive control framing only when actions and constraints are explicit.

## Small Heads On Representations

The lecture's Q&A supports a practical evaluation pattern: train small heads on top of learned representations for constraints/objectives.

In this skill:

```text
frozen encoder -> latent -> small probe head -> future property label
```

Examples:
- Volatility bucket head.
- Liquidity-worsening head.
- Regime-change head.
- Constraint-risk head.
- Depth/segmentation/action-recognition head for visual systems.

Small heads test whether the representation contains accessible structure. They do not prove the full system can trade, plan, or act safely.

## Hierarchy

Hierarchical world models predict at different time scales and abstraction levels.

Design implication:
- Start with one horizon and one abstraction.
- Add hierarchy only when a single-scale model is clearly insufficient.
- For market data, possible hierarchy levels are tick/order-book, intraday regime, daily regime, and cross-asset macro state. Do not combine these in a first experiment.

## Trading Interpretation

Finance is a plausible complex-system domain because it is high-dimensional, continuous, noisy, and partially observed. That does not make JEPA a trading recipe.

Use the world-model lens to design research questions:
- Can a JEPA learn market-state representations?
- Can those representations support small heads for volatility, liquidity, flow, or regime?
- Can action-conditioned variants later model execution outcomes?

Keep live trading, position sizing, and broker integration out of scope until the representation passes leakage-safe probes and baseline comparisons.
