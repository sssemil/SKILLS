# Toy JEPA Experiments

Use this reference when the user wants a CPU-friendly implementation, tutorial, or prototype.

## Best First Toy

Synthetic regime-switching OHLC is the best first toy for trading-oriented JEPA.

```text
regime 0: calm drift up
regime 1: calm drift down
regime 2: volatile sideways
```

Generate OHLCV bars from hidden regimes. Train JEPA on context and target windows, then freeze the encoder and probe for hidden regime or future volatility bucket.

Minimal spec:

```text
context: past 32 bars
target: next 8 bars
features: return, high-low range, volume z-score
encoder: small 1D CNN or MLP
latent dim: 16-64
batch size: 64
steps: 1000-5000
target update: EMA
probe: future volatility bucket
```

Expected outcome:
- Loss decreases.
- Latent variance stays nonzero.
- Frozen latents separate regimes better than raw naive baseline.
- Probe beats recent-volatility baseline on held-out time blocks.

## Ten Good Toy Options

1. Synthetic regime OHLC.
   - Teaches market-like windows, regimes, leakage-safe probes.
2. Noisy sine regimes.
   - Teaches latent clustering by frequency/amplitude/phase.
3. AR process switcher.
   - Teaches time-series dynamics with known coefficients.
4. Synthetic order-book imbalance.
   - Teaches microstructure-like state, spread/depth/imbalance.
5. Moving dot video.
   - Teaches visual world model and velocity latents.
6. Bouncing ball with occlusion.
   - Teaches hidden dynamics and impossible-event prediction error.
7. Weather toy grid.
   - Teaches spatial-temporal prediction and region probes.
8. Synthetic sensor machine.
   - Teaches complex-system modes and fault probes.
9. Synthetic token grammar JEPA.
   - Teaches transformer encoders and future-span latent prediction.
10. Tiny image patch JEPA.
   - Teaches I-JEPA-style masking with MNIST or generated shapes.

## Micro GPT-Shaped JEPA

A language-like toy is possible but it teaches mechanics more than JEPA motivation.

Use synthetic token grammars rather than natural language:

```text
regime 0: ABABAB...
regime 1: AABAABAAB...
regime 2: ABBABBABB...
regime 3: random with rare marker tokens
```

JEPA task:

```text
context tokens -> transformer encoder -> predictor -> predicted future-span latent
target tokens  -> target encoder       -> target latent
loss = latent distance
```

Probes:
- Grammar regime.
- Future entropy bucket.
- Rare marker appears soon.

State clearly:
- This is not GPT training.
- GPT predicts next-token distributions.
- JEPA predicts a latent representation of a future span.

## Minimal Implementation Guidance

For CPU:
- Use synthetic data.
- Keep samples under 100k.
- Use tiny encoders.
- Prefer 1D CNN/MLP/GRU before transformers.
- Use latent dim 16-64.
- Use batch size 32-128.
- Train for minutes, not hours.
- Log loss, latent variance, and probe metrics.

## Toy Acceptance Criteria

A toy JEPA is successful when:
- It runs on CPU quickly.
- It cannot trivially copy the target.
- Latents do not collapse.
- A frozen probe beats simple baselines on held-out generated data.
- The result is explainable through the known generator variables.

A toy is not successful just because:
- Pretraining loss goes down.
- Exact future values look close.
- A large probe overfits.
- Random splits look good.
