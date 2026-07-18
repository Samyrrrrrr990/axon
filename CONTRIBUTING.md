# Contributing to Axon

## Dev setup

```bash
git clone https://github.com/Samyrrrrrr990/axon.git
cd axon
uv sync --extra dev            # core + test deps (light)
uv run pytest                  # backend tests
cd web && npm install && npm run build   # frontend
./axon.sh                      # run the app
```

Optional heavy packs for local testing: `uv sync --extra dev --extra ml-boost --extra deep --extra finetune --extra rag`.

## Your first node in 20 lines

Nodes are decorated Python functions. The UI form, sockets, and docs are generated from the declaration — no frontend work.

```python
# axon/nodes/my_pack.py
from axon.sdk import Dataset, Int
from axon.sdk.node import node

@node(
    id="my.head",
    name="First N Rows",
    category="Data",
    description="Keep only the first N rows of a dataset.",
    inputs={"dataset": "dataset"},
    outputs={"dataset": "dataset"},
    params={"n": Int(default=10, min=1, help="How many rows to keep")},
)
def head(ctx, dataset, n):
    ctx.log(f"Keeping first {n} rows")
    return {"dataset": Dataset(df=dataset.df.head(n), target=dataset.target)}
```

Add the module name to the list in `axon/nodes/__init__.py`, restart, and your node is in the palette — typed sockets, form field, and all.

**The contract:**
- First argument is `ctx` (`ctx.log`, `ctx.progress(fraction, metrics)`, `ctx.cancelled`, `ctx.resolve_path`).
- Inputs/outputs are socket-type names from `axon/sdk/containers.py` (`dataset`, `model`, `text`, `docs`, `metrics`, `chart`, `any`, …).
- Heavy imports go **inside** the function, and the node declares `pack="deep"` (etc.) so it installs lazily.
- Long-running loops should call `ctx.progress()` and check `ctx.cancelled`.
- Raise `ValueError` with a plain-language message when the user wires something wrong.

## Tests

Every node needs a test (see `tests/nodes/`). Call the function directly with the `ctx` fixture:

```python
def test_head(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    out = head(ctx, dataset=ds, n=5)["dataset"]
    assert out.df.shape[0] == 5
```

Run `uv run pytest` before opening a PR. CI runs the same suite plus a headless end-to-end workflow.

## Style

- Python: type hints where they help, plain-language error messages, no heavy imports at module top in packs.
- Frontend: match the existing token system in `web/src/index.css`; socket colors are part of the design language.

## Licensing note

Axon is PolyForm Noncommercial. By contributing you agree your contribution is licensed the same way.
