# Paper Deep Dive: A Path Towards Autonomous Machine Intelligence

Use this reference for LeCun's autonomous intelligence architecture, the motivation for JEPA, world models, objective-driven agents, and cautious translation to finance.

## Sources

- Yann LeCun, "A Path Towards Autonomous Machine Intelligence", OpenReview PDF: https://openreview.net/pdf?id=BZ5a1r-kVsf
- Related JEPA framing in the LeCun world-model lecture digest: `references/lecun-lecture-digest.md`

## Core Contribution

This is a position paper, not an implementation paper. Its value for JEPA design is the architecture it argues for:

```text
perception -> configurable world model -> actor/planner
          -> cost/objective modules -> short-term memory
```

The key claim is that intelligent agents need learned world models over abstract state representations. Exact raw prediction is too expensive and too ambiguous for high-dimensional continuous domains.

## Architecture

The paper separates several roles that should not be collapsed into one model:

- Perception module: maps observations to state representations.
- World model: predicts future or counterfactual state representations.
- Cost/objective modules: score predicted states or trajectories.
- Actor/planner: searches for actions that minimize cost.
- Short-term memory: keeps relevant state over time.

JEPA fits the perception/world-model part: learn an embedding space where prediction is possible and useful.

## Objective And Loss

The paper motivates energy-based and joint-embedding objectives. A model assigns low energy to compatible pairs such as `(context, target)` and higher energy to incompatible pairs. In practical JEPA training, this often becomes a representation-space prediction loss:

```text
context observation -> context encoder -> predictor -> predicted target latent
target observation  -> target encoder              -> target latent
loss = distance(predicted target latent, target latent)
```

The important design point is not a specific MSE formula. It is the choice to predict useful abstractions instead of all raw details.

## Masking Or Target Design

The paper does not specify I-JEPA-style image masks. It motivates a broader target-design rule:

- Hide what the model should infer.
- Predict a latent that preserves task-relevant structure.
- Allow the latent to discard unpredictable nuisance detail.

For market data, this means the target should not be exact next tick. A better first target is the latent of a future window whose structure contains volatility, liquidity, order-flow, or regime information.

## Collapse Prevention

The paper frames collapse as a central joint-embedding risk: if every input maps to the same representation, prediction becomes easy and useless. The later JEPA family uses concrete prevention mechanisms such as slow target networks, stop-gradient branches, or regularized embedding distributions.

In this skill, always pair this paper with a concrete collapse source:

- I-JEPA or V-JEPA for EMA target encoders.
- BYOL or SimSiam for non-contrastive collapse mechanics.
- LeJEPA/SIGReg for regularization-based alternatives.

## Evaluation

The position paper argues for learned representations and world models but does not define a benchmark recipe for trading or time series. For practical designs, use:

- Frozen probes for representation quality.
- Simple baselines under the same split.
- Time-safe validation for markets.
- Planning tests only after passive representation tests pass.

## Design Lessons

- Keep representation learning separate from policy claims.
- Build a predictive latent state before building an action policy.
- Treat objectives and guardrails as separate heads/modules.
- Avoid raw reconstruction when the raw future is underdetermined.
- Use action-conditioned prediction only when actions are actually observed, modeled, and validated.

## Trading And Time-Series Translation

The finance translation is methodological:

```text
market observations -> latent market state
candidate action/order -> predicted future latent state
objective/constraints -> score risk, cost, liquidity, fill, exposure
```

Do not jump there first. Start with a passive JEPA:

```text
context: past market window
target: future market window latent
probe: future volatility/liquidity/regime bucket
baseline: simple time-safe features
```

Only after this works should action-conditioned execution modeling enter the design.

## Failure Modes

- Treating the paper as evidence that JEPA will produce profitable trading.
- Training a raw next-price predictor and calling it JEPA.
- Combining representation, objective, planner, and strategy evaluation in one experiment.
- Ignoring collapse because the pretraining loss is low.
- Planning with actions before modeling costs, latency, fill uncertainty, and market impact.

## Use In This Skill

Use this paper to justify the high-level architecture and representation-space prediction. Use more concrete papers for implementation choices.
