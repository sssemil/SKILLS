# Paper Deep Dive: V-JEPA 2

Use this reference when JEPA design reaches scaling, video understanding, action-conditioned world models, or planning.

## Sources

- Assran et al., "V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning", arXiv: https://arxiv.org/abs/2506.09985
- Official implementation: https://github.com/facebookresearch/vjepa2

## Core Contribution

V-JEPA 2 scales JEPA-style video pretraining and then shows how the learned representation can be post-trained into an action-conditioned latent world model for robotic planning.

The important stage separation:

```text
Stage 1: action-free video/image pretraining -> strong encoder
Stage 2: action-conditioned post-training on robot trajectories -> latent world model
Stage 3: planning in latent space toward visual goals
```

This is a design warning: representation learning and planning are separate stages with different data requirements.

## Architecture

The full system combines:

- A self-supervised video encoder trained at scale.
- A predictor/world-model component operating in latent space.
- An action-conditioned post-training stage for robot trajectories.
- A planner that searches candidate action sequences against goal representations.

The passive encoder is not automatically a planner. The action-conditioned component needs interaction trajectories.

## Objective And Loss

The pretraining objective follows the JEPA family: predict hidden/future latent video representations rather than reconstruct raw frames. The action-conditioned stage predicts future latent states conditioned on actions.

Conceptual form:

```text
state latent at t + action sequence -> predicted future latent
future observation -> encoder/target branch -> future latent
loss = distance(predicted future latent, future latent)
```

## Masking Or Target Design

V-JEPA 2 inherits the video masking lesson: target regions and horizons should force scene and motion understanding. The planning extension adds a second target design question:

- What future latent should count as reaching the goal?
- What action labels or trajectories are available?
- Does the latent space preserve geometry and object state enough for planning?

## Collapse Prevention

The system still depends on non-collapsed latent representations. For planning, collapse is especially dangerous because a planner may optimize in a meaningless latent space.

Planning-stage diagnostics should include:

- Passive frozen probes.
- Goal-state nearest neighbors.
- Prediction error over rollout horizon.
- Planning success under held-out environments.
- Failure cases where low latent error hides task failure.

## Evaluation

The paper reports video understanding, prediction, video QA alignment, and robotic planning results. For design purposes, the general evaluation ladder is:

```text
representation quality -> prediction quality -> planning quality
```

Do not skip rungs. A good encoder does not imply a good planner.

## Design Lessons

- Use a two-stage or three-stage plan when actions matter.
- Learn passive representations before action-conditioned transition models.
- Use unlabeled video/time-series data for representation learning where possible.
- Use action-labeled trajectories only for the action-conditioned layer.
- Keep the planning objective explicit and separate from the encoder loss.

## Trading And Time-Series Translation

For automated trading research, V-JEPA 2 suggests a future roadmap, not a first experiment:

```text
Stage 1: passive market JEPA on historical observations
Stage 2: frozen probes for volatility/liquidity/regime
Stage 3: action-conditioned execution model with orders, fills, costs, latency
Stage 4: planner/strategy search under explicit risk and cost objectives
```

Action labels in trading are not just "buy/sell". They include order type, price, size, timing, queue position, venue, fill state, cancellation, and market impact.

## Failure Modes

- Calling a passive market encoder a world model for trading.
- Training on historical prices without action/fill data and claiming execution planning.
- Ignoring that market actions can affect the state through impact.
- Optimizing a strategy objective before validating representation quality.
- Evaluating planning without costs, slippage, latency, and capacity constraints.

## Use In This Skill

Use V-JEPA 2 when the user asks how JEPA connects to planning. For a first CPU toy or market prototype, keep the design passive and use V-JEPA 2 only as the roadmap.
