# Source Map

Use this reference when the user asks for source-grounded JEPA design, paper comparison, or explanations tied to the video/slides/papers.

## Bundled Skill References

- `references/course-recap.md`
  - Self-contained recap of the teaching sequence that led to this skill: JEPA loop, masking, collapse, probes, labels, and the trading research boundary.
- `references/lecun-lecture-digest.md`
  - Self-contained digest of the LeCun world-model lecture and ETH Zurich slides: timestamp map, slide map, world-model lessons, and design implications.
- `references/core-jepa-design.md`
  - Core JEPA architecture, masking, target encoder, predictor, collapse, and action-conditioned design notes.
- `references/evaluation-and-trading.md`
  - Finance/trading evaluation guardrails: probes, baselines, leakage, splits, metrics, and claims.
- `references/toy-experiments.md`
  - CPU-friendly JEPA toy experiments and acceptance criteria.
- `references/world-model-lessons.md`
  - Objective-driven AI and world-model planning framing.
- `references/paper-deep-dives.md`
  - Router for standalone paper-level notes. Use it before loading a specific paper deep dive.
- `references/paper-ami-world-models.md`
  - LeCun autonomous machine intelligence, JEPA motivation, world-model architecture, objectives, planning, and finance interpretation.
- `references/paper-ijepa.md`
  - I-JEPA architecture, block masking, target encoder, predictor, loss, evaluation, and design translation.
- `references/paper-vjepa.md`
  - V-JEPA video feature prediction, spatiotemporal masking, frozen evaluation, and temporal design lessons.
- `references/paper-vjepa2.md`
  - V-JEPA 2 scaling, video understanding, action-conditioned post-training, and planning implications.
- `references/paper-collapse-byol-simsiam-simclr.md`
  - BYOL, SimSiam, SimCLR, and LeJEPA/SIGReg collapse-prevention patterns.
- `references/paper-market-validation.md`
  - Finance validation, DeepLOB baseline context, PBO, Sharpe uncertainty, leakage, and trading claims.
- `references/paper-frontier-jepa-notes.md`
  - Recent lecture-linked work such as LeJEPA, LeWorldModel, DINO-WM, DINO-world, V-JEPA 2.1, latent action models, and DINOv3.

## Primary JEPA Sources

- LeCun, "A Path Towards Autonomous Machine Intelligence"
  - Use for objective-driven architecture, JEPA motivation, world models, planning, energy-based framing.
- Assran et al., "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture" (I-JEPA)
  - Use for image context/target blocks, masking, predictor, target encoder, evaluation.
- facebookresearch/ijepa
  - Use for implementation details.
- Bardes et al., "Revisiting Feature Prediction for Learning Visual Representations from Video" (V-JEPA)
  - Use for video masking, spatiotemporal feature prediction, video representation learning.
- facebookresearch/jepa
  - Use for practical V-JEPA implementation structure.
- "V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning"
  - Use for planning and action/world-model connection.
- facebookresearch/vjepa2
  - Use for current public implementation lineage.

## Lecture-Linked Sources From The Slides

These appear in the user-provided LeCun ETH Zurich slide deck. Treat them as source leads from the lecture; verify current paper/code details from primary sources before relying on exact claims.

- LeJEPA / SIGReg, Balestriero and LeCun, arXiv:2511.08544
  - Use for regularized/information-maximization JEPA training and collapse-prevention alternatives to distillation.
- LeWorldModel, arXiv:2603.19312
  - Use for JEPA world models trained with SIGReg and action-conditioned representation-space prediction.
- DINO-WM, Zhou 2024, arXiv:2411.04983
  - Use for planning with DINO-style representations as a world-model substrate.
- DINO-World, Baldassare 2025, arXiv:2507.19468
  - Use for DINO-based world-model/planning comparisons.
- V-JEPA 2.1, Mur-Labadia et al., arXiv:2603.14482
  - Use for video understanding/planning extensions, depth estimation, segmentation, and dense feature probes.
- "Inferring hidden actions from video", arXiv:2601.05230
  - Use for action/inference questions where actions are unobserved but must be recovered from state transitions.
- DINOv3, arXiv:2508.10104
  - Use as a representation-learning baseline or comparison point when the question is about generic visual encoders rather than JEPA mechanics.

## Collapse And Non-Contrastive SSL

- BYOL, "Bootstrap Your Own Latent"
  - Use for online/target network and slow target update intuition.
- SimSiam, "Exploring Simple Siamese Representation Learning"
  - Use for collapse, stop-gradient, and why symmetric joint-embedding objectives can fail.
- SimCLR
  - Use for linear/frozen evaluation protocol ideas, even though its objective is contrastive.

## Finance Evaluation Sources

- Lopez de Prado, "Advances in Financial Machine Learning"
  - Use for purging, embargoing, labeling, sample weights, and validation discipline.
- Bailey et al., "The Probability of Backtest Overfitting"
  - Use for model selection skepticism.
- Andrew Lo, "The Statistics of Sharpe Ratios"
  - Use for uncertainty and serial dependence in performance claims.
- DeepLOB
  - Use for limit-order-book deep learning baseline and market-data representation ideas.
- Kearns and Nevmyvaka, "Machine Learning for Market Microstructure and High Frequency Trading"
  - Use for microstructure grounding.

## Source-To-Design Mapping

When making a claim:

```text
latent prediction over raw reconstruction -> LeCun lecture, I-JEPA, V-JEPA
mask scale and semantic target pressure -> I-JEPA
slow target encoder / EMA answer key -> I-JEPA, BYOL
collapse risk -> LeCun lecture, SimSiam, BYOL
frozen probes -> SimCLR evaluation pattern, LeCun small-head Q&A
time-safe finance validation -> Lopez de Prado, Bailey et al., Lo
market microstructure representation -> DeepLOB, Kearns/Nevmyvaka
planning/world model -> LeCun AMI paper, V-JEPA 2
```

If the user asks for the latest status of a paper, model, codebase, or package, verify against current primary sources before answering.

## Deep-Dive Routing

Use `references/paper-deep-dives.md` when the user asks for:

```text
deep dive / explain the paper / compare papers / what should I copy from this paper
paper-grounded architecture design / collapse method choice / market JEPA validation
```

Load only the relevant paper file after the router. Do not load every deep dive unless the task explicitly asks for a broad literature survey.
