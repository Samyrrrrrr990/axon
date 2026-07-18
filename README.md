# Axon

**Build real AI visually — train, fine-tune, and orchestrate models without writing code.**

Axon is what n8n did for automation, applied to machine learning. Drag nodes onto a canvas, wire them together, press Run: load a dataset, train a random forest or a neural network, LoRA-finetune a language model, or compose a RAG pipeline with agents — all on your own machine, no code required. (You can still drop into Python anytime with the code node. But why?)

![Axon canvas — a house-price model trained and evaluated visually](docs/assets/canvas.png)

## Why Axon

- **Real ML, not just API calls.** Train scikit-learn, XGBoost, and PyTorch models locally. Watch the loss curve fall in real time.
- **Fine-tune LLMs visually.** LoRA fine-tuning of Hugging Face models as a five-node graph.
- **LLM pipelines & agents.** RAG over your own documents, tools, agent loops — with free OpenRouter models, Claude/GPT, or local Ollama.
- **A copilot that builds graphs.** Type "train a model that predicts house prices from this CSV" and watch the nodes appear, wired and configured. It emits graph operations, never code.
- **Smart caching.** Change one node, re-run, and only the changed part of the pipeline recomputes. Iteration feels instant.
- **Local-first.** Your data never leaves your machine unless you explicitly connect a cloud model. Workflows are single portable `.axon.json` files — send one to a colleague.

## Quickstart (60 seconds)

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/Samyrrrrrr990/axon.git
cd axon
./axon.sh
```

Your browser opens at `http://localhost:8700` with a gallery of examples. Open **Predict House Prices**, press **Run**, and watch a model train. The core install is light; heavy packs (PyTorch, Transformers, RAG) install with one click when you first need them.

Run any workflow headless, too:

```bash
uv run python -m axon run examples/house-prices.axon.json
```

## What's in the box

| Domain | Nodes |
|---|---|
| Data | CSV/Excel, sample datasets, Hugging Face datasets, split, scale, encode, impute |
| Classical ML | linear/logistic regression, random forest, XGBoost, k-means, evaluate, confusion matrix |
| Deep learning | MLP/CNN builders, PyTorch trainer with live loss, evaluate, ONNX/TorchScript export |
| Fine-tuning | pretrained model loader, tokenizer, LoRA fine-tune, generate, save adapter |
| LLM & agents | chat models (OpenRouter/Anthropic/OpenAI/Ollama), prompts, structured extract, embeddings, vector store, RAG, tools, agent loop |
| Utility | Python code (the escape hatch), charts, table/metric viewers, file output |

47 nodes at launch. Writing your own takes ~20 lines of Python — see [docs/writing-nodes.md](docs/writing-nodes.md).

## The copilot

Open the Copilot sidebar, paste a free [OpenRouter key](https://openrouter.ai/keys), and describe what you want. The copilot reads your graph and the node catalog, then emits validated graph edits you can undo. Swap in Claude, GPT, or a local Ollama model in Settings.

## License: free for research, paid for profit

Axon is [PolyForm Noncommercial](LICENSE.md): **free forever** for academic research, non-profits, personal projects, and learning. For-profit use requires a [commercial license](COMMERCIAL_LICENSE.md) — that's what funds free access for everyone else.

## Roadmap

- Community node packs (pip-installable, auto-discovered)
- Workflow sharing gallery
- Experiment tracking & run comparison
- Hosted cloud option for teams

## Contributing

The fastest way to help: build a node pack. See [CONTRIBUTING.md](CONTRIBUTING.md) — your first node in 20 lines. Bug reports and example workflows are equally welcome.

---

Built with FastAPI, React Flow, scikit-learn, PyTorch, and the conviction that ML research shouldn't require a CS degree.
