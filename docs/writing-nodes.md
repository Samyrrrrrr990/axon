# Writing Axon nodes

A node is a Python function with a declaration. Everything else — the palette entry, the form fields, the typed sockets, wire-time validation, caching, previews — is derived from that declaration.

## Anatomy

```python
from axon.sdk import Choice, Dataset, Float, Int, Metrics
from axon.sdk.node import node

@node(
    id="stats.outliers",                    # unique, dot-namespaced
    name="Remove Outliers",                 # what users see
    category="Data",                        # palette group
    description="Drop rows more than k standard deviations from the mean.",
    inputs={"dataset": "dataset"},          # socket name -> socket type
    outputs={"dataset": "dataset"},
    params={
        "k": Float(default=3.0, min=0.5, help="How strict to be"),
        "mode": Choice(["clip", "drop"], default="drop"),
    },
    pack="core",                            # or ml-boost / deep / finetune / rag
    cacheable=True,                         # False for anything nondeterministic (LLM calls)
)
def outliers(ctx, dataset, k, mode):
    ...
    return {"dataset": Dataset(df=filtered, target=dataset.target)}
```

## Socket types

Defined in `axon/sdk/containers.py`. Wires only connect matching types (or `any`):

| type | container | carries |
|---|---|---|
| `dataset` | `Dataset` | DataFrame + target column |
| `model` | `Model` | trained estimator + framework tag |
| `metrics` | `Metrics` | dict of scores |
| `text` | `TextValue` | a string |
| `docs` | `TextDocs` | list of documents |
| `embeddings` | `Embeddings` | vectors + their docs |
| `vectorstore` | `VectorStoreRef` | path to a Chroma collection |
| `chart` | `ChartSpec` | data the UI renders as a chart |
| `image` | `ImageRef` | path to an image |
| `any` | `AnyValue` | anything |

Each container has a `.preview()` that powers the output panel — return real containers and previews come free.

## Param kinds

`Int`, `Float`, `Str`, `Text` (multiline), `Bool`, `Choice`, `FilePath`, `Secret`, `Json` — each renders as the right form control automatically.

## The context object

- `ctx.log("...")` — streams to the run log
- `ctx.progress(0.4, {"epoch": 4, "loss": 0.12})` — drives the live metric chart
- `ctx.cancelled` — check inside loops; stop promptly when True
- `ctx.resolve_path(p)` — resolves relative paths against the workflow's folder
- `ctx.workspace` — the Axon home dir for artifacts you want to keep
- `ctx.settings` — provider keys/defaults (for LLM-calling nodes)

## Rules of thumb

1. Heavy imports (`torch`, `transformers`) go inside the function body; declare the matching `pack=` so Axon offers one-click install.
2. Raise `ValueError` with a sentence a non-programmer understands. "No column named 'price'. Columns: …" beats a KeyError.
3. Deterministic nodes get a `seed` param; nondeterministic nodes set `cacheable=False`.
4. Return new containers instead of mutating inputs — cached outputs are shared.

## Shipping a community pack

Any pip-installable module that registers nodes on import works. Auto-discovery via entry points is on the roadmap; for now, packs land through PRs adding a module to `axon/nodes/` — open an issue with the `node pack proposal` template first.
