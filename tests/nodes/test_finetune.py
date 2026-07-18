import pytest

pytest.importorskip("transformers")
pytest.importorskip("peft")

from axon.nodes import finetune as FT
from axon.sdk import TextDocs

TINY = "sshleifer/tiny-gpt2"

DOCS = TextDocs(
    docs=[
        {"id": str(i), "text": f"Quote {i}: the quick brown fox jumps over the lazy dog.", "meta": {}}
        for i in range(8)
    ]
)


@pytest.fixture(scope="module")
def hf_model():
    import threading

    from axon.sdk.context import NodeContext

    ctx = NodeContext(workspace=None, settings={}, cancel_event=threading.Event())
    return FT.load_model(ctx, model_name=TINY)["hf_model"]


def test_load_model(hf_model):
    tokenizer, model = hf_model.value
    assert tokenizer is not None and model is not None


def test_docs_from_dataset(ctx):
    import pandas as pd

    from axon.sdk import Dataset

    ds = Dataset(df=pd.DataFrame({"quote": ["a", "b"], "author": ["x", "y"]}))
    docs = FT.docs_from_dataset(ctx, dataset=ds, text_column="quote")["docs"]
    assert [d["text"] for d in docs.docs] == ["a", "b"]


def test_lora_finetune_and_generate(ctx, hf_model):
    tokenized = FT.text_data(ctx, docs=DOCS, hf_model=hf_model, max_length=32)["tokenized"]
    model = FT.lora_finetune(
        ctx, hf_model=hf_model, tokenized=tokenized,
        r=4, alpha=8, epochs=1, lr=2e-4, batch_size=4, seed=0,
    )["model"]
    assert model.framework == "hf"
    assert model.meta["train_loss"] is not None

    out = FT.generate(ctx, model=model, prompt="Quote", max_new_tokens=8, temperature=0.8)["text"]
    assert isinstance(out.text, str) and len(out.text) > 0


def test_save_adapter(ctx, tmp_path, hf_model):
    tokenized = FT.text_data(ctx, docs=DOCS, hf_model=hf_model, max_length=32)["tokenized"]
    model = FT.lora_finetune(
        ctx, hf_model=hf_model, tokenized=tokenized,
        r=4, alpha=8, epochs=1, lr=2e-4, batch_size=4, seed=0,
    )["model"]
    ctx.workspace = tmp_path
    FT.save_adapter(ctx, model=model, name="test-adapter")
    saved = list((tmp_path / "data" / "adapters" / "test-adapter").glob("*"))
    assert any("adapter" in p.name for p in saved)
