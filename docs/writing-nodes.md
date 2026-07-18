# Writing nodes

A node is a Python function with a declaration. The palette entry, the form fields, the typed sockets, wire-time validation, caching, and output previews are all derived from that declaration.

## Anatomy

```python
from axon.sdk import Choice, Dataset, Float
from axon.sdk.node import node

@node(
    id="stats.outliers",                    # unique, dot-namespaced
    name="Remove Outliers",                 # what users see in the palette
    category="Data",                        # palette group
    description="Drop rows more than k standard deviations from the mean.",
    inputs={"dataset": "dataset"},          # socket name -> socket type
    outputs={"dataset": "dataset"},
    params={
        "k": Float(default=3.0, min=0.5, help="How strict to be"),
        "mode": Choice(["clip", "drop"], default="drop"),
    },
    pack="core",                            # or ml-boost / deep / finetune / rag
    cacheable=True,                         # False for anything nondeterministic
)
def outliers(ctx, dataset, k, mode):
    ...
    return {"dataset": Dataset(df=filtered, target=dataset.target)}
```

## Socket types

Socket types are defined in `axon/sdk/containers.py`. Wires only connect matching types, with `any` compatible with everything.

| Type | Container | Carries |
|---|---|---|
| `dataset` | `Dataset` | DataFrame plus target column |
| `model` | `Model` | trained estimator plus framework tag |
| `metrics` | `Metrics` | dict of scores |
| `text` | `TextValue` | a string |
| `docs` | `TextDocs` | list of documents |
| `embeddings` | `Embeddings` | vectors plus their documents |
| `vectorstore` | `VectorStoreRef` | reference to a Chroma collection |
| `chart` | `ChartSpec` | data the UI renders as a chart |
| `image` | `ImageRef` | path to an image |
| `any` | `AnyValue` | anything |

Each container has a `preview()` method that powers the output panel. Return real containers and previews come free.

## Parameter kinds

`Int`, `Float`, `Str`, `Text` (multiline), `Bool`, `Choice`, `FilePath`, `Secret`, and `Json`. Each renders as the matching form control automatically.

## The context object

- `ctx.log("...")` streams a line to the run log.
- `ctx.progress(0.4, {"epoch": 4, "loss": 0.12})` drives the live metric chart.
- `ctx.cancelled` should be checked inside loops; stop promptly when it is True.
- `ctx.resolve_path(p)` resolves relative paths against the workflow's folder.
- `ctx.workspace` is the Axon home directory, for artifacts worth keeping.
- `ctx.settings` holds provider keys and defaults, for nodes that call LLMs.

## Rules of thumb

1. Heavy imports (`torch`, `transformers`) go inside the function body, and the node declares the matching `pack=` so Axon can offer one-click installation.
2. Raise `ValueError` with a sentence a non-programmer understands. "No column named 'price'. Columns: ..." beats a bare KeyError.
3. Deterministic nodes take a `seed` parameter. Nondeterministic nodes set `cacheable=False`.
4. Return new containers instead of mutating inputs, because cached outputs are shared between runs.

## Shipping a community pack

Any pip-installable module that registers nodes on import works. Automatic discovery through entry points is on the roadmap. For now, packs land through pull requests that add a module to `axon/nodes/`; open an issue with the "node pack proposal" template first.
