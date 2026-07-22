# Frontier JEPA And World-Model Notes

Use this reference for recent lecture-linked papers and near-JEPA work. Treat these as research leads. Verify current paper/code status before relying on exact claims in a user-facing answer.

## Sources

- LeJEPA, arXiv: https://arxiv.org/abs/2511.08544
- LeWorldModel, arXiv: https://arxiv.org/abs/2603.19312
- LeWorldModel code: https://github.com/lucas-maes/le-wm
- DINO-WM, arXiv: https://arxiv.org/abs/2411.04983
- DINO-WM project: https://dino-wm.github.io/
- DINO-world, arXiv: https://arxiv.org/abs/2507.19468
- V-JEPA 2.1, arXiv: https://arxiv.org/abs/2603.14482
- Learning Latent Action World Models In The Wild, arXiv: https://arxiv.org/abs/2601.05230
- DINOv3, arXiv: https://arxiv.org/abs/2508.10104
- DINOv3 code: https://github.com/facebookresearch/dinov3

## LeJEPA And SIGReg

LeJEPA frames JEPA training as needing stronger theory and fewer heuristics. Its proposed Sketched Isotropic Gaussian Regularization constrains the embedding distribution toward an isotropic Gaussian target.

Design takeaways:

- Prediction loss alone is not enough.
- Distributional regularization is a serious alternative to EMA-target heuristics.
- A collapse-prevention choice should be stated explicitly in every JEPA design.

Use it when the user asks:

```text
Can we avoid EMA?
What is SIGReg?
How do we regularize embeddings?
Why do JEPA models collapse?
```

## LeWorldModel

LeWorldModel applies a JEPA-like latent world-model objective with a Gaussian embedding regularizer to train from pixels. The source emphasizes stable end-to-end training and latent-space planning/control.

Design takeaways:

- Compact latent prediction can support control tasks.
- Simple objectives are valuable when they reduce fragile loss stacks.
- Surprise or prediction-error signals can test physical plausibility.

For trading:

- Interesting for action-conditioned world-model research.
- Not a reason to skip passive representation probes.
- Execution data and costs remain separate requirements.

## DINO-WM

DINO-WM trains a world model over pretrained DINOv2 patch features rather than reconstructing pixels. It supports planning toward visual goals by optimizing action sequences in feature space.

Design takeaways:

- A strong frozen representation can be a world-model substrate.
- Planning can happen against goal features.
- Latent feature prediction can be cheaper and more useful than pixel prediction.

JEPA relation:

- It is JEPA-adjacent: representation-space future prediction with action-conditioned planning.
- It uses pretrained DINO features rather than learning the representation end-to-end from the same JEPA objective.

## DINO-World

DINO-world scales the idea of predicting future video in DINOv2 latent space, then explores action-conditioned fine-tuning for planning.

Design takeaways:

- Feature-space video prediction is a recurring pattern.
- Pretrained encoders can make world-model training easier.
- Action-conditioned planning is a separate layer on top of representation prediction.

Use it as a comparison point when deciding whether to train the encoder end-to-end or freeze a strong pretrained representation.

## V-JEPA 2.1

V-JEPA 2.1 focuses on dense, high-quality image and video features. The source highlights dense predictive loss, deep self-supervision across layers, multimodal tokenizers, and scaling.

Design takeaways:

- Global semantic features and dense spatial features can conflict.
- Dense prediction objectives can improve grounding.
- Intermediate-layer supervision may help representation quality.

For time series:

- Consider whether the latent needs both global regime information and local event-level detail.
- A single pooled latent may lose local structure.
- Multi-layer probes can reveal where different state variables live.

## Learning Latent Action World Models In The Wild

This work studies learning latent actions from video without explicit action labels. It uses inferred continuous latent actions to support world-model prediction and planning.

Design takeaways:

- Action labels are a bottleneck for web-scale world models.
- Continuous constrained latent actions may be more expressive than discrete codes.
- In-the-wild action spaces can become camera- or scene-relative rather than cleanly embodied.

For trading:

- Hidden actions are analogous to unobserved participant intent and hidden liquidity.
- Inferring latent actions from price movement is risky because many causes are unobserved.
- Do not treat inferred latent action as causal without interventions or strong validation.

## DINOv3

DINOv3 is not a JEPA paper, but it matters as a strong self-supervised representation baseline. It emphasizes scalable SSL, dense features, and Gram anchoring to prevent degradation of dense feature maps.

Design takeaways:

- Strong non-JEPA encoders can be hard baselines.
- Dense-feature quality matters when planning or local grounding matters.
- Representation collapse can occur at the dense-feature level, not only globally.

## How To Use These Notes

Use frontier papers to generate hypotheses, not to overrule basic validation:

```text
hypothesis -> minimal toy -> no-collapse checks -> frozen probes -> simple baselines -> time-safe validation
```

When a user asks for the latest status, browse primary sources first. These notes may be stale because several entries are recent.

## Failure Modes

- Treating frontier arXiv results as settled engineering defaults.
- Mixing too many frontier ideas in one first prototype.
- Using a pretrained visual-feature world model as direct evidence for market data.
- Inferring actions in finance and calling them causal.
- Skipping the evaluation ladder because a paper reports planning results.

## Use In This Skill

Use this reference after the foundational paper notes when a question touches SIGReg, latest JEPA work, dense features, DINO feature world models, latent actions, or planning extensions.
