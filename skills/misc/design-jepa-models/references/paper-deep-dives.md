# Paper Deep-Dive Router

Use this reference when a user asks for paper-grounded JEPA design, paper comparison, or deeper source notes. Load only the paper file that matches the decision being made.

## Selection Table

| Need | Read |
| --- | --- |
| Why JEPA exists, objective-driven agents, world models, planning | `references/paper-ami-world-models.md` |
| Image JEPA mechanics, block masks, target encoder, predictor | `references/paper-ijepa.md` |
| Video JEPA mechanics, spatiotemporal masks, frozen video features | `references/paper-vjepa.md` |
| Scaling JEPA to understanding, prediction, and robotic planning | `references/paper-vjepa2.md` |
| Collapse prevention, EMA targets, stop-gradient, contrastive baselines, SIGReg | `references/paper-collapse-byol-simsiam-simclr.md` |
| Market-data validation, LOB baselines, leakage, PBO, Sharpe uncertainty | `references/paper-market-validation.md` |
| Recent lecture-linked papers and what is promising but not settled | `references/paper-frontier-jepa-notes.md` |

## Common Comparison Questions

### I-JEPA vs V-JEPA

Use I-JEPA for still-image masked block prediction and the cleanest explanation of context blocks, target blocks, predictor tokens, and target encoder. Use V-JEPA for temporal/spatiotemporal masking, video-only feature prediction, and frozen representation evaluation across motion and appearance tasks.

### V-JEPA vs V-JEPA 2

Use V-JEPA for representation learning from video features. Use V-JEPA 2 when the question reaches planning: large-scale video pretraining first, then a separate action-conditioned post-training stage for latent world-model planning.

### BYOL/SimSiam vs JEPA

Use BYOL and SimSiam to explain why non-contrastive joint embedding can avoid or suffer collapse. Use JEPA papers to explain predictive masking and latent target prediction. Use LeJEPA/SIGReg when the user asks about regularization alternatives to teacher-student EMA.

### JEPA For Trading

Use the JEPA papers for representation objectives, but use the market-validation reference for claims. A trading JEPA needs time-safe labels, purged or embargoed splits, honest simple baselines, and probe results before any strategy claim.

## Paper-Note Template

When adding a future paper note, keep the same headings:

```text
Sources
Core contribution
Architecture
Objective and loss
Masking or target design
Collapse prevention
Evaluation
Design lessons
Trading/time-series translation
Failure modes
Use in this skill
```

Keep the note standalone. Do not link to local transcripts, slide files, or workspace paths.
