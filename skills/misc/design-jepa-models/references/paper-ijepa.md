# Paper Deep Dive: I-JEPA

Use this reference for image JEPA mechanics: context blocks, target blocks, predictor, target encoder, EMA update, semantic masking, and frozen evaluation.

## Sources

- Assran et al., "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture", arXiv: https://arxiv.org/abs/2301.08243
- Official implementation: https://github.com/facebookresearch/ijepa

## Core Contribution

I-JEPA shows that a model can learn strong image representations by predicting latent representations of masked image regions from visible context regions. It is non-generative: it does not reconstruct pixels, and it does not rely on hand-crafted image augmentations or negative examples as the main learning signal.

The basic loop:

```text
visible image patches -> context encoder -> context latent
masked target patches -> target encoder  -> target latent
context latent + mask tokens -> predictor -> predicted target latent
loss(predicted target latent, target latent)
```

## Architecture

Core modules:

- Context encoder: a ViT that sees only visible context patches.
- Target encoder: a slowly updated copy-like branch that encodes target patches from the full image.
- Predictor: maps context features plus target-position information to predictions for target block latents.
- Mask sampler: chooses target blocks and context blocks.

Deployment usually reuses the context encoder. The target encoder is a training-time answer branch.

## Objective And Loss

I-JEPA predicts target representations, not target pixels. The target branch is stop-gradient from the prediction loss. The target encoder is updated with an exponential moving average of the context encoder, making the target representation slower and more stable than the online context branch.

Design consequence:

```text
The predictor should learn "what latent should be over there?"
not "what exact pixels should be over there?"
```

## Masking Or Target Design

The masking strategy is one of the main design lessons. Target blocks are large enough to encourage semantic prediction rather than texture copying. Context must remain spatially distributed and informative enough to make inference possible.

Good mask pressure:

- Hide coherent blocks, not random isolated pixels.
- Make targets large enough to carry semantic structure.
- Use context that covers enough of the observation to infer missing structure.
- Avoid masks where local continuity solves the task.

Market translation:

```text
context = past/current market window available at time t
target = future or masked market-state window
mask pressure = force regime/volatility/liquidity inference, not exact tick copying
```

## Collapse Prevention

I-JEPA relies on the asymmetric online/target structure:

- Target branch uses stop-gradient.
- Target encoder is EMA-updated from the context encoder.
- Predictor exists only on the online branch.
- Evaluation checks representation quality, not only loss.

The EMA target is not magic. It stabilizes the answer branch, but collapse diagnostics remain required.

## Evaluation

I-JEPA is evaluated with frozen or lightly adapted representations on image tasks such as classification, object counting, and depth prediction. The important evaluation pattern is:

```text
pretrain self-supervised -> freeze or lightly adapt encoder -> test downstream information
```

For JEPA research, the equivalent is frozen probes before large fine-tuning or strategy claims.

## Design Lessons

- Predict latent targets instead of reconstructing raw observations.
- Choose masks that require structure, not local interpolation.
- Keep the predictor separate from the encoder.
- Treat the target encoder as an answer generator during pretraining, not as an inference-time dependency.
- Use frozen probes to test whether useful information is accessible.

## Trading And Time-Series Translation

An I-JEPA-inspired market model might be:

```text
observation: 64 bars or order-book/trade events
context: first 48 bars, or current/past book state
target: next 16 bars, or hidden future liquidity/flow window
context encoder: 1D CNN/TCN/Transformer
target encoder: EMA copy branch
predictor: MLP/Transformer block with horizon or target-position embedding
loss: MSE/cosine distance between predicted and target latents
probe: future volatility/liquidity/regime bucket
```

The target can use future data during pretraining, but future data must never enter context features, scaling, threshold fitting, or validation choices.

## Failure Modes

- Mask target is too tiny, so the model learns local interpolation.
- Context contains future-derived features through normalization or alignment mistakes.
- Target encoder collapses but loss still looks good.
- Probe uses a large head that learns the task itself.
- Direction or PnL labels are used before mechanical labels like volatility or liquidity.

## Use In This Skill

Use I-JEPA as the cleanest concrete template for a first JEPA architecture. For video/time dynamics, pair it with V-JEPA.
