# Growth playbook

Internal document. This is the launch and community plan for Axon.

## Positioning

One sentence: "n8n for machine learning: train, fine-tune, and orchestrate real AI models visually, on your own machine, free for research."

Three claims carry the pitch:

1. It trains real models locally, not just calls to a chat API.
2. It is free for research and runs on your own hardware, which is both a privacy story and an accessibility story.
3. The copilot assembles graphs from plain descriptions.

The demo that sells it is a 30-second recording: open an example, press Run, watch the loss curve fall, then ask the copilot to add a confusion matrix and watch the nodes appear already wired.

## Launch sequence

Space these three to five days apart so each wave builds on the previous one.

### 1. Polish pass, before any post

- Record the 30-second demo and place it at the top of the README.
- Verify that `git clone` then `./axon.sh` works on a clean macOS and a clean Linux machine.
- Seed three to five issues labeled `good first issue`, each a small self-contained node such as "Load JSON", "Correlation matrix", or "PCA".

### 2. Show HN

Suggested title: `Show HN: Axon, an n8n-style visual builder for training real ML models locally`.

Post a first comment immediately covering: what it is, why you built it (ML research is gated behind coding skill), what works today, what does not work yet, and the licensing model. End with a direct question about the node SDK to invite specific feedback. Stay online for six hours and answer everything.

### 3. Reddit

Tailor each post to the community. Do not cross-post identical text.

| Subreddit | Angle |
|---|---|
| r/MachineLearning (`[P]` tag) | research accessibility, caching and iteration speed |
| r/LocalLLaMA | local LoRA fine-tuning, Ollama support, data never leaves the machine |
| r/selfhosted | one-command local install, source-available license |
| r/datascience | teaching ML without teaching Python first |

### 4. Product Hunt

Launch after the HN and Reddit waves so the page arrives with stars and quotes. Assets needed: the demo recording, four screenshots (canvas, live training, copilot, gallery), and a 60-second video.

### 5. Content, one piece per week

- A walkthrough of training a house-price model with no code
- Fine-tuning GPT-2 on your own text, visually
- A technical deep-dive on the caching design
- Building a research agent with tools, using only nodes

## Community flywheel

1. Workflows are single shareable files. Create a "show your workflow" channel and repost everything good.
2. Nodes take 20 lines. Every "can Axon do X" question gets the answer "here is the node, want to PR it?" Contributors tend to become advocates.
3. The examples gallery grows from community workflows, merged with credit.
4. Later: a registry that indexes community node packs, following the n8n and Obsidian plugin ecosystem model.

## Channels to set up on day one

- GitHub Discussions with Q&A and Show-and-tell categories
- A Discord server with help, show-your-workflow, and node-dev channels, linked from the README
- A social account that posts short recordings of workflows

## Metrics

Watch weekly: stars (drives discovery), the clone-to-first-run rate (the real funnel), examples opened, workflows shared, node pack pull requests, and the number of new people asking questions (an activation signal).

## Monetization path

1. Now: commercial licenses through COMMERCIAL_LICENSE.md inquiries.
2. Next: a hosted version of the same codebase with cloud runs and team workspaces.
3. Later: priority support and certified packs for commercial customers.

The noncommercial community is the moat. The free tier stays genuinely good.
