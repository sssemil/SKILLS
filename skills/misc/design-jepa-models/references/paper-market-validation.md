# Paper Deep Dive: Market Validation And Baselines

Use this reference when a JEPA design involves trading, market data, probes, labels, validation, baselines, or strategy claims.

## Sources

- DeepLOB, "Deep Convolutional Neural Networks for Limit Order Books", arXiv: https://arxiv.org/abs/1808.03668
- Bailey et al., "The Probability of Backtest Overfitting", SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- Andrew Lo, "The Statistics of Sharpe Ratios", CFA Institute page: https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios
- Andrew Lo paper page: https://alo.mit.edu/research-page/the-statistics-of-sharpe-ratios/

## Core Contribution

The JEPA papers tell how to learn representations. They do not tell whether a trading result is valid. Market validation needs its own discipline:

```text
representation learning -> frozen probes -> baselines -> time-safe validation -> strategy tests
```

The first goal is not "make money". The first goal is proving the frozen latent carries out-of-sample market-state information beyond simple features.

## DeepLOB Baseline Context

DeepLOB is a supervised limit-order-book model using convolutional filters for book structure and recurrent modules for temporal dependencies. It is useful as a reminder that:

- LOB data has spatial structure across price levels and sides.
- Temporal dependencies matter.
- Strong supervised baselines already exist for price-movement labels.
- Cross-instrument generalization is a meaningful test.

For JEPA, DeepLOB is not the first baseline for every task. A simpler baseline should come first:

```text
recent volatility
recent returns
spread/depth
volume/trade count
order-flow imbalance
linear/logistic/ridge probe on simple features
```

Use DeepLOB-style supervised models later when the JEPA claim is stronger and the dataset supports it.

## Backtest Overfitting

Bailey et al. formalize the risk that repeated strategy search produces an apparently good backtest that does not generalize. The design lesson for JEPA:

- Keep pretraining, probe selection, and strategy selection separate.
- Do not try many labels/horizons/masks and report only the winner.
- Use untouched test periods.
- Report how many variants were tried.
- Prefer a small number of predeclared probe labels.

For a JEPA study, overfitting can occur before any backtest:

```text
mask search -> label search -> probe search -> split search -> strategy search
```

Every search step consumes evidence.

## Sharpe Ratio Uncertainty

Lo shows that Sharpe ratio estimates are statistical estimates affected by serial correlation and return dynamics. Design consequences:

- Annualized Sharpe is not automatically reliable.
- Serial dependence can distort naive scaling.
- Strategy claims need uncertainty, not just point estimates.
- High Sharpe in a short backtest is weak evidence.

This matters only after strategy tests. For representation learning, use probe metrics first.

## Label Design For JEPA Probes

Prefer mechanical labels:

```text
future realized volatility bucket
future liquidity bucket
future order-flow imbalance bucket
regime-change indicator
spread widening / depth thinning
```

Avoid first:

```text
PnL label
buy/sell signal
exact next return
hand-labeled regime
label using full-dataset thresholds
```

Bucket thresholds must be fit on the training period only.

## Split And Leakage Rules

Market windows overlap. Chronological validation is the default.

Use:

- Train on earlier time blocks.
- Validate on later time blocks.
- Test on the final untouched time block.
- Add embargo gaps larger than the target horizon and overlapping feature window.
- Fit scalers, thresholds, PCA, feature selection, and hyperparameters on train only.

Leakage traps:

- Full-dataset normalization.
- Future bars in rolling features.
- Overlapping future windows across split boundaries.
- Corporate action adjustment mismatch.
- Timestamp alignment mistakes.
- Survivorship-biased asset universes.
- Using revised or delayed data as if known at time t.

## Success Criteria

For a market JEPA, success means:

- Latents do not collapse.
- Frozen probes beat simple baselines on time-separated data.
- Results survive an embargo.
- The useful signal is not just time-of-day or asset identity.
- Probe metrics are stable across periods/regimes.

It does not mean:

- A strategy is profitable.
- Costs and slippage are solved.
- The signal has capacity.
- The model understands causality.
- Automated trading is ready.

## Failure Modes

- Reporting pretraining loss as evidence.
- Comparing JEPA probe to an artificially weak baseline.
- Randomly splitting overlapping market windows.
- Choosing labels after seeing test results.
- Evaluating direction before volatility/liquidity.
- Hiding failed horizons or masks.

## Use In This Skill

Use this reference for every trading-related JEPA design. It is the guardrail that prevents representation research from turning into unsupported strategy claims.
