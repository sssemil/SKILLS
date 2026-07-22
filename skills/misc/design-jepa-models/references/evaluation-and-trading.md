# Evaluation And Trading

Use this reference for market-data JEPA, probe design, labels, baselines, validation, leakage, and trading-specific claims.

## Evaluation Ladder

Do not jump from pretraining loss to trading.

```text
1. Pretraining sanity: loss, latent variance, no collapse
2. Representation sanity: clusters, nearest neighbors, regime separation
3. Frozen probes: small heads on latents
4. Baseline comparison: simple features under same split
5. Strategy research: costs, slippage, latency, turnover, capacity
6. Robustness: walk-forward, stress, ablation, backtest-overfit checks
```

Positive results at one rung do not imply success at the next.

## Probe Design

A probe is a small model trained on frozen latents to test whether information is accessible.

Probe spec:

```text
frozen input:
probe label:
bucket thresholds:
baseline:
split:
metric:
success means:
does not prove:
```

Best first market labels:
- Future realized volatility bucket.
- Future liquidity bucket.
- Future order-flow imbalance bucket.
- Regime-change indicator.

Riskier later labels:
- Future direction bucket.
- Return quantile.
- Entry/exit rule outcome.
- PnL label.

Start with volatility because it is mechanical, relevant, and less noisy than direction.

## Label Construction

Labels must be mechanically defined and time-safe.

Example:

```text
input at t: data up to t
future window: t to t+30s
label value: realized volatility over future window
bucket thresholds: tertiles from training period only
label: low / medium / high
```

Rules:
- Future data may define the label.
- Future data must not enter context, scaling, threshold fitting, model selection, or baseline features.
- Bucket thresholds belong to the training split, not the full dataset.
- Label windows that overlap split boundaries require purging or embargo gaps.

## Baselines

A JEPA latent is interesting only against honest baselines.

Market baselines:
- Majority-class or unconditional baseline.
- Recent realized volatility.
- Recent returns/momentum.
- Current spread/depth.
- Trade count/volume.
- Order-flow imbalance.
- Linear/logistic/ridge model on simple features.
- Simple MLP on simple features if the JEPA probe uses a nonlinear head.

Fairness rule:
- Baseline gets features available at the same time as the JEPA context.
- Baseline should not be artificially weak.
- Compare under identical time split and metric.

## Splits And Leakage

Random row splits are usually invalid for market windows.

Use:
- Train on older blocks.
- Validate on later blocks.
- Test on a final untouched later block.
- Add embargo gaps larger than the future label window where samples overlap.
- Fit scalers, PCA, thresholds, feature selectors, and hyperparameters on training data only.

Leakage traps:
- Full-dataset normalization.
- Full-dataset volatility tertiles.
- Overlapping train/validation future windows.
- Labels derived from closing candles unavailable at decision time.
- Survivorship-biased assets.
- Corporate actions not handled consistently.
- Timestamp alignment mistakes.
- Using revised data that was unavailable historically.

## Metrics

For probes:
- Balanced accuracy for imbalanced buckets.
- Macro F1 when classes are uneven.
- ROC-AUC/PR-AUC for binary event labels.
- Calibration and Brier score for probabilistic labels.
- Confusion matrix by time period/regime.

For later strategies:
- Return net of costs.
- Turnover.
- Drawdown.
- Sharpe with serial dependence caution.
- Capacity and slippage sensitivity.
- Backtest-overfitting checks.

## What Success Means

Probe success means:
- The frozen latent contains out-of-sample signal for that label.
- The signal is accessible to a small head.
- The representation may be worth testing further.

Probe success does not mean:
- The model can trade.
- The signal survives transaction costs.
- The strategy has capacity.
- The result is robust to model search.
- The world model understands causality.

## Market JEPA Design Pattern

Good first market JEPA:

```text
data: synthetic OHLC or small clean historical bars
context: past 32-128 bars
target: next 8-32 bars
features: returns, range, volume z-score, spread/depth if available
encoder: small 1D CNN, TCN, GRU, or transformer encoder
target update: EMA target encoder
loss: distance between predicted and target latents
probe: future volatility bucket
baseline: recent volatility + spread/depth + volume
split: chronological with embargo
```

Avoid first:
- Exact next-close target.
- Direction-only objective.
- PnL labels.
- Action-conditioned execution model.
- Many assets and many horizons at once.
- Live trading loop.
