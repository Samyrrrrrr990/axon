# Example workflows

Open these from the in-app gallery (Examples button), or run them headless:

```bash
uv run axon run examples/house-prices.axon.json
```

| Example | Domain | Needs |
|---|---|---|
| `house-prices` | Classical ML | nothing — runs offline |
| `digit-classifier` | Deep learning | `deep` pack (PyTorch) |
| `finetune-tiny-llm` | Fine-tuning | `finetune` pack |
| `chat-your-docs` | RAG | `rag` pack + a free OpenRouter key |
| `research-agent` | Agents | a free OpenRouter key |

Each example is a single portable `.axon.json` file — send one to a colleague
and they can open it on their machine.
