# Paper Deep Dive: Collapse Prevention And SSL Baselines

Use this reference when choosing a collapse-prevention mechanism or comparing JEPA to BYOL, SimSiam, SimCLR, or LeJEPA/SIGReg.

## Sources

- BYOL, "Bootstrap Your Own Latent", arXiv: https://arxiv.org/abs/2006.07733
- SimSiam, "Exploring Simple Siamese Representation Learning", arXiv: https://arxiv.org/abs/2011.10566
- SimCLR, "A Simple Framework for Contrastive Learning of Visual Representations", arXiv: https://arxiv.org/abs/2002.05709
- LeJEPA, "Provable and Scalable Self-Supervised Learning Without the Heuristics", arXiv: https://arxiv.org/abs/2511.08544

## Core Contribution

Joint-embedding methods are attractive because they can learn without reconstructing raw data. Their central risk is collapse:

```text
all inputs -> same latent
prediction loss -> low
representation -> useless
```

BYOL, SimSiam, SimCLR, and LeJEPA represent different families of answers to this problem.

## BYOL Pattern

BYOL uses two networks:

```text
online encoder/projector/predictor -> predicts target representation
target encoder/projector           -> slow moving average of online branch
```

Key design lesson:

- EMA target networks can stabilize a non-contrastive objective.
- The predictor and asymmetry matter.
- Negative examples are not mandatory, but collapse checks remain mandatory.

JEPA connection: I-JEPA/V-JEPA use a similar slow target branch intuition.

## SimSiam Pattern

SimSiam shows that a simple Siamese setup can avoid collapse without negatives, large batches, or momentum encoders when stop-gradient and predictor asymmetry are used.

Key design lesson:

- Stop-gradient is not a minor implementation detail.
- Removing asymmetry can cause collapse.
- A predictor can act as a buffer between representation and objective.

JEPA connection: target branch stop-gradient and predictor asymmetry should be treated as structural choices, not cleanup code.

## SimCLR Pattern

SimCLR is contrastive:

```text
two augmented views of same sample -> pull together
other samples in batch            -> push apart
```

Key design lesson:

- Contrastive baselines are strong and honest.
- Augmentation/task design matters.
- Large batches and negative sampling can be expensive or tricky.

JEPA connection: even if a JEPA is non-contrastive, SimCLR-style linear or frozen evaluation is useful as an evaluation pattern.

## LeJEPA And SIGReg Pattern

LeJEPA proposes a regularized JEPA objective using Sketched Isotropic Gaussian Regularization. The source frames SIGReg as a way to constrain embedding distributions directly, reducing reliance on teacher-student EMA, stop-gradient, schedulers, or other heuristics.

Key design lesson:

- Regularize the embedding distribution, not only the prediction error.
- Track variance and covariance-like structure explicitly.
- Consider regularization when EMA target setups are unstable or too heuristic-heavy.

For a first CPU toy, EMA is simpler. For research-grade designs, document whether collapse prevention is EMA, stop-gradient, contrastive negatives, SIGReg/VICReg-style regularization, or a combination.

## Choosing A Mechanism

Use this decision table:

| Situation | Default |
| --- | --- |
| First toy JEPA | EMA target encoder plus latent variance diagnostics |
| I-JEPA/V-JEPA-style implementation | EMA target encoder, stop-gradient target, predictor asymmetry |
| Need a strong SSL baseline | SimCLR or contrastive predictive baseline |
| EMA is unstable or theory question matters | LeJEPA/SIGReg or VICReg-style regularization |
| Market data with small batch sizes | EMA or regularized embedding objective before contrastive negatives |

## Diagnostics

Always log:

- Mean latent standard deviation across dimensions.
- Number of near-dead dimensions.
- Batch covariance or correlation summary if available.
- Nearest neighbors for different regimes.
- Probe metrics on frozen latents.
- Comparison against shuffled labels and simple baselines.

Collapse can be partial. A model can preserve one easy factor while losing the factor the user cares about.

## Trading And Time-Series Translation

Market data has strong persistence and repeated regimes. That creates pseudo-success cases:

- The model predicts "same as recent past" and gets low loss.
- The latent keeps volatility but loses liquidity or flow.
- The latent keeps asset identity but not state.
- The latent learns time-of-day shortcuts.

Market-specific collapse checks:

```text
cluster latents by volatility bucket
cluster latents by liquidity bucket
cluster latents by time of day
cluster latents by asset/session
probe future volatility after controlling for recent volatility
```

## Failure Modes

- Trusting low pretraining loss.
- Measuring only global variance while task-relevant factors collapse.
- Using random splits that make shortcut latents look useful.
- Adding a large probe that relearns the target.
- Forgetting that no-collapse does not imply tradability.

## Use In This Skill

Use this reference whenever a design mentions two encoders, slow copying, stop-gradient, predictor asymmetry, low loss with useless latents, or regularization choices.
