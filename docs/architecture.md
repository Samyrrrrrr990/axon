# Axon architecture

One Python process serves everything: a FastAPI app exposing REST + WebSocket APIs and the built React frontend, with a pure-Python execution engine underneath.

```
browser (React + React Flow)
   │  REST: workflows, runs, settings, packs, copilot
   │  WS:   run events (status, logs, live metrics)
   ▼
FastAPI (axon/server)
   ├─ RunManager (axon/engine/runs.py)      one thread per run
   │    └─ execute_workflow (executor.py)   topo order, cache, events
   │         └─ nodes (axon/nodes/*)        decorated Python functions
   ├─ WorkflowStore (.axon.json files)
   ├─ RunHistory (SQLite)
   └─ Copilot (graph-ops protocol over any chat provider)
```

## The flow of a run

1. `POST /api/runs` validates the graph (types, cycles, required inputs) and returns a `run_id`.
2. A worker thread executes nodes in topological order. Each node's cache key = hash(type + params + upstream keys + version). Hit → outputs load from disk, marked `cached`.
3. Every event (`node_started`, `node_progress`, `node_log`, `node_finished`, `node_failed`, `run_finished`) fans out to: the WebSocket hub (→ UI), SQLite run history, and the in-memory run state served by `GET /api/runs/{id}`.
4. Failures carry a plain-language `hint` where we can map the exception; downstream nodes are skipped, independent branches continue.

## Key invariants

- **Nodes never see the graph** — only their inputs, params, and `ctx`. All orchestration lives in the engine.
- **LLM-calling nodes are uncacheable**, and anything downstream of an uncacheable node re-runs.
- **The copilot emits graph operations, never code.** Ops are applied to a copy, validated, and only then returned; one retry with the validation errors on failure.
- **Workflows are portable**: no absolute paths persisted; file params resolve against the workflow's own directory at run time.
- **Heavy deps are lazy**: node modules import them inside functions; `axon/server/packs.py` installs extras on demand.
