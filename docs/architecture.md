# Architecture

One Python process serves everything: a FastAPI app exposing REST and WebSocket APIs, the built React frontend, and a pure-Python execution engine underneath.

```
browser (React + React Flow)
   |  REST: workflows, runs, settings, packs, copilot
   |  WS:   run events (status, logs, live metrics)
   v
FastAPI (axon/server)
   +- RunManager (axon/engine/runs.py)      one thread per run
   |    +- execute_workflow (executor.py)   topological order, cache, events
   |         +- nodes (axon/nodes/*)        decorated Python functions
   +- WorkflowStore (.axon.json files)
   +- RunHistory (SQLite)
   +- Copilot (graph operations over any chat provider)
```

## The life of a run

1. `POST /api/runs` validates the graph (socket types, cycles, required inputs) and returns a run id.
2. A worker thread executes nodes in topological order. Each node's cache key is a hash of its type, its parameters, its upstream cache keys, and the package version. On a cache hit the outputs load from disk and the node is marked `cached`.
3. Every event (`node_started`, `node_progress`, `node_log`, `node_finished`, `node_failed`, `run_finished`) fans out to three consumers: the WebSocket hub for the UI, the SQLite run history, and the in-memory run state behind `GET /api/runs/{id}`.
4. When a node fails, the error carries a plain-language hint where one can be inferred. Downstream nodes are skipped and independent branches continue.

## Invariants

- Nodes never see the graph. They receive their inputs, their parameters, and a context object. All orchestration lives in the engine.
- Nodes that call language models are declared uncacheable, and anything downstream of an uncacheable node re-runs.
- The copilot emits graph operations, never code. Operations are applied to a copy of the workflow, validated, and only then returned. On validation failure it gets one retry with the errors included.
- Workflows are portable. No absolute paths are persisted; file parameters resolve against the workflow's own directory at run time.
- Heavy dependencies are lazy. Node modules import them inside function bodies, and `axon/server/packs.py` installs the matching extra on demand.
