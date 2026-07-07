# Core JEPA Design

Use this reference for JEPA architecture design, masking, targets, predictors, target encoders, collapse prevention, and model-review checklists.

## The Core Loop

JEPA learns by predicting a target representation from a context representation.

```text
context observation -> context encoder -> context latent -> predictor -> predicted target latent
target observation  -> target encoder  -> target latent
loss = distance(predicted target latent, target latent)
```

In I-JEPA, the context is visible image blocks and the target is masked image blocks. In V-JEPA, the same principle moves to video: predict representations of masked/future spatiotemporal content. For market data, context might be past OHLCV/order-book/trade windows and target might be a future or masked market-state window encoded into a latent.

## Design Objective

A JEPA design should state what structure the latent must preserve and what detail it may discard.

Good objectives:
- Preserve object/scene/temporal structure in images or video.
- Preserve volatility, liquidity, order-flow, regime, or system-state structure in market/sensor time series.
- Preserve action-conditioned state transitions for planning.

Weak objectives:
- Predict exact pixels, exact next ticks, or every raw detail.
- Maximize pretraining loss reduction without downstream representation checks.
- Train a representation and immediately claim a strategy or policy.

## Context And Target

The context is what the predictor can use. The target is hidden from the predictor and encoded separately.

Design rules:
- Context must be available at inference or decision time.
- Target may use hidden/future data during pretraining, but it must never leak into context features, scaling, split choices, or baseline features.
- Target should be large/structured enough to prevent local copying and small enough to be learnable.
- Target should be represented in latent space, not necessarily reconstructed as raw observations.

Examples:

```text
Image JEPA:
context = visible image blocks
target = masked image block representations

Video JEPA:
context = visible frames/patches
target = masked spatiotemporal region representations

Market JEPA:
context = order book + trades up to time t
target = future window from t to t+30s encoded by target encoder
```

## Masking As Curriculum

Masking defines the learning problem. It should force useful inference.

Check:
- What shortcut would solve this mask without learning the intended abstraction?
- Is the target too local, encouraging texture/continuity copying?
- Is the target too unpredictable, punishing the model for unknowable detail?
- In time series, does any future-derived statistic enter context?
- In cross-sectional data, does masking let the model infer a target from duplicated or synchronized leakage?

For markets:
- Temporal mask: hide a future window and predict its latent.
- Cross-sectional mask: hide some assets/venues/book levels and infer their latent from related visible context.
- Feature mask: hide liquidity or flow-derived channels while preserving time-safe inputs.

## Encoders And Predictor

Core components:
- Context encoder: maps visible/current observations to latents.
- Target encoder: maps hidden/target observations to answer latents.
- Predictor: maps context latents plus positional/mask/action information to predicted target latents.

Target encoder update options:
- EMA/distillation target: target encoder slowly follows context encoder. Common in BYOL/I-JEPA-style systems.
- Stop-gradient target: target branch provides a non-gradient answer.
- Regularized joint embedding: use variance/covariance/information constraints rather than EMA.
- Contrastive objective: possible but less aligned with the LeCun recommendation to prefer regularized/non-contrastive methods where feasible.

Design constraints:
- The predictor must not read target observations.
- The target encoder produces the answer representation; it is not a deployment-time oracle.
- In probing or deployment, the context encoder is usually the reusable representation source.

## Collapse Prevention

Collapse means different inputs map to the same or near-same latent.

Failure:

```text
different market states -> same latent -> low JEPA loss -> useless representation
```

Prevention families:
- Distillation / slow target networks: DINO, BYOL, I-JEPA, V-JEPA family.
- Information maximization / regularization: variance and covariance constraints such as SIGReg, VCReg, Barlow Twins-style ideas.
- Contrastive methods: push non-matching samples apart; useful but carries sampling/negative-pair choices.

Diagnostics:
- Latent variance per dimension.
- Nearest neighbors in latent space.
- Clusters colored by known regimes or labels.
- Probe performance with frozen encoder.
- Performance under time-separated validation.
- Collapse under ablation: remove predictor, change target size, change EMA rate, reduce mask difficulty.

## Loss And Metrics

Training loss should compare predicted target latents to target latents. Common choices are MSE/cosine-like distances, often with normalization and stabilization details depending on implementation.

Do not trust pretraining loss alone. A low loss can come from:
- Trivial persistence.
- Constant latents.
- Leakage.
- Targets that are too easy.
- Target encoder drift.

Always add representation checks and downstream probes.

## Action-Conditioned JEPA

For world models, include actions/interventions:

```text
state context latent + action sequence -> predictor/world model -> predicted future state latent
future state observation -> target encoder -> future state latent
```

Use when:
- The system can choose actions.
- The goal is planning or model-predictive control.
- Interventions alter state transitions.

For trading, actions are orders and placements. Do not start with action-conditioned JEPA until the passive representation and validation stack works. Execution, fill uncertainty, transaction costs, latency, and market impact make action-conditioned finance models much harder than passive state representation.

## Design Checklist

A JEPA design is not complete until these are answered:

- What is one observation?
- What is visible context?
- What is hidden target?
- What latent structure matters?
- What raw detail may be discarded?
- What mask makes the task semantic/structural?
- What shortcut could solve the task?
- How is the target encoder updated?
- How is collapse prevented and detected?
- What frozen probe tests the latent?
- What baseline must be beaten?
- What split prevents leakage?
- What result would falsify the idea quickly?
