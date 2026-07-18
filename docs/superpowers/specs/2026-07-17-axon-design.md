# Axon — Design Spec

**Date:** 2026-07-17
**Status:** Approved by user

## What Axon is

Axon is a local-first, n8n-style visual platform for building AI — real machine learning, not just automation. Users drag nodes onto a canvas, wire them together, and hit Run to train models, fine-tune pretrained models, or compose LLM/agent pipelines — without writing code. Code remains available as an escape hatch (Python code node), but is never required.

**Mission:** revolutionize accessibility of machine-learning research. Free for non-profit research, paid for for-profit use.

## Product decisions (settled with user)

| Decision | Choice |
|---|---|
| V1 scope | All three domains: train real ML models, fine-tune pretrained models, LLM/agent pipelines |
| Form factor | Local web app — one command starts a server, opens `localhost:8700` in browser |
| Name | **Axon** |
| License | PolyForm Noncommercial 1.0.0 + `COMMERCIAL_LICENSE.md` (contact for commercial licensing) |
| AI copilot | In v1. Default: free model via OpenRouter (user's free API key). Optional: paid models (Anthropic/OpenAI) or local Ollama |
| Monetization in v1 | License text only — no billing, accounts, or cloud hosting |

## Architecture

**Python-native monorepo.** One FastAPI server serves the REST/WebSocket API and the built React frontend. The execution engine and all nodes are pure Python — the same runtime as the entire ML ecosystem (PyTorch, scikit-learn, transformers, peft), so writing a node never crosses a language boundary.

```
axon/
├── axon/                    # Python package (server + engine + nodes)
│   ├── server/              # FastAPI app, REST + WebSocket endpoints
│   ├── engine/              # Graph model, executor, caching, run manager
│   ├── sdk/                 # @node decorator, param/socket types, registry
│   ├── nodes/               # Built-in node packs (data, ml, deep, finetune, llm, util)
│   ├── copilot/             # Graph-building AI assistant
│   └── storage/             # Workspace, workflow files, SQLite run history
├── web/                     # React + Vite + React Flow canvas UI
├── examples/                # Shareable .axon.json example workflows
├── docs/                    # User + contributor docs
└── tests/                   # pytest suites
```

### Environment management

- Bootstrap via `uv` — users never touch pip. `./axon.sh` (or `uvx axon` once published) creates the venv, installs core deps, starts the server, opens the browser.
- **Lazy dependency packs**: core install is light (FastAPI, pandas, scikit-learn). Heavy packs (PyTorch, transformers/peft, vector store) install on demand — when a user first adds a node needing an uninstalled pack, the UI offers one-click install with progress.

### The engine

- A workflow is a JSON graph: nodes (id, type, params, position) + edges (source socket → target socket).
- Execution: topological sort, node-by-node. Cycles rejected at validation (except inside the agent-loop node, which encapsulates its own iteration).
- **Content-addressed caching**: each node's output is cached on disk, keyed by hash(node type + params + upstream output hashes). Re-running a tweaked workflow recomputes only what changed. Cache lives in the workspace; clearable per-workflow.
- **Live streaming**: per-node status (queued/running/done/error), logs, and metric streams (e.g. training loss per epoch) go to the UI over WebSocket during the run. Training nodes report progress callbacks; UI renders live charts.
- Runs are cancellable. Node errors halt downstream execution, mark the node red, and surface the Python error plainly (with a human-readable hint where we can map common failures).

### Node SDK

A node is a decorated Python function:

```python
@node(
    id="ml.random_forest",
    name="Random Forest",
    category="Classical ML",
    inputs={"train": Dataset},
    outputs={"model": Model},
    params={
        "n_estimators": Int(default=100, min=1, help="Number of trees"),
        "task": Choice(["classification", "regression"], default="classification"),
    },
)
def random_forest(train, n_estimators, task):
    ...
```

- The UI (form controls, socket types/colors, node docs) is **auto-generated** from the declaration. No frontend work to add a node.
- Socket types (Dataset, Model, Text, Embeddings, Image, Any...) are checked at wire-time — incompatible connections are refused with an explanation.
- Data passed between nodes uses a small set of standard containers (e.g. Dataset wraps a DataFrame + metadata; Model wraps estimator + framework tag) so packs compose.
- Community packs: any pip-installable package exposing nodes via entry points. `docs/writing-nodes.md` targets "your first node in 20 lines."

### V1 node packs (~40 nodes)

- **Data**: Load CSV/Excel, Hugging Face dataset, image folder, sample datasets (iris, california housing, etc.), train/test split, select columns, scale/normalize, encode categoricals, handle missing values
- **Classical ML**: linear regression, logistic regression, random forest, XGBoost, k-means, evaluate (metrics), confusion matrix
- **Deep learning**: neural net builder (MLP/CNN via layer list), PyTorch trainer (live loss curve), evaluator, save/export (ONNX, pickle), predict
- **Fine-tuning**: HF model loader, text dataset prep/tokenize, LoRA/PEFT fine-tune, save adapter / push to Hub
- **LLM & agents**: chat model (OpenRouter, Ollama, Anthropic, OpenAI — configurable per node), prompt template, structured extract, embed text, local vector store (Chroma), retriever, RAG answer, tool definition, agent loop
- **Utility**: Python code node, chart (line/bar/scatter), view table, view image, view metrics, text input/output, file output

### Copilot

- Chat sidebar in the UI. Context = current graph JSON + node catalog (ids, descriptions, socket types).
- Emits **graph operations as structured JSON** (add/remove/rewire/set-params) — never arbitrary code. Changes appear on canvas immediately; user can undo. One retry pass if the emitted graph fails validation.
- Provider config in Settings: default is OpenRouter with a curated free model; paid Anthropic/OpenAI keys or local Ollama as alternatives. Keys stored locally in workspace config, never leave the machine except to the chosen provider.

### Frontend

- React + TypeScript + Vite + React Flow + Tailwind. Dark-first theme; polished, non-generic visual identity (this is the product's face — design effort is warranted).
- Canvas: drag nodes from a searchable palette, wire sockets, pan/zoom, minimap, undo/redo, multi-select.
- Node inspector panel: auto-generated param forms, per-node output preview after runs (table/image/chart/metrics).
- Run bar: Run / Cancel, per-node status colors on canvas, live logs drawer.
- Copilot sidebar. Settings modal (providers/keys, dependency packs). Workflow manager (list, create, import/export `.axon.json`).
- First-run experience: gallery of the 5 example workflows front and center — "open → Run → watch it train."

### Storage

- Workspace at `~/.axon/` (config, cache, SQLite run history). Workflows saved as portable single-file `.axon.json` (graph + metadata, no absolute paths) — shareable by design.
- Run history: SQLite via a thin layer; per-run node timings, statuses, logs, metric series.

## Examples shipped (all runnable offline except LLM ones)

1. **Predict house prices** — CSV → clean → split → random forest → metrics + chart (classical ML)
2. **Handwritten digit classifier** — image data → CNN → live training curve → confusion matrix (deep learning)
3. **Fine-tune a tiny LLM** — small HF model + LoRA on a sample dataset (fine-tuning; CPU-feasible tiny model)
4. **Chat with your documents** — folder → embed → vector store → RAG answer (LLM)
5. **Research agent** — agent loop + tools (LLM)

## Testing

- pytest: engine (graph validation, topo sort, caching, cancellation), SDK (decorator → schema), every node pack (unit level, heavy deps mocked or skipped when uninstalled), copilot graph-op application.
- End-to-end: run examples 1–2 headlessly in CI (small data, CPU).
- Frontend: production build must pass + a Playwright smoke test (load app, open example, see canvas).
- CI: GitHub Actions on push/PR.

## Repo & launch

- Public GitHub repo (user's account): LICENSE (PolyForm Noncommercial 1.0.0), `COMMERCIAL_LICENSE.md`, README with demo GIF + quickstart, CONTRIBUTING.md (first node in 20 lines), issue templates, `examples/` gallery.
- `GROWTH.md` playbook: launch sequencing (Show HN, r/MachineLearning, r/LocalLLaMA, Product Hunt), community flywheel (shareable workflows, node-pack ecosystem, Discord), content angles ("I trained a model without writing code").

## Explicitly out of v1

Billing/accounts, cloud hosting, plugin marketplace UI, collaborative editing, Windows-native installer (uv covers Windows via script), distributed training.

## Success criteria

A non-coder can: start Axon with one command, open the house-prices example, hit Run, watch it train, see metrics — then ask the copilot to "add a chart comparing predictions to actual prices" and get a working modified graph.
