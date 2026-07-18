# Example workflows

Open these from the in-app gallery (the Examples button), or run them headless:

```bash
uv run python -m axon run examples/house-prices.axon.json
```

| Example | Domain | Requirements |
|---|---|---|
| `house-prices` | Classical ML | none, runs offline |
| `digit-classifier` | Deep learning | `deep` pack (PyTorch) |
| `finetune-tiny-llm` | Fine-tuning | `finetune` pack |
| `chat-your-docs` | Retrieval | `rag` pack plus a free OpenRouter key |
| `research-agent` | Agents | a free OpenRouter key |

Each example is a single portable `.axon.json` file. Send one to a colleague and they can open it on their machine.
