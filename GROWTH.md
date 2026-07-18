# Axon growth playbook

## Positioning

One sentence: **"n8n for machine learning — train, fine-tune, and orchestrate real AI models visually, on your own machine, free for research."**

The three claims that make people click:
1. It trains *real* models (not another ChatGPT wrapper).
2. It runs locally and is free for research (privacy + accessibility story).
3. The copilot builds the graph for you (the "replaces coding" demo moment).

The demo that sells it: a 30-second GIF — open example → press Run → loss curve falls live → ask copilot "add a confusion matrix" → nodes appear wired.

## Launch sequence

Do these in order, ~3–5 days apart, so each wave compounds the last.

### 1. Polish pass (before any post)
- [ ] Record the 30-second GIF (QuickTime + gifski) and put it at the top of the README.
- [ ] Verify `git clone` → `./axon.sh` works on a clean machine (macOS + Linux).
- [ ] Seed 3–5 GitHub issues labeled `good first issue` (each a small node: "Load JSON", "Correlation matrix", "PCA").

### 2. Show HN
- Title: `Show HN: Axon – n8n for machine learning (train real models visually, locally)`
- First comment (post it yourself immediately): what it is, why you built it (ML research is gated behind coding skill), what works today (47 nodes, 3 domains, copilot), what doesn't yet (roadmap), the licensing model, and a direct ask for feedback on the node SDK.
- Be online for 6 hours answering everything. HN rewards responsive founders.

### 3. Reddit (staggered, tailored — never cross-post identical text)
- **r/MachineLearning** (`[P]` tag): lead with the *research accessibility* angle and the caching/experiment-iteration story.
- **r/LocalLLaMA**: lead with local LoRA fine-tuning + Ollama support + "your data never leaves your machine."
- **r/selfhosted**: lead with the one-command local install and the fair-code license.
- **r/datascience**: lead with "teach ML without teaching Python first" (educators are a huge quiet audience).

### 4. Product Hunt
- Launch after HN/Reddit so you arrive with stars and testimonials.
- Assets: the GIF, 4 screenshots (canvas, live training, copilot, gallery), a 60-second video.

### 5. Content drumbeat (1/week)
- "I trained a house-price model without writing a line of code" (walkthrough)
- "Fine-tuning GPT-2 on my own quotes, visually" (fine-tuning audience)
- "How Axon's caching makes ML iteration feel instant" (technical deep-dive, HN-bait)
- "Building a research agent with tools — no framework, just nodes"

## The community flywheel

1. **Workflows are shareable files** → encourage a `#show-your-workflow` channel/discussion; retweet/repost everything.
2. **Nodes are 20 lines** → every "can Axon do X?" answer is "here's the 20-line node, want to PR it?" Contributors become evangelists.
3. **Examples gallery grows from community workflows** → merge good ones into `examples/` with credit.
4. Later: a registry (`axon-packs`) indexing community packs; the n8n/Obsidian plugin-ecosystem play.

## Channels to set up (day 1, zero cost)
- [ ] GitHub Discussions on (Q&A + Show and tell categories)
- [ ] Discord server (invite link in README) — #help, #show-your-workflow, #node-dev
- [ ] Twitter/X + Bluesky account posting GIFs of workflows

## Metrics that matter (weekly)
- GitHub stars (vanity but drives discovery), **clones→first-run rate** (the real funnel), examples opened, workflows shared, node-pack PRs, Discord members asking questions (activation signal).

## Monetization path (when traction arrives)
1. Now: commercial licenses via COMMERCIAL_LICENSE.md inquiries.
2. Next: hosted Axon (same codebase, cloud runs, team workspaces) — the n8n cloud model.
3. Later: priority support + certified packs for commercial users.

Keep the free tier genuinely great forever — the noncommercial community IS the product's moat.
