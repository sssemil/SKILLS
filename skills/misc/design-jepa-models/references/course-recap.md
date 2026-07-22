# Course Recap

This is the self-contained recap of the JEPA learning path that informed this skill.

## Core JEPA Loop

JEPA predicts target representations from context representations.

```text
visible/current data -> context encoder -> context latent -> predictor -> predicted target latent
hidden/future data   -> target encoder  -> target latent
loss = distance(predicted target latent, target latent)
```

The context encoder reads what is available now. The predictor guesses the hidden/future target latent. The target encoder creates the answer representation for the target. Training moves the predicted target latent closer to the target latent.

Important wording:
- Predicted target latent = predictor's guess.
- Target latent = answer key from target encoder.
- The predictor does not read target data.

## Two Encoders

The context encoder and target encoder are separate because they do different jobs.

```text
context encoder = active branch trained by gradient
target encoder = stable answer branch, often EMA-updated
predictor = maps context latent to predicted target latent
```

EMA intuition:

```text
target_encoder = 99.9% old_target_encoder + 0.1% new_context_encoder
```

This slow update gives a steadier answer key and reduces direct chasing between both branches. During probing or deployment, usually use the context encoder because it only uses data available at decision time.

## Masking Is The Curriculum

Masking chooses the prediction problem. It is not just removing noise.

Good mask:
- Hides enough data to force useful abstraction.
- Leaves enough context for the target to be inferable.
- Prevents local copying or trivial persistence.

Bad mask:
- Target is tiny and adjacent, encouraging texture/continuity shortcuts.
- Target is too large or too random, making prediction impossible.
- Future data leaks into context, scaling, thresholds, or validation.

Market example:

```text
context = order book/trades/OHLCV up to time t
target = future/masked market window encoded into a latent
shortcut risk = persistence or duplicated features
leakage risk = future candle close, full-dataset scaling, overlapping labels
```

## Semantic Means Useful Structure

In JEPA language, "semantic" means the target requires meaningful structure rather than surface detail.

Image/video:
- Non-semantic: exact pixel colors, tiny edge continuation, texture noise.
- Semantic: object, part, layout, relation, physical plausibility.

Market data:
- Non-semantic: exact next tick.
- More semantic: volatility/liquidity/order-flow/regime structure over a future window.

For trading research, semantic roughly means decision-relevant market structure, not raw noisy motion.

## Collapse

Collapse is when different inputs map to the same or nearly same representation.

```text
high-volatility state -> same latent
low-volatility state  -> same latent
pretraining loss low  -> representation still useless
```

Low pretraining loss is not enough. Always inspect latent variance, clusters, nearest neighbors, and frozen probe performance.

## Probes Before Trading

A JEPA encoder is not a strategy. It is a representation learner.

Evaluation ladder:

```text
pretrain JEPA -> freeze encoder -> train small probe -> compare baseline -> only later test strategy
```

Probe asks:

```text
Does the current latent contain information that helps predict a future property?
```

Good first market probe:

```text
frozen input = context encoder latent from data up to time t
probe label = future realized volatility bucket over t to t+30s
baseline = recent volatility, spread/depth, trade count, recent returns
split = older train blocks, later validation blocks, embargo for overlap
success = latent beats baseline out-of-sample
does not prove = profitable strategy
```

## Probe Labels

Keep three concepts separate:

- JEPA target: hidden/future data encoded during pretraining.
- Probe label: mechanically defined future property used after pretraining.
- Trading signal: later decision rule for entries/exits/sizing/costs.

Recommended first label:
- Future realized volatility bucket.

Good later labels:
- Future liquidity bucket.
- Future order-flow imbalance bucket.
- Regime-change indicator.

Risky early labels:
- Direction.
- PnL.
- Overbought/oversold unless mechanically defined.

Threshold rule:
- Compute bucket thresholds on training data only.
- Never use full-dataset tertiles or full-dataset normalization.

## Toy Experiments

Best first toy:

```text
synthetic regime-switching OHLC
context = past 32 bars
target = next 8 bars
features = returns, range, volume z-score
probe = hidden regime or future volatility bucket
```

Why:
- CPU-friendly.
- Market-shaped.
- Known hidden truth.
- Tests representation learning without real-market data mess.

Other good toys:
- AR process switcher.
- Noisy sine regimes.
- Synthetic order-book imbalance.
- Moving dot video.
- Synthetic token grammar JEPA.

## Trading Boundary

JEPA research for trading should progress:

```text
representation -> probe -> baseline comparison -> robust validation -> strategy research
```

Do not skip from JEPA loss to automated trading. Positive probe results mean the latent may carry signal; they do not establish profitability, capacity, robustness, or execution viability.
