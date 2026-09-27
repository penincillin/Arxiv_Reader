# Ranking Papers

Use the following rubric as a decision aid rather than a mechanical citation score.

| Dimension | Weight | What to examine |
|---|---:|---|
| Topic fit | 35% | Directly advances the requested topic rather than merely applying a model in an unrelated domain |
| Technical and empirical quality | 30% | Clear problem, meaningful novelty, appropriate baselines, controlled ablations, realistic scale, and evidence that supports the claims |
| Open artifacts | 15% | Working code, data, weights, benchmark, or reproducible recipe; distinguish available artifacts from “coming soon” claims |
| Publication signal | 10% | Explicit acceptance/publication is stronger than submission language; a recognizable template alone is only a weak signal |
| Team and affiliation | 10% | Relevant track record, credible collaboration, and capacity to run the reported study; do not use prestige as a proxy for correctness |

## Topic boundaries

### World model

Include learned environment dynamics, predictive representations, action-conditioned models, planning through learned dynamics, world-action models, and evaluation that tests whether predictions improve control. Exclude generic forecasting that has no connection to agents, physical environments, or learned state transitions.

### Video generation

Include text/image-to-video generation, video diffusion, causal or streaming video generation, audio-video generation, video-generation post-training, acceleration, controllability, and evaluation of generated videos. Video understanding or retrieval is adjacent rather than direct; include it only to fill a requested quota and label it.

### LLM and multimodal LLM

Include foundation-model architecture, training and post-training, inference systems, reasoning, alignment, interpretability, evaluation, safety, agents, VLMs, MLLMs, and audio-language models. Down-rank narrow domain applications unless they introduce a reusable method or unusually strong evidence.

## Evidence rules

- Prefer reported measurements over qualitative claims.
- Look for evaluation breadth, strong baselines, ablations, human evaluation where appropriate, and real-world tests for embodied systems.
- Verify repository and project links. A paper that merely cites public datasets is not itself an artifact release.
- Do not call a team “Qwen,” “Wan,” or another organization merely because its method uses that model or its repository name contains the term.
- Record unknown or undisclosed affiliations explicitly rather than guessing.
- If arXiv comments say “accepted,” “published,” or name a final track, report that wording. If only source files reveal `iclr`, `neurips`, `aaai`, `acl`, `ieeeconf`, or `usenix`, report “uses the X template; acceptance not established.”

