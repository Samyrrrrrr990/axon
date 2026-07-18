"""Deep learning pack: build and train PyTorch networks with live loss streaming."""

from __future__ import annotations

from axon.sdk import AnyValue, Choice, Float, Int, Model, Str
from axon.sdk.node import node


class TorchNet:
    """Picklable bundle: the trained network plus everything needed to predict."""

    def __init__(self, net, classes, input_dim, arch):
        self.net = net
        self.classes = classes  # None for regression
        self.input_dim = input_dim
        self.arch = arch


def _build_net(arch: dict, input_dim: int, output_dim: int):
    import math

    import torch.nn as nn

    activations = {"relu": nn.ReLU, "tanh": nn.Tanh}
    if arch["kind"] == "mlp":
        act = activations[arch["activation"]]
        layers, prev = [], input_dim
        for width in arch["hidden"]:
            layers += [nn.Linear(prev, width), act()]
            if arch.get("dropout"):
                layers.append(nn.Dropout(arch["dropout"]))
            prev = width
        layers.append(nn.Linear(prev, output_dim))
        return nn.Sequential(*layers)

    if arch["kind"] == "cnn":
        side = int(math.isqrt(input_dim))
        if side * side != input_dim:
            raise ValueError(
                f"CNN needs square image data; got {input_dim} features "
                f"(not a perfect square). Use an MLP for tabular data."
            )
        kernel = arch.get("kernel", 3)
        layers, prev = [nn.Unflatten(1, (1, side, side))], 1
        for ch in arch["channels"]:
            layers += [nn.Conv2d(prev, ch, kernel, padding=kernel // 2), nn.ReLU(), nn.MaxPool2d(2)]
            prev = ch
            side //= 2
        if side < 1:
            raise ValueError("Too many CNN layers for this image size. Remove some channels.")
        layers += [nn.Flatten(), nn.Linear(prev * side * side, output_dim)]
        return nn.Sequential(*layers)

    raise ValueError(f"Unknown architecture kind '{arch['kind']}'")


@node(
    id="deep.mlp",
    name="Neural Net (MLP)",
    category="Deep Learning",
    description="A feed-forward neural network for tabular data.",
    outputs={"arch": "any"},
    params={
        "hidden": Str(default="64,32", help="Hidden layer sizes, comma-separated"),
        "activation": Choice(["relu", "tanh"], default="relu"),
        "dropout": Float(default=0.0, min=0.0, max=0.9),
    },
    pack="deep",
)
def mlp(ctx, hidden, activation, dropout):
    sizes = [int(s.strip()) for s in hidden.split(",") if s.strip()]
    return {"arch": AnyValue(value={"kind": "mlp", "hidden": sizes, "activation": activation, "dropout": dropout})}


@node(
    id="deep.cnn",
    name="Neural Net (CNN)",
    category="Deep Learning",
    description="A convolutional network for square image data (e.g. digits).",
    outputs={"arch": "any"},
    params={
        "channels": Str(default="16,32", help="Conv channels per block, comma-separated"),
        "kernel": Int(default=3, min=1, max=9),
    },
    pack="deep",
)
def cnn(ctx, channels, kernel):
    chans = [int(s.strip()) for s in channels.split(",") if s.strip()]
    return {"arch": AnyValue(value={"kind": "cnn", "channels": chans, "kernel": kernel})}


@node(
    id="deep.trainer",
    name="Train Neural Net",
    category="Deep Learning",
    description="Train a network on your data and watch the loss curve live.",
    inputs={"train": "dataset", "arch": "any"},
    outputs={"model": "model"},
    params={
        "task": Choice(["classification", "regression"], default="classification"),
        "epochs": Int(default=10, min=1),
        "lr": Float(default=0.001, min=0.0),
        "batch_size": Int(default=32, min=1),
        "seed": Int(default=42),
    },
    pack="deep",
)
def trainer(ctx, train, arch, task, epochs, lr, batch_size, seed):
    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(seed)
    np.random.seed(seed)

    if not train.target:
        raise ValueError("Add a 'Set Target' node so the network knows what to predict.")
    X = train.df[train.features].select_dtypes("number")
    features = list(X.columns)
    X_t = torch.tensor(X.values, dtype=torch.float32)
    y_raw = train.df[train.target]

    if task == "classification":
        classes = sorted(y_raw.unique().tolist())
        index = {c: i for i, c in enumerate(classes)}
        y_t = torch.tensor([index[v] for v in y_raw], dtype=torch.long)
        output_dim, loss_fn = len(classes), nn.CrossEntropyLoss()
    else:
        classes = None
        y_t = torch.tensor(y_raw.values, dtype=torch.float32).unsqueeze(1)
        output_dim, loss_fn = 1, nn.MSELoss()

    net = _build_net(arch.value, X_t.shape[1], output_dim)
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    loader = DataLoader(TensorDataset(X_t, y_t), batch_size=batch_size, shuffle=True)

    epochs_completed = 0
    for epoch in range(epochs):
        if ctx.cancelled:
            ctx.log(f"Cancelled after {epochs_completed} epochs")
            break
        net.train()
        total, count = 0.0, 0
        for xb, yb in loader:
            if ctx.cancelled:
                break
            optimizer.zero_grad()
            loss = loss_fn(net(xb), yb)
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * len(xb)
            count += len(xb)
        epochs_completed = epoch + 1
        avg = total / max(count, 1)
        ctx.progress(epochs_completed / epochs, {"epoch": epochs_completed, "loss": round(avg, 6)})

    wrapper = TorchNet(net=net, classes=classes, input_dim=X_t.shape[1], arch=arch.value)
    return {
        "model": Model(
            obj=wrapper,
            framework="torch",
            task=task,
            meta={"features": features, "target": train.target, "epochs_completed": epochs_completed},
        )
    }


def torch_predict(model: Model, X):
    """Used by ml.predict / ml.evaluate when the model is a torch network."""
    import numpy as np
    import torch

    wrapper: TorchNet = model.obj
    wrapper.net.eval()
    with torch.no_grad():
        out = wrapper.net(torch.tensor(X.values.astype("float32")))
    if wrapper.classes is not None:
        idx = out.argmax(dim=1).numpy()
        return np.array([wrapper.classes[i] for i in idx])
    return out.squeeze(1).numpy()


@node(
    id="deep.evaluate",
    name="Evaluate Network",
    category="Deep Learning",
    description="Score a trained network on held-out test data.",
    inputs={"model": "model", "test": "dataset"},
    outputs={"metrics": "metrics"},
    pack="deep",
)
def evaluate(ctx, model, test):
    from axon.nodes.ml import evaluate as ml_evaluate

    return ml_evaluate(ctx, model=model, test=test)


@node(
    id="deep.export",
    name="Export Model",
    category="Deep Learning",
    description="Save a trained network to disk.",
    inputs={"model": "model"},
    outputs={},
    params={
        "format": Choice(["pickle", "onnx", "torchscript"], default="pickle"),
        "path": Str(default="model.pkl", help="Output file (relative paths go to the workspace)"),
    },
    pack="deep",
)
def export(ctx, model, format, path):
    import pickle

    import torch

    target = ctx.resolve_path(path)
    if not target.is_absolute():
        target = (ctx.workspace or target.parent) / target
    target.parent.mkdir(parents=True, exist_ok=True)
    wrapper = model.obj

    if format == "pickle":
        with open(target, "wb") as f:
            pickle.dump(wrapper, f)
    elif format == "torchscript":
        scripted = torch.jit.trace(wrapper.net, torch.zeros(1, wrapper.input_dim))
        scripted.save(str(target))
    else:  # onnx
        torch.onnx.export(wrapper.net, torch.zeros(1, wrapper.input_dim), str(target))
    ctx.log(f"Exported {format} model to {target}")
    return None
