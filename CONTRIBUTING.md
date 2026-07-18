# Contributing to Axon

Thank you for considering a contribution. This document covers the development setup, the node SDK, and what we look for in pull requests.

## Development setup

```bash
git clone https://github.com/Samyrrrrrr990/axon.git
cd axon
uv sync --extra dev
uv run pytest
```

That installs the light core and runs the backend test suite. For the frontend:

```bash
cd web
npm install
npm run build
```

Run the app with `./axon.sh`. To work on the heavy packs locally:

```bash
uv sync --extra dev --extra ml-boost --extra deep --extra finetune --extra rag
```

## Writing your first node

Nodes are decorated Python functions. The palette entry, the form fields, the typed sockets, and the output preview are all generated from the declaration, so there is no frontend work involved.

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

Add the module name to the list in `axon/nodes/__init__.py`, restart the server, and the node appears in the palette with typed sockets and a working form.

The contract:

- The first argument is `ctx`. It provides `ctx.log`, `ctx.progress(fraction, metrics)`, `ctx.cancelled`, and `ctx.resolve_path`.
- Input and output types are socket names from `axon/sdk/containers.py`, such as `dataset`, `model`, `text`, `docs`, `metrics`, `chart`, and `any`.
- Heavy imports go inside the function body, and the node declares the matching `pack=` so the dependency installs lazily.
- Long-running loops call `ctx.progress()` and check `ctx.cancelled` so users can watch and cancel.
- When a user wires something wrong, raise `ValueError` with a message a non-programmer can act on.

The full reference is in [docs/writing-nodes.md](docs/writing-nodes.md).

## Tests

Every node needs a test. See `tests/nodes/` for the pattern: call the function directly with the `ctx` fixture.

```python
def test_head(ctx):
    ds = D.sample_dataset(ctx, name="iris")["dataset"]
    out = head(ctx, dataset=ds, n=5)["dataset"]
    assert out.df.shape[0] == 5
```

Run `uv run pytest` before opening a pull request. CI runs the same suite plus a headless end-to-end workflow on every push.

## Style

- Python: type hints where they clarify, plain-language error messages, and no heavy imports at module top inside node packs.
- Frontend: use the design tokens in `web/src/index.css`. Socket colors encode the type system and should not be repurposed.
- Commit messages follow the conventional `feat:`, `fix:`, `docs:` prefixes used in the history.

## Proposing larger changes

For a new node pack or an engine change, open an issue first (there is a "node pack proposal" template). A short description of the nodes and their sockets is enough to start the conversation.

## Licensing of contributions

Axon is licensed under PolyForm Noncommercial 1.0.0. By contributing, you agree that your contribution is licensed under the same terms.
