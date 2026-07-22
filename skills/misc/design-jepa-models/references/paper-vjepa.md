# Paper Deep Dive: V-JEPA

Use this reference for video JEPA, spatiotemporal masking, feature prediction without reconstruction, and frozen video representation evaluation.

## Sources

- Bardes et al., "Revisiting Feature Prediction for Learning Visual Representations from Video", arXiv: https://arxiv.org/abs/2404.08471
- Meta research page: https://ai.meta.com/research/publications/revisiting-feature-prediction-for-learning-visual-representations-from-video/
- Official implementation lineage: https://github.com/facebookresearch/jepa

## Core Contribution

V-JEPA extends the JEPA idea to video. It trains visual encoders using only feature prediction over masked spatiotemporal regions, without pixel reconstruction, negative examples, text supervision, or a pretrained image encoder as the teacher.

The key shift from I-JEPA is temporal structure:

```text
visible video tubelets -> context encoder -> context latent
masked video tubelets  -> target encoder  -> target latent
context latent + spatiotemporal positions -> predictor -> predicted target latent
```

## Architecture

Core modules:

- Video encoder over space-time patches or tubelets.
- Target encoder updated slowly from the online encoder.
- Predictor that receives context features and target positions.
- Masking strategy over both space and time.

The predictor is intentionally a training-time bridge. The reusable object is the encoder representation.

## Objective And Loss

V-JEPA optimizes representation-space prediction of masked video features. It avoids raw video generation, which would require modeling unpredictable texture, lighting, camera noise, and stochastic future details.

Design consequence:

```text
Predict "what high-level state/motion should be there?"
not "what exact frame will be there?"
```

## Masking Or Target Design

V-JEPA uses spatiotemporal masking. The mask should require the model to infer object persistence, motion, and scene dynamics.

Good video targets:

- Coherent spatiotemporal regions.
- Future or hidden tubelets that require temporal inference.
- Regions large enough to avoid pixel/texture shortcuts.

Market translation:

- Hide a coherent future interval, not a single next point.
- Predict latent structure over the interval.
- Use horizon embeddings or target-position embeddings.
- Consider multiscale horizons only after a one-horizon model works.

## Collapse Prevention

V-JEPA follows the target-encoder family: an online branch predicts features from a target branch that is stabilized and stop-gradient. This reduces but does not eliminate collapse risk.

Required diagnostics:

- Latent variance across dimensions.
- Nearest-neighbor inspection.
- Probe performance under frozen encoder.
- Regime or motion clustering.
- Ablation against trivial persistence baselines.

## Evaluation

The paper evaluates frozen or lightly adapted representations on video and image tasks. The important lesson is that feature prediction can produce useful motion and appearance representations without adapting the backbone heavily.

For time series:

```text
freeze encoder -> probe future property -> compare to simple feature baselines
```

Do not use pretraining loss alone as evidence.

## Design Lessons

- Temporal JEPA should predict latent spans, not exact frames or exact ticks.
- Masking should make dynamics necessary.
- Evaluation should test whether motion/state information is accessible from frozen latents.
- The target branch is a training signal, not a deployment sensor.

## Trading And Time-Series Translation

V-JEPA maps naturally to market windows because both video and markets are sequential, partially observed, and noisy. A good first translation:

```text
context: observed market window up to t
target: future window t+1...t+h
mask: hide contiguous future interval
latent should preserve: volatility, liquidity, flow, regime, spread/depth state
latent may discard: individual unpredictable trades, exact tick path
probe: future volatility or liquidity bucket
baseline: recent volatility, spread, depth, volume, imbalance
```

## Failure Modes

- Treating video feature prediction as proof that market direction is predictable.
- Making the future target too long or too stochastic for the available context.
- Letting future-window statistics leak into normalization.
- Evaluating with random window splits instead of chronological splits.
- Using a large probe that hides representation weakness.

## Use In This Skill

Use V-JEPA when the user asks about temporal masks, video-style JEPA, or future-span prediction. Pair with the market-validation notes for finance.
