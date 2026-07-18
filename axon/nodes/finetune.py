"""Fine-tuning pack — LoRA-adapt pretrained Hugging Face models on your own text."""

from __future__ import annotations

from axon.sdk import AnyValue, Float, Int, Model, Str, TextDocs, TextValue
from axon.sdk.node import node


@node(
    id="ft.load_model",
    name="Load Pretrained Model",
    category="Fine-tuning",
    description="Download a pretrained language model from the Hugging Face Hub.",
    outputs={"hf_model": "any"},
    params={"model_name": Str(default="distilgpt2", help="Model name on the Hub")},
    pack="finetune",
    cacheable=False,  # holds live model objects; cheap to reload from HF's own disk cache
)
def load_model(ctx, model_name):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    ctx.log(f"Loading {model_name} (cached locally by Hugging Face after first download)")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name)
    return {"hf_model": AnyValue(value=(tokenizer, model))}


@node(
    id="ft.docs_from_dataset",
    name="Docs from Dataset",
    category="Fine-tuning",
    description="Turn one text column of a dataset into training documents.",
    inputs={"dataset": "dataset"},
    outputs={"docs": "docs"},
    params={"text_column": Str(required=True, help="Which column holds the text")},
    pack="finetune",
)
def docs_from_dataset(ctx, dataset, text_column):
    if text_column not in dataset.df.columns:
        raise ValueError(f"No column named '{text_column}'. Columns: {', '.join(map(str, dataset.df.columns))}")
    docs = [
        {"id": str(i), "text": str(t), "meta": {}}
        for i, t in enumerate(dataset.df[text_column].dropna())
    ]
    return {"docs": TextDocs(docs=docs)}


@node(
    id="ft.text_data",
    name="Tokenize Text",
    category="Fine-tuning",
    description="Prepare documents for training: tokenize and chunk.",
    inputs={"docs": "docs", "hf_model": "any"},
    outputs={"tokenized": "any"},
    params={"max_length": Int(default=128, min=8)},
    pack="finetune",
    cacheable=False,
)
def text_data(ctx, docs, hf_model, max_length):
    tokenizer, _ = hf_model.value
    texts = [d["text"] for d in docs.docs]
    encoded = tokenizer(
        texts, truncation=True, max_length=max_length, padding="max_length", return_tensors="pt"
    )
    ctx.log(f"Tokenized {len(texts)} documents (max_length={max_length})")
    return {"tokenized": AnyValue(value=encoded)}


@node(
    id="ft.lora_finetune",
    name="LoRA Fine-tune",
    category="Fine-tuning",
    description="Efficiently fine-tune with LoRA adapters — watch the loss live.",
    inputs={"hf_model": "any", "tokenized": "any"},
    outputs={"model": "model"},
    params={
        "r": Int(default=8, min=1, help="LoRA rank"),
        "alpha": Int(default=16, min=1),
        "epochs": Int(default=1, min=1),
        "lr": Float(default=0.0002, min=0.0),
        "batch_size": Int(default=4, min=1),
        "seed": Int(default=42),
    },
    pack="finetune",
    cacheable=False,
)
def lora_finetune(ctx, hf_model, tokenized, r, alpha, epochs, lr, batch_size, seed):
    import torch
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(seed)
    tokenizer, base_model = hf_model.value

    config = LoraConfig(r=r, lora_alpha=alpha, task_type="CAUSAL_LM")
    model = get_peft_model(base_model, config)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    ctx.log(f"LoRA attached — {trainable:,} trainable parameters")

    ids, mask = tokenized.value["input_ids"], tokenized.value["attention_mask"]
    loader = DataLoader(TensorDataset(ids, mask), batch_size=batch_size, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    model.train()
    total_steps = max(len(loader) * epochs, 1)
    step, last_loss = 0, None
    for epoch in range(epochs):
        if ctx.cancelled:
            break
        for input_ids, attention_mask in loader:
            if ctx.cancelled:
                break
            labels = input_ids.clone()
            labels[attention_mask == 0] = -100
            out = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            out.loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            step += 1
            last_loss = float(out.loss.item())
            ctx.progress(step / total_steps, {"step": step, "loss": round(last_loss, 4)})

    return {
        "model": Model(
            obj=(tokenizer, model),
            framework="hf",
            task="causal-lm",
            meta={"train_loss": last_loss, "steps": step, "lora_r": r},
        )
    }


@node(
    id="ft.generate",
    name="Generate Text",
    category="Fine-tuning",
    description="Generate text with a (fine-tuned) language model.",
    inputs={"model": "model"},
    outputs={"text": "text"},
    params={
        "prompt": Str(default="", help="Starting text"),
        "max_new_tokens": Int(default=50, min=1),
        "temperature": Float(default=0.8, min=0.0, max=2.0),
    },
    pack="finetune",
    cacheable=False,
)
def generate(ctx, model, prompt, max_new_tokens, temperature):
    import torch

    tokenizer, lm = model.obj
    lm.eval()
    inputs = tokenizer(prompt or tokenizer.bos_token or "", return_tensors="pt")
    with torch.no_grad():
        out = lm.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=max(temperature, 1e-5),
            pad_token_id=tokenizer.pad_token_id,
        )
    text = tokenizer.decode(out[0], skip_special_tokens=True)
    return {"text": TextValue(text=text)}


@node(
    id="ft.save_adapter",
    name="Save Adapter",
    category="Fine-tuning",
    description="Save the trained LoRA adapter (small file, shareable).",
    inputs={"model": "model"},
    outputs={},
    params={"name": Str(default="my-adapter", help="Folder name for the adapter")},
    pack="finetune",
    cacheable=False,
)
def save_adapter(ctx, model, name):
    _, lm = model.obj
    target = (ctx.workspace or __import__("pathlib").Path(".")) / "data" / "adapters" / name
    target.mkdir(parents=True, exist_ok=True)
    lm.save_pretrained(str(target))
    ctx.log(f"Adapter saved to {target}")
    return None
